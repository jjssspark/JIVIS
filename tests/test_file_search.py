from pathlib import Path
import src.tools.file_search as file_search
from src.tools.file_search import search_files


def test_search_files_matches_substring_in_filename(tmp_path):
    (tmp_path / "study_plan.txt").write_text("x")
    (tmp_path / "report.pdf").write_text("x")

    result = search_files("study", base_dir=tmp_path)

    assert result == [str(tmp_path / "study_plan.txt")]


def test_search_files_matches_extension_keyword(tmp_path):
    (tmp_path / "a.pdf").write_text("x")
    (tmp_path / "b.txt").write_text("x")

    result = search_files("pdf", base_dir=tmp_path)

    assert result == [str(tmp_path / "a.pdf")]


def test_search_files_matches_korean_extension_alias(tmp_path):
    (tmp_path / "main.py").write_text("x")
    (tmp_path / "notes.txt").write_text("x")

    result = search_files("파이썬", base_dir=tmp_path)

    assert result == [str(tmp_path / "main.py")]


def test_search_files_is_case_insensitive(tmp_path):
    (tmp_path / "Report.PDF").write_text("x")

    result = search_files("report", base_dir=tmp_path)

    assert result == [str(tmp_path / "Report.PDF")]


def test_search_files_searches_subdirectories(tmp_path):
    sub = tmp_path / "2026"
    sub.mkdir()
    (sub / "study_plan.txt").write_text("x")

    result = search_files("study", base_dir=tmp_path)

    assert result == [str(sub / "study_plan.txt")]


def test_search_files_returns_empty_list_when_no_match(tmp_path):
    (tmp_path / "a.txt").write_text("x")

    assert search_files("xyz", base_dir=tmp_path) == []


def test_search_files_returns_empty_list_when_dir_missing(tmp_path):
    missing = tmp_path / "no_such_dir"

    assert search_files("anything", base_dir=missing) == []


def test_search_files_skips_hidden_directories(tmp_path):
    hidden = tmp_path / ".git"
    hidden.mkdir()
    (hidden / "study_plan.txt").write_text("x")
    visible = tmp_path / "normal"
    visible.mkdir()
    (visible / "study_plan.txt").write_text("x")

    result = search_files("study", base_dir=tmp_path)

    assert result == [str(visible / "study_plan.txt")]


def test_search_files_skips_known_heavy_directories(tmp_path):
    noisy = tmp_path / "node_modules"
    noisy.mkdir()
    (noisy / "study_plan.txt").write_text("x")
    visible = tmp_path / "normal"
    visible.mkdir()
    (visible / "study_plan.txt").write_text("x")

    result = search_files("study", base_dir=tmp_path)

    assert result == [str(visible / "study_plan.txt")]


def test_default_base_dir_is_home_directory():
    assert file_search.HOME_DIR == Path.home()
