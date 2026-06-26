import os
from pathlib import Path

from app.environment import load_project_env


def test_load_project_env_reads_dotenv_file(tmp_path: Path, monkeypatch) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("DOUYIN_COOKIE=test-cookie\nOPENAI_API_KEY=test-key\n", encoding="utf-8")

    monkeypatch.delenv("DOUYIN_COOKIE", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    load_project_env(tmp_path)

    assert os.getenv("DOUYIN_COOKIE") == "test-cookie"
    assert os.getenv("OPENAI_API_KEY") == "test-key"


def test_load_project_env_keeps_existing_value(tmp_path: Path, monkeypatch) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("DOUYIN_COOKIE=file-cookie\n", encoding="utf-8")
    monkeypatch.setenv("DOUYIN_COOKIE", "env-cookie")

    load_project_env(tmp_path)

    assert os.getenv("DOUYIN_COOKIE") == "env-cookie"
