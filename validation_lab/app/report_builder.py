"""Render self contained HTML and matching Word reports from stored validation evidence."""
import base64
from datetime import datetime, timezone
from io import BytesIO
import json
from pathlib import Path
from typing import Any
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from jinja2 import Environment, FileSystemLoader, select_autoescape
from markdown_it import MarkdownIt
from markupsafe import Markup
from app.config import LabError, output_directory, relative, safe_path, write_json
from app.data_loader import file_hash
from app.schemas import ReportRequest, ValidationResult

DISCLOSURE = ("Numbers, tables and charts were computed by deterministic code. Narrative text was drafted by "
              "the validator agent of ModelPassport and reviewed by a human.")
MARKDOWN = MarkdownIt("commonmark", {"html": False}).disable("image")


def label(value: str) -> str:
    """Turn a machine field name into a readable heading."""
    return value if "/" in value else value.replace("_", " ").title()


def display(value: Any) -> str:
    """Show null measurements honestly and format scalar values consistently."""
    if value is None:
        return "Not available"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=True)
    return str(value)


def sections(request: ReportRequest, result: dict, hashes: dict) -> list[dict]:
    """Assemble the fourteen ordered report sections shared by both formats."""
    s, n = result["sections"], request.narrative
    return [
        {"title": "Executive summary", "markdown": n.executive_summary},
        {"title": "Model overview", "data": request.inventory_record},
        {"title": "Scope and approach", "text": "Independent deterministic tests on supplied observations and scores. The holdout is a random holdout and not a true out of time sample. OOT in field names means holdout.",
         "data": {"sample_sizes": result["sample_sizes"], "tests_run": [k for k, v in s.items() if v is not None]}},
        {"title": "Data quality", "data": s["data_quality"]},
        {"title": "Conceptual soundness", "markdown": n.conceptual_soundness},
        {"title": "Implementation verification", "data": request.parity_summary,
         "text": "No redevelopment parity summary supplied." if request.parity_summary is None else "Parity evidence supplied by factory_core; not recomputed by validation_lab."},
        {"title": "Outcome analysis", "data": {k: s[k] for k in ("discrimination", "calibration", "backtest")},
         "chart_ids": ["roc_oot", "calibration_oot"]},
        {"title": "Stability", "data": s["stability"], "chart_ids": ["score_distribution", "psi_features"]},
        {"title": "Fairness", "data": s["fairness"], "chart_ids": [c["id"] for c in result["charts"] if c["id"].startswith("fairness_")]},
        {"title": "Sensitivity and benchmark", "data": {k: s[k] for k in ("sensitivity", "benchmark")}},
        {"title": "Findings and recommendations", "markdown": n.findings_commentary,
         "data": {"findings_table": [{k: f[k] for k in ("id", "section", "severity", "title", "recommendation")} for f in result["findings"]],
                  "supporting_evidence": [{k: f[k] for k in ("id", "detail", "evidence")} for f in result["findings"]]}},
        {"title": "Conclusion and sign off", "markdown": n.conclusion,
         "text": f"Human validator: {request.sign_off.human_validator}; signed at {request.sign_off.signed_at}. Supplied sign off; governance approval is managed by factory_core."
                 if request.sign_off.human_validator and request.sign_off.signed_at else "Pending human sign off",
         "data": {"validator_agent_model": request.sign_off.validator_agent_model}},
        {"title": "Appendix", "text": "Thresholds are illustrative defaults, not regulatory limits. " + DISCLOSURE,
         "data": {"thresholds_used": [{"metric": k, "value": v} for k, v in result["thresholds_used"].items()],
                  "data_file_hashes": [{"path": k, "sha256": v} for k, v in hashes.items()],
                  "review_status": "Pending human review" if not (request.sign_off.human_validator and request.sign_off.signed_at) else "Sign off supplied by factory_core"}},
    ]


def table(document, rows: list[dict]) -> None:
    """Write comparable rows with repeating headers and readable bounded widths."""
    if not rows:
        document.add_paragraph("No entries.")
        return
    keys = list(dict.fromkeys(k for row in rows for k in row))
    # Split wide tables with their identifying column repeated in each part.
    groups = [keys] if len(keys) <= 5 else [[keys[0]] + keys[i:i+4] for i in range(1, len(keys), 4)]
    for columns in groups:
        grid = document.add_table(rows=1, cols=len(columns))
        grid.style = "Table Grid"
        grid.autofit = False
        borders = OxmlElement("w:tblBorders")
        for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
            line = OxmlElement("w:" + edge)
            for key, item in (("val", "single"), ("sz", "4"), ("color", "D9D9D9")):
                line.set(qn("w:" + key), item)
            borders.append(line)
        grid._tbl.tblPr.append(borders)
        for cell, key in zip(grid.rows[0].cells, columns):
            cell.text = label(key)
            shade = OxmlElement("w:shd")
            shade.set(qn("w:fill"), "DCE6F1")
            cell._tc.get_or_add_tcPr().append(shade)
        repeat = OxmlElement("w:tblHeader")
        grid.rows[0]._tr.get_or_add_trPr().append(repeat)
        for row in rows:
            for cell, key in zip(grid.add_row().cells, columns):
                cell.text = display(row.get(key))
        for row in grid.rows:
            row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
            for cell in row.cells:
                cell.width = Inches(6.5 / len(columns))
                for paragraph in cell.paragraphs:
                    paragraph.paragraph_format.space_after = Pt(5)
                    for run in paragraph.runs:
                        run.font.size = Pt(9)
        document.add_paragraph()


