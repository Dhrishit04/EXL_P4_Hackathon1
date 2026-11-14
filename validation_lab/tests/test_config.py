"""Test repository detection, safe path handling and response precision."""
from pathlib import Path
import pytest
from app.config import LabError, repository_root, response_numbers, safe_path


@pytest.mark.parametrize("path", ["../outside.csv", "C:/secret.csv", "/tmp/secret", "a\\b", "//host/share", "model_estate/_answer_keys/M001.json"])
def test_reject_unsafe_paths(repository, path):
    """Reject absolute, traversal, Windows drive and restricted paths."""
    with pytest.raises(LabError, match="Path"):
        safe_path(path)


def test_root_and_relative_path(repository):
    """Resolve paths independently from the process working directory."""
    assert repository_root() == repository
    assert safe_path("validation_lab/sample_data/dev.csv").is_file()
    assert response_numbers({"v": 1 / 3, "missing": float("nan")}) == {"v": .333333, "missing": None}


def test_automatic_root(monkeypatch, tmp_path):
    """Detect a real skeleton and require configuration in an isolated standalone root."""
    import app.config as config
    monkeypatch.delenv("REPO_ROOT", raising=False)
    service = tmp_path / "validation_lab" / "app"
    service.mkdir(parents=True)
    monkeypatch.setattr(config, "__file__", str(service / "config.py"))
    with pytest.raises(LabError) as error:
        repository_root()
    assert error.value.code == "CONFIG_ERROR"
    (tmp_path / "contracts").mkdir()
    assert repository_root() == tmp_path


def test_symlink_escape(repository, tmp_path):
    """Reject resolved links leaving the repository where the OS supports links."""
    outside = tmp_path.parent / (tmp_path.name + "_outside.csv")
    outside.write_text("secret")
    link = repository / "link.csv"
    try:
        link.symlink_to(outside)
    except OSError:
        pytest.skip("Creating symlinks requires Windows developer mode or link privileges")
    with pytest.raises(LabError):
        safe_path("link.csv")
