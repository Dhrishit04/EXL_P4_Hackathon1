"""Test strict ID joins and validation of model outputs."""
import pandas as pd
import pytest
from app.config import LabError
from app.data_loader import load_scored


def inputs(repository, ids=("001", "002"), score_ids=("002", "001")):
    """Write minimal aligned inputs with meaningful leading zero identifiers."""
    pd.DataFrame({"ID": ids, "target": [0, 1]}).to_csv(repository / "data.csv", index=False)
    pd.DataFrame({"ID": score_ids, "pd": [.8, .1], "score": [10, 20], "decision": ["DECLINE", "APPROVE"]}).to_csv(repository / "scores.csv", index=False)


def test_join_on_id_not_position(repository):
    """Align shuffled scores by string ID and preserve all input observations."""
    inputs(repository)
    data = load_scored("data.csv", "scores.csv", "ID", "target")
    assert list(data.ID) == ["001", "002"]
    assert list(data.pd) == [.1, .8]


@pytest.mark.parametrize("ids,score_ids,code", [(("001", "002"), ("001", "003"), "ID_MISMATCH"),
    (("001", "001"), ("001", "002"), "INVALID_ID"), (("001", "002"), ("001", "001"), "INVALID_ID")])
def test_invalid_ids(repository, ids, score_ids, code):
    """Reject missing counterpart IDs and duplicates on either side."""
    inputs(repository, ids, score_ids)
    with pytest.raises(LabError) as error:
        load_scored("data.csv", "scores.csv", "ID", "target")
    assert error.value.code == code


@pytest.mark.parametrize("column,value,code", [("pd", 1.1, "INVALID_PD"), ("pd", None, "INVALID_PD"),
    ("score", 1.5, "INVALID_SCORE"), ("decision", "YES", "INVALID_DECISION")])
def test_invalid_scores(repository, column, value, code):
    """Reject impossible probabilities, noninteger scores and unknown decisions."""
    inputs(repository)
    scores = pd.read_csv(repository / "scores.csv", dtype={"ID": str})
    if column == "score":
        scores[column] = scores[column].astype(float)
    scores.loc[0, column] = value
    scores.to_csv(repository / "scores.csv", index=False)
    with pytest.raises(LabError) as error:
        load_scored("data.csv", "scores.csv", "ID", "target")
    assert error.value.code == code
