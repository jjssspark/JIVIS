import pytest
from src.memory.database import init_db, save_memory, load_memory, load_all_memory


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_save_and_load():
    save_memory("_test_key", "hello")
    assert load_memory("_test_key") == "hello"


def test_overwrite_same_key():
    save_memory("_test_goal", "백엔드 개발자")
    save_memory("_test_goal", "프론트엔드 개발자")
    assert load_memory("_test_goal") == "프론트엔드 개발자"


def test_load_nonexistent_returns_none():
    assert load_memory("_test_nonexistent_xyz_999") is None


def test_load_all_memory_contains_saved_key():
    save_memory("_test_hobby", "독서")
    all_mem = load_all_memory()
    assert "_test_hobby" in all_mem
    assert all_mem["_test_hobby"] == "독서"


def test_multiple_keys_independent():
    save_memory("_test_a", "value_a")
    save_memory("_test_b", "value_b")
    assert load_memory("_test_a") == "value_a"
    assert load_memory("_test_b") == "value_b"
