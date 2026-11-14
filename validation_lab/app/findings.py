"""Apply transparent per test rating rules and stable evidence identifiers."""
import hashlib
from app.thresholds import higher, lower

RANK = {"GREEN": 0, "AMBER": 1, "RED": 2}


def worst(ratings) -> str:
    """Return the worst applicable traffic light."""
    return max(ratings, key=RANK.get, default="GREEN")


def finding(section: str, metric: str, value, rating: str, threshold: str,
            detail: str | None = None) -> dict:
    """Construct a deterministic finding identifier and evidence record."""
    identity = hashlib.sha256(f"{section}:{metric}".encode()).hexdigest()[:10].upper()
    return {"id": "F_" + identity, "section": section,
            "severity": {"RED": "HIGH", "AMBER": "MEDIUM", "GREEN": "LOW"}[rating],
            "title": f"{section.replace('_', ' ').title()}: {metric}",
            "detail": detail or f"The measured {metric} is outside the green illustrative limit.",
            "evidence": {"metric": metric, "value": value, "threshold": threshold},
            "recommendation": {
                "calibration": "Review calibration by risk band and consider intercept recalibration on recent data.",
                "fairness": "Review group outcomes and sample support with an independent conduct risk reviewer.",
                "stability": "Investigate population changes and assess the need for revalidation.",
                "discrimination": "Investigate rank performance and model suitability on representative data.",
                "data_quality": "Review the affected input columns and correct or document quality limitations.",
                "backtest": "Review predicted against observed risk in the affected band.",
                "benchmark": "Review the challenger's uplift using independent temporal validation.",
            }.get(section, "Review the unavailable test or sensitivity evidence before human approval.")}


def rate(sections: dict, thresholds: dict, notes: list[tuple[str, str]]) -> tuple[list[dict], str]:
    """Rate every measured test and expose unavailable metrics as low findings."""
    results = []
    ratings = {name: [] for name in sections}

    def record(section: str, metric: str, value, light: str, threshold: str, detail: str | None = None) -> None:
        """Record one test outcome without hiding undefined measurements."""
        ratings[section].append(light)
        if value is None:
            results.append(finding(section, metric, None, "GREEN", threshold,
                           detail or "This test could not run because sample support or a denominator is insufficient."))
        elif light != "GREEN" or detail:
            results.append(finding(section, metric, value, light, threshold, detail))

    for check in sections["data_quality"]["checks"]:
        light = "GREEN" if check["passed"] else "AMBER"
        record("data_quality", check["check"], check["value"], light, f"At most {check['threshold']}")
    d = sections["discrimination"]
    for sample in ("dev", "oot"):
        for metric in ("auc", "ks"):
            g, a = thresholds[metric + "_green"], thresholds[metric + "_amber"]
            record("discrimination", f"{sample}.{metric}", d[sample][metric], higher(d[sample][metric], g, a), f"Green >= {g}; amber >= {a}")
    record("discrimination", "gini_relative_drop", d["gini_relative_drop"],
           lower(d["gini_relative_drop"], thresholds["gini_drop_green"], thresholds["gini_drop_amber"]),
           f"Green <= {thresholds['gini_drop_green']}; amber <= {thresholds['gini_drop_amber']}")
    calibration = sections["calibration"]["oot"]
    oe = calibration["observed_over_expected"]
    record("calibration", "observed_over_expected", oe,
           lower(abs(oe - 1) if oe is not None else None, thresholds["oe_band_green"], thresholds["oe_band_amber"]),
           f"Distance from 1 <= {thresholds['oe_band_green']}; amber <= {thresholds['oe_band_amber']}")
    hl = calibration["hosmer_lemeshow_p"]
    record("calibration", "hosmer_lemeshow_p", hl, "AMBER" if hl is not None and hl < thresholds["hl_p_green"] else "GREEN",
           f"Green >= {thresholds['hl_p_green']}; rejection is amber at most")
    stable = sections["stability"]
    for metric, value in [("psi_score", stable["psi_score"])] + [(f"csi.{x['feature']}", x["csi"]) for x in stable["csi"]]:
        light = lower(value, thresholds["psi_green"], thresholds["psi_amber"], strict_green=True)
        record("stability", metric, value, light, f"Green < {thresholds['psi_green']}; amber <= {thresholds['psi_amber']}")
        for row in stable["csi"]:
            if metric == f"csi.{row['feature']}":
                row["rating"] = light
    for band in sections["backtest"]["bands"]:
        record("backtest", f"band.{band['band']}.binomial_p", band["binomial_p"], band["light"], "Green >= 0.05; amber >= 0.01")
    for attr in sections["fairness"]["by_attribute"]:
        lights = []
        for metric, prefix, direction in (("demographic_parity_ratio", "dp_ratio", higher),
                                          ("equal_opportunity_diff", "eo_diff", lower),
                                          ("equalized_odds_diff", "eo_diff", lower)):
            value = attr[metric]
            light = direction(value, thresholds[prefix + "_green"], thresholds[prefix + "_amber"])
            lights.append(light)
            record("fairness", f"{attr['attribute']}.{metric}", value, light,
                   f"Illustrative green {thresholds[prefix + '_green']}; amber {thresholds[prefix + '_amber']}")
        attr["rating"] = worst(lights)
        for group in attr["groups"]:
            if group["n"] < 50:
                record("fairness", f"{attr['attribute']}.{group['group']}.sample_size", group["n"], "GREEN", "At least 50 records",
                       "Group is reported but excluded from fairness comparisons because it has fewer than 50 records.")
            for field in ("approval_rate_good_customers", "approval_rate_bad_customers"):
                if group[field] is None:
                    record("fairness", f"{attr['attribute']}.{group['group']}.{field}", None, "GREEN", "Both outcome classes required")
    benchmark = sections.get("benchmark")
    if benchmark:
        value = benchmark["auc_uplift"]
        record("benchmark", "auc_uplift", value, "AMBER" if value > thresholds["benchmark_uplift_amber"] else "GREEN",
               f"Amber > {thresholds['benchmark_uplift_amber']}")
    for section, message in notes:
        results.append(finding(section, "unavailable", None, "GREEN", "Test must be applicable", message))
    for name, section in sections.items():
        if section is not None:
            section["rating"] = worst(ratings[name])
    overall = "RED" if any(f["severity"] == "HIGH" for f in results) else "AMBER" if any(f["severity"] == "MEDIUM" for f in results) else "GREEN"
    return results, overall