def word_value(document, value: Any, depth: int = 2) -> None:
    """Render nested evidence as prose, labelled subsections and comparable tables."""
    if isinstance(value, dict):
        scalars = {k: v for k, v in value.items() if not isinstance(v, (dict, list))}
        if len(scalars) > 10:
            table(document, [{"metric": k, "value": v} for k, v in scalars.items()])
        elif scalars:
            for key, item in scalars.items():
                document.add_paragraph(f"{label(key)}: {display(item)}")
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                document.add_heading(label(key), level=min(depth, 4))
                word_value(document, item, depth + 1)
    elif isinstance(value, list):
        if value and all(isinstance(row, dict) for row in value):
            if any(isinstance(v, (dict, list)) for row in value for v in row.values()):
                for i, row in enumerate(value, 1):
                    document.add_heading(str(row.get("attribute", row.get("id", f"Entry {i}"))), level=min(depth, 4))
                    word_value(document, row, depth + 1)
            else:
                table(document, value)
        else:
            document.add_paragraph(", ".join(display(v) for v in value) or "No entries.")
    else:
        document.add_paragraph(display(value))


def word_report(path: Path, title: str, subtitle: str, blocks: list[dict], images: dict, warning: list) -> None:
    """Write a portrait report with identical evidence, narrative and embedded charts."""
    document = Document()
    section = document.sections[0]
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    section.top_margin = section.bottom_margin = Inches(.7)
    section.left_margin = section.right_margin = Inches(1)
    normal = document.styles["Normal"]
    normal.font.name, normal.font.size = "Calibri", Pt(11)
    for name in ("Title", "Heading 1", "Heading 2", "Heading 3", "Heading 4"):
        document.styles[name].font.color.rgb = RGBColor(0, 0, 0)
        properties = document.styles[name].element.find(qn("w:pPr"))
        if properties is not None:
            for border in list(properties.findall(qn("w:pBdr"))):
                properties.remove(border)
    document.core_properties.author = "ModelPassport team"
    document.add_paragraph(title, "Title")
    document.add_paragraph(subtitle)
    document.add_paragraph("Draft validation evidence for independent expert review.")
    if warning:
        document.add_paragraph("Warning: unverified numbers in supplied narrative: " + display(warning))
    for block in blocks:
        document.add_heading(block["title"], level=1)
        if block.get("markdown"):
            for token in MARKDOWN.parse(block["markdown"]):
                if token.type == "inline":
                    document.add_paragraph(token.content)
        if block.get("text"):
            document.add_paragraph(block["text"])
        if "data" in block:
            word_value(document, block["data"])
        for identifier in block.get("chart_ids", []):
            picture = images[identifier]
            caption = document.add_paragraph(picture["title"])
            caption.paragraph_format.keep_with_next = True
            document.add_picture(BytesIO(picture["bytes"]), width=Inches(6.3))
    document.save(path)


def build(request: ReportRequest) -> dict:
    """Validate stored identity, verify input provenance and render requested formats."""
    result_path = safe_path(request.validation_result_path)
    try:
        result = ValidationResult.model_validate_json(result_path.read_text(encoding="utf-8")).model_dump()
    except ValueError as exc:
        raise LabError("INVALID_RESULT", "Stored file is not a ValidationResult.") from exc
    if result["model_id"] != request.model_id or result["run_id"] != request.run_id:
        raise LabError("RESULT_MISMATCH", "Stored result does not belong to the requested model and run.", 409)
    if request.inventory_record.get("model_id") != request.model_id:
        raise LabError("INVENTORY_MISMATCH", "Inventory record belongs to a different model.")
    evidence_path = result_path.parent / "input_evidence.json"
    hashes = {}
    if evidence_path.exists():
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        if evidence.get("run_id") != request.run_id or evidence.get("model_id") != request.model_id:
            raise LabError("EVIDENCE_MISMATCH", "Input evidence belongs to a different validation run.", 409)
        hashes = evidence["data_hashes"]
        if any(file_hash(p) != h for p, h in hashes.items()):
            raise LabError("INPUT_CHANGED", "An input file changed after validation; rerun validation before reporting.", 409)
    if not hashes:
        hashes = {"status": "Input hash evidence unavailable for this stored result"}
    images = {}
    for chart in result["charts"]:
        content = safe_path(chart["path"]).read_bytes()
        if not content.startswith(b"\x89PNG\r\n\x1a\n"):
            raise LabError("INVALID_CHART", "Chart must be a PNG file.")
        images[chart["id"]] = {"bytes": content, "title": chart["title"],
                                "uri": "data:image/png;base64," + base64.b64encode(content).decode("ascii")}
    blocks = sections(request, result, hashes)
    for block in blocks:
        if "markdown" in block:
            block["html"] = Markup(MARKDOWN.render(block["markdown"]))
    today = datetime.now(timezone.utc).date().isoformat()
    name = request.inventory_record.get("model_name", request.model_id)
    tier = request.inventory_record.get("tiering", {}).get("tier", "Not supplied")
    title = f"{name} validation report"
    subtitle = f"{request.model_id} | {tier} | {today} UTC | Overall rating {result['overall_rating']}"
    directory = output_directory(request.model_id, "validation")
    response = {"model_id": request.model_id, "html_path": None, "docx_path": None, "error": None}
    if "html" in request.formats:
        env = Environment(loader=FileSystemLoader(Path(__file__).parent / "templates"), autoescape=select_autoescape(["html"]))
        page = env.get_template("validation_report.html").render(title=title, subtitle=subtitle, blocks=blocks,
                   images=images, warnings=request.narrative.unverified_numbers, display=display, label=label)
        path = directory / "validation_report.html"
        path.write_text(page, encoding="utf-8")
        response["html_path"] = relative(path)
    if "docx" in request.formats:
        path = directory / "validation_report.docx"
        word_report(path, title, subtitle, blocks, images, request.narrative.unverified_numbers)
        response["docx_path"] = relative(path)
    write_json(directory / "report_result.json", response)
    return response
