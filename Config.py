import os
from pathlib import Path


def _load_env_file() -> None:
	env_path = Path(__file__).resolve().parent / ".env"
	if not env_path.exists():
		return

	for raw_line in env_path.read_text(encoding="utf-8").splitlines():
		line = raw_line.strip()
		if not line or line.startswith("#") or "=" not in line:
			continue

		key, value = line.split("=", 1)
		key = key.strip()
		value = value.strip().strip('"').strip("'")

		if key and key not in os.environ:
			os.environ[key] = value


def _load_streamlit_secrets() -> None:
	try:
		import streamlit as st
	except Exception:
		return

	for key in ("API_KEY", "BASE_URL", "MODEL_NAME"):
		if key in os.environ:
			continue

		try:
			value = st.secrets.get(key)
		except Exception:
			value = None

		if value:
			os.environ[key] = str(value)


_load_env_file()
_load_streamlit_secrets()

API_KEY = os.getenv("API_KEY", "")
BASE_URL = os.getenv("BASE_URL", "https://api.groq.com/openai/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "llama-3.3-70b-versatile")