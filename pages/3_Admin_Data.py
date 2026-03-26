"""Local admin page for running pipeline steps and viewing summaries."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import streamlit as st

# Setup paths
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
	sys.path.insert(0, str(ROOT_DIR))

LOGS_DIR = ROOT_DIR / "logs"
WORKLOG_PATH = ROOT_DIR / "WORKLOG.md"


def _read_lines(path: Path) -> list[str]:
	if not path.exists():
		return []
	return path.read_text(encoding="utf-8").splitlines()


def _latest_worklog_entry(keyword: str) -> str | None:
	lines = _read_lines(WORKLOG_PATH)
	for line in reversed(lines):
		if keyword in line:
			return line
	return None


def _load_scrape_summary() -> dict | None:
	path = LOGS_DIR / "scrape_summary.json"
	if not path.exists():
		return None
	try:
		return json.loads(path.read_text(encoding="utf-8"))
	except json.JSONDecodeError:
		return None


def _stream_process(command: list[str], cwd: Path) -> int:
	output_box = st.empty()
	log_lines: list[str] = []

	process = subprocess.Popen(
		command,
		cwd=str(cwd),
		stdout=subprocess.PIPE,
		stderr=subprocess.STDOUT,
		text=True,
		bufsize=1,
	)

	assert process.stdout is not None
	for line in iter(process.stdout.readline, ""):
		clean = line.rstrip("\n")
		log_lines.append(clean)
		# Keep the last 400 lines to avoid huge UI payloads
		log_lines = log_lines[-400:]
		output_box.code("\n".join(log_lines), language="text")

	process.stdout.close()
	return process.wait()


def _run_script(label: str, script_path: Path) -> None:
	st.write(f"Running {label}...")
	command = [sys.executable, str(script_path)]
	exit_code = _stream_process(command, ROOT_DIR)
	if exit_code == 0:
		st.success(f"{label} completed successfully.")
	else:
		st.error(f"{label} failed with exit code {exit_code}.")


def _render_last_runs() -> None:
	st.subheader("Last run summaries")

	scrape_summary = _load_scrape_summary()
	if scrape_summary:
		st.markdown("**Latest scrape summary (logs/scrape_summary.json):**")
		st.json(scrape_summary)
	else:
		st.info("No scrape summary found in logs/.")

	latest_scrape = _latest_worklog_entry("scrape_all_courses")
	latest_embed = _latest_worklog_entry("build_embeddings")
	latest_faiss = _latest_worklog_entry("build_faiss")

	if any([latest_scrape, latest_embed, latest_faiss]):
		st.markdown("**Latest WORKLOG entries:**")
		lines: list[str] = []
		if latest_scrape:
			lines.append(latest_scrape)
		if latest_embed:
			lines.append(latest_embed)
		if latest_faiss:
			lines.append(latest_faiss)
		st.code("\n".join(lines), language="text")
	else:
		st.info("No WORKLOG entries found for pipeline steps yet.")


def main() -> None:
	st.title("Admin Data")
	st.caption("Local-only tools for running the pipeline and reviewing run history.")

	st.warning(
		"Running the pipeline can take a long time. Scraping and embeddings can take "
		"minutes to hours depending on network, model, and hardware. The UI will block "
		"while a step runs."
	)

	st.subheader("Pipeline steps")
	col1, col2, col3 = st.columns(3)

	with col1:
		if st.button("Run scrape (01)"):
			_run_script("Scrape courses", ROOT_DIR / "scripts" / "01_scrape_courses.py")

	with col2:
		if st.button("Run embeddings (02)"):
			_run_script("Build embeddings", ROOT_DIR / "scripts" / "02_build_embeddings.py")

	with col3:
		if st.button("Run FAISS index (03)"):
			_run_script("Build FAISS index", ROOT_DIR / "scripts" / "03_build_faiss.py")

	st.divider()
	_render_last_runs()


if __name__ == "__main__":
	main()
