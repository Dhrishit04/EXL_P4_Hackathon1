"""Typed wire contracts for the validation service in project context section 9.2."""
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

Rating = Literal["GREEN", "AMBER", "RED"]
Number = float | None
Identifier = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,99}$")]


class Contract(BaseModel):
    """Reject accidental contract changes and nonfinite numeric values."""
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class DataPaths(Contract):
    """Locate development and holdout observations."""
    dev_path: str
    oot_path: str
    id_col: str
    target_col: str


class ScorePaths(Contract):
    """Locate model scores and identify score columns."""
    dev_path: str
    oot_path: str
    pd_col: str
    score_col: str
    decision_col: str


class ValidateRequest(Contract):
    """Request independent validation on aligned observations and scores."""
    run_id: Identifier
    model_id: Identifier
    model_type: Literal["credit_pd", "fraud", "pricing", "other"]
    data: DataPaths
    scores: ScorePaths
    feature_cols: list[str]
    protected_cols: list[str]
    model_module_path: str | None = None
    thresholds: dict[str, float] | None = None

    @model_validator(mode="after")
    def independent_features(self) -> "ValidateRequest":
        """Keep protected attributes and outcome information out of challenger inputs."""
        excluded = set(self.protected_cols + [self.data.target_col, self.data.id_col,
                         self.scores.pd_col, self.scores.score_col, self.scores.decision_col])
        if excluded.intersection(self.feature_cols) or len(set(self.feature_cols)) != len(self.feature_cols):
            raise ValueError("feature_cols must be unique and exclude protected, id, target and score columns")
        return self


class Check(Contract):
    """Record a measured quality check."""
    check: str
    value: Number
    threshold: float
    passed: bool


class DataQuality(Contract):
    """Summarize quality checks and sample target rates."""
    rating: Rating
    checks: list[Check]
    target_rate: dict[str, Number]


class DiscriminationMetrics(Contract):
    """Measure rank ordering of good and bad outcomes."""
    auc: Number
    gini: Number
    ks: Number


class Discrimination(Contract):
    """Compare development and holdout discrimination."""
    rating: Rating
    dev: DiscriminationMetrics
    oot: DiscriminationMetrics
    gini_relative_drop: Number


class CalibrationMetrics(Contract):
    """Measure probability accuracy and calibration."""
    brier: Number
    mean_predicted_pd: Number
    observed_default_rate: Number
    observed_over_expected: Number
    hosmer_lemeshow_stat: Number
    hosmer_lemeshow_p: Number


class Decile(Contract):
    """Describe an equal sized holdout probability group."""
    decile: int
    n: int
    mean_pd: Number
    observed_rate: Number


class Calibration(Contract):
    """Hold holdout calibration and decile evidence."""
    rating: Rating
    oot: CalibrationMetrics
    decile_table: list[Decile]


class FeatureStability(Contract):
    """Measure population change in one feature."""
    feature: str
    csi: Number
    rating: Rating


class Stability(Contract):
    """Measure probability and feature distribution drift."""
    rating: Rating
    psi_score: Number
    csi: list[FeatureStability]


class Band(Contract):
    """Compare predicted and observed risk in a development defined band."""
    band: str
    pd_min: Number
    pd_max: Number
    n: int
    mean_pd: Number
    observed_rate: Number
    binomial_p: Number
    light: Rating


class Backtest(Contract):
    """Collect risk band calibration tests."""
    rating: Rating
    bands: list[Band]


class FairnessGroup(Contract):
    """Record outcome statistics for a protected group."""
    group: str
    n: int
    approval_rate: Number
    approval_rate_good_customers: Number
    approval_rate_bad_customers: Number
    observed_default_rate: Number
    mean_pd: Number


class FairnessAttribute(Contract):
    """Compare eligible groups within one attribute."""
    attribute: str
    groups: list[FairnessGroup]
    demographic_parity_ratio: Number
    equal_opportunity_diff: Number
    equalized_odds_diff: Number
    rating: Rating


class Fairness(Contract):
    """Collect fairness evidence with approval as the favourable outcome."""
    rating: Rating
    favourable_outcome: Literal["APPROVE"]
    by_attribute: list[FairnessAttribute]


class Shock(Contract):
    """Measure a feature perturbation against original model outputs."""
    feature: str
    shock: str
    mean_pd_change: Number
    decision_flip_rate: Number


class Sensitivity(Contract):
    """Collect numeric feature shock results."""
    rating: Rating
    shocks: list[Shock]


