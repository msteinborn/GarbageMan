# Starter Agent

A minimal agentic framework for exploring AI-assisted developer workflows. This repository provides a small, local-first "brain" process (LLM control unit) and a lightweight tool server that expose tools the agent can call. The goal is to demonstrate a safe, testable pattern for tool discovery, invocation, and a simple web UI for human interaction.

**High-level intent**
- Demonstrate an agentic workflow that can run tools, ingest JSON results, and let an LLM interpret those results to produce human-friendly answers.
- Provide a compact, local dev environment (FastAPI + simple frontend) to iterate quickly.
- Serve as a starting point for experiments in making repositories "AI-resilient": tooling that augments developer workflows rather than replacing them.

**Repository layout (important files)**
- `brain/` — the LLM control unit (agent). Key files:
  - `brain/main.py` — agent loop, tool discovery, `process_tool_call()` helper
  - `brain/ui/web_server.py` — FastAPI server that exposes the web UI and bridges to the brain
- `tools/` — lightweight tool server exposing tools via HTTP
  - `tools/server.py` — example tools: `calculate_margin`, `get_weather`
- `docker-compose.yml` — compose configuration to run `brain` + `tools` locally

How it works (very brief)
1. The brain fetches a tool list from the tool server and builds a registry.
2. When a user sends a message, the brain (LLM) may decide to call a tool.
3. The web server/brain invoke the tool, receive JSON, and place a `tool_result` block back to the LLM so it can interpret the raw JSON and craft a reply.
4. The web UI displays only the LLM's final reply (tool inputs/results are logged server-side).

Quick start (development)
1. Copy environment variables (if needed) and ensure Docker is installed.
2. Build and run locally via Docker Compose from the repository root:

```bash
docker-compose up --build
```

3. Open the web UI at `http://localhost:8001` (the web server runs in `brain` container on port 8001 by default).

Run instructions (multiple options)

1) Using UV (project workspace manager)

If you use `uv` to manage workspace projects, you can create or recreate the virtual environments and install dependencies via the project's `pyproject.toml` entries. Example (replace `brain`/`tools` with the project module you want to install):

```bash
# export a requirements file from a uv-managed project (optional)
uv export --project brain --format requirements.txt > brain/requirements.txt

# create and activate a venv, then install
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r brain/requirements.txt

# run the service
uvicorn brain.ui.web_server:app --reload --port 8001
```

2) Using plain Python venv (recommended for new contributors)

This approach starts from the minimal `requirements` files in the repo and works on any system with Python 3.9+.

```bash
# create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

# install service dependencies
pip install -r brain/requirements-min.txt
pip install -r tools/requirements.txt

# run services in separate terminals (or use tmux)
uvicorn tools.server:app --reload --port 8000
uvicorn brain.ui.web_server:app --reload --port 8001
```

3) Using Conda / Miniconda (alternate)

```bash
# create and activate a conda env
conda create -n starter-agent python=3.10 -y
conda activate starter-agent

# install pip packages into the conda env
pip install -r brain/requirements-min.txt
pip install -r tools/requirements.txt

# run services
uvicorn tools.server:app --reload --port 8000
uvicorn brain.ui.web_server:app --reload --port 8001
```

4) Using Docker Compose (fast local integration)

```bash
docker-compose up --build
```

Notes
- Use `brain/requirements-min.txt` and `tools/requirements.txt` for quick installs; keep the auto-generated pinned `brain/requirements.txt` for reproducible installs or CI.
- If you use `uv` as a workspace manager, you can export fully pinned requirement files and commit them for reproducibility.

Notes for developers
- The webserver intentionally does not persist raw tool JSON in the UI; full tool logs are kept in server/container logs for privacy and debugging.
- The current implementation serializes `tool_result` as a JSON string when returning it to the LLM (this satisfies the LLM API content requirements).
- `process_tool_call()` returns parsed dicts; the webserver packages them as strings for the model layer.

Work to be done / next steps
- Implement a more robust front end: structured chat UI, better error handling, streaming updates, and accessibility features.
- Build a richer tool server: typed tool schemas, authentication, retries, caching, granular logging, and sandboxing for untrusted code.
- Add tests: unit tests for `process_tool_call()`, integration tests for `tools/server.py`, and end-to-end tests for agent+tools+UI.
- Improve agent prompting and safety guards: tool usage policies, tool input validation, and post-call sanity checks.
- Improve developer DX: add `Makefile` targets, a minimal `README` for contributing, and CI for linting and tests.

Contributing
- This project is experimental. If you'd like to contribute, open issues or pull requests describing the change. Keep changes minimal and well-scoped.

License
- See the `LICENSE` file in the repository root.

Contact / Notes
- Intended use of this agent is TBD; treat this repo as a developer experiment and playfield for iterating on agentic patterns and tooling.
# Testing Initial Commit

