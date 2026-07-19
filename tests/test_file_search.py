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


def test_search_files_ignores_generic_document_words_when_scoring(tmp_path):
    # "강의자료"는 흔한 단어라 무관한 파일까지 끌어오면 안 됨 — 실제 내용어(이산수학)만으로 매칭
    correct = tmp_path / "이산수학_1주차.pdf"
    correct.write_text("x")
    wrong = tmp_path / "컴퓨터공학특론_강의자료.pdf"
    wrong.write_text("x")

    result = search_files("이산수학 강의자료 같은거", base_dir=tmp_path)

    assert result == [str(correct)]


def test_search_files_ranks_more_specific_token_matches_first(tmp_path):
    two_tokens = tmp_path / "이산수학_기말고사.pdf"
    two_tokens.write_text("x")
    one_token = tmp_path / "이산수학_사진.png"
    one_token.write_text("x")

    result = search_files("이산수학 기말고사", base_dir=tmp_path)

    assert result[0] == str(two_tokens)  # 토큰 2개 다 매칭 → 1순위
    assert str(one_token) in result


def test_search_files_ignores_filler_only_query(tmp_path):
    (tmp_path / "a.txt").write_text("x")

    assert search_files("같은거", base_dir=tmp_path) == []
    assert search_files("강의자료 같은거", base_dir=tmp_path) == []


def test_search_files_matches_folders_not_just_files(tmp_path):
    image_folder = tmp_path / "image"
    image_folder.mkdir()
    (image_folder / "photo.png").write_text("x")

    result = search_files("image", base_dir=tmp_path)

    assert str(image_folder) in result


def test_search_files_matches_name_glued_with_korean_particles(tmp_path):
    # "image라는폴더가"처럼 한국어 조사가 영단어에 그대로 붙어도(공백 없이) 찾아야 함
    image_folder = tmp_path / "image"
    image_folder.mkdir()

    result = search_files("그냥 폴더 이름중에 image라는폴더가 있어 그거", base_dir=tmp_path)

    assert str(image_folder) in result
