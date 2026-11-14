"""Reject protected feature leakage and invalid wire contract changes."""
import pytest
from pydantic import ValidationError
from app.schemas import ValidateRequest


@pytest.mark.parametrize("feature", ["SEX", "AGE_BAND", "default_flag", "pd", "ID"])
def test_feature_exclusions(requests, feature):
    """Protected attributes, outcomes and outputs cannot become model inputs."""
    value = requests["validate"]
    value["feature_cols"].append(feature)
    with pytest.raises(ValidationError):
        ValidateRequest.model_validate(value)


def test_unknown_required_fields_and_traversal_identifiers(requests):
    """Reject extra wire fields and model identifiers that could create unsafe paths."""
    value = requests["validate"]
    value["unknown"] = True
    with pytest.raises(ValidationError):
        ValidateRequest.model_validate(value)
    value.pop("unknown")
    value["model_id"] = "../escape"
    with pytest.raises(ValidationError):
        ValidateRequest.model_validate(value)