class Benchmark(Contract):
    """Compare champion with a reproducible gradient boosting challenger."""
    rating: Rating
    challenger: Literal["gradient_boosting"]
    champion_auc_oot: Number
    challenger_auc_oot: Number
    auc_uplift: Number


class Sections(Contract):
    """Collect every validation section with optional challenge tests."""
    data_quality: DataQuality
    discrimination: Discrimination
    calibration: Calibration
    stability: Stability
    backtest: Backtest
    fairness: Fairness
    sensitivity: Sensitivity | None
    benchmark: Benchmark | None


class Evidence(Contract):
    """Tie a finding to a measured value and stated threshold."""
    metric: str
    value: Number
    threshold: str


class Finding(Contract):
    """Record a stable rated finding and actionable recommendation."""
    id: str
    section: str
    severity: Literal["HIGH", "MEDIUM", "LOW"]
    title: str
    detail: str
    evidence: Evidence
    recommendation: str


class Chart(Contract):
    """Locate one chart and name the matching dashboard series."""
    id: str
    title: str
    path: str


class ValidationResult(Contract):
    """Return computed evidence without changing the frozen result shape."""
    model_id: str
    run_id: str
    status: Literal["COMPLETED"]
    overall_rating: Rating
    sample_sizes: dict[str, int]
    sections: Sections
    findings: list[Finding]
    charts: list[Chart]
    series: dict[str, list[dict[str, Any]]]
    thresholds_used: dict[str, float]
    result_path: str
    duration_seconds: float
    error: dict | None


class Narrative(Contract):
    """Receive report prose from factory_core without computing it locally."""
    executive_summary: str
    conceptual_soundness: str
    findings_commentary: str
    conclusion: str
    unverified_numbers: list[Any]


class SignOff(Contract):
    """Display supplied sign off information without approving any gate."""
    validator_agent_model: str
    human_validator: str | None
    signed_at: str | None


class ReportRequest(Contract):
    """Render stored validation evidence and supplied inventory and narrative."""
    run_id: Identifier
    model_id: Identifier
    validation_result_path: str
    inventory_record: dict[str, Any]
    parity_summary: dict[str, Any] | None
    narrative: Narrative
    sign_off: SignOff
    formats: list[Literal["html", "docx"]] = Field(min_length=1)


class ReportResult(Contract):
    """Locate the requested report formats."""
    model_id: str
    html_path: str | None
    docx_path: str | None
    error: dict | None


class MonitorSimulateRequest(Contract):
    """Configure seeded simulated monthly production batches."""
    model_id: Identifier
    data_path: str
    scores_path: str
    id_col: str
    target_col: str
    pd_col: str
    score_col: str
    feature_cols: list[str]
    n_batches: int = Field(ge=1, le=120)
    batch_size: int = Field(ge=1, le=100000)
    drift_start_batch: int = Field(ge=1)
    drift_strength: float = Field(ge=0, le=100)
    seed: int


class SimulatedBatch(Contract):
    """Locate an explicitly simulated batch."""
    batch: str
    path: str
    n: int
    drift_injected: bool


class MonitorSimulateResult(Contract):
    """Return simulated batch locations."""
    model_id: str
    simulated: bool
    batches_dir: str
    batches: list[SimulatedBatch]
    error: dict | None


class Reference(Contract):
    """Locate the development reference data and scores."""
    data_path: str
    scores_path: str


class MonitorRunRequest(Contract):
    """Request drift and performance tests on stored production batches."""
    model_id: Identifier
    reference: Reference
    batches_dir: str
    id_col: str
    target_col: str
    pd_col: str
    score_col: str
    feature_cols: list[str]
    thresholds: dict[str, float] | None = None


class MaximumCSI(Contract):
    """Identify the most shifted feature."""
    feature: str | None
    csi: Number


class MonitoringBatch(Contract):
    """Measure drift and predictive performance in one batch."""
    batch: str
    n: int
    psi_score: Number
    max_csi: MaximumCSI
    auc: Number
    observed_default_rate: Number
    mean_pd: Number
    alert: Rating


class Alert(Contract):
    """Explain a triggered monitoring rule."""
    batch: str
    level: Rating
    rule: str
    value: Number


class MonitoringResult(Contract):
    """Return batch evidence and an explicit revalidation decision."""
    model_id: str
    status: Literal["COMPLETED"]
    simulated: bool
    reference_sample: Literal["dev"]
    batches: list[MonitoringBatch]
    alerts: list[Alert]
    revalidation_triggered: bool
    trigger_reason: str | None
    thresholds_used: dict[str, float]
    result_path: str
    error: dict | None
