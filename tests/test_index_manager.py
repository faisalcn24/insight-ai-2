import importlib
import json
from pathlib import Path


def test_remove_index_removes_registry_entry_and_index_dir(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("INSIGHT_STORAGE_DIR", str(tmp_path))
    index_manager = importlib.import_module("functions.index_manager")

    index_dir = index_manager.get_index_dir("demo")
    index_dir.mkdir(parents=True)
    registry_file = tmp_path / "registry.json"
    registry_file.write_text(json.dumps({"demo": {"documents": []}, "keep": {"documents": []}}), encoding="utf-8")

    assert index_manager.remove_index("demo") is True

    assert not index_dir.exists()
    assert json.loads(registry_file.read_text(encoding="utf-8")) == {"keep": {"documents": []}}
