# Demo 1 — Stateless Memory: Message Formatting &amp; Conversation Memory

**Module 4: Conversation and Context Management**
Based on [`day2/loan_intake_manager.py`](../../../../day2/loan_intake_manager.py).

Runs the same three-turn conversation two ways — a broken version that only ever sends the latest
message, and the correct `ConversationManager` pattern that resends the full history every call —
to prove, concretely, that the Claude API has no server-side memory of its own.

Independent [`uv`](https://docs.astral.sh/uv/) project — its own `pyproject.toml`, lockfile, and
`.venv`.

## Setup

```bash
uv sync
cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY=sk-ant-...
```

## Run

```bash
uv run stateless_memory.py
```

## What to notice

- The final applicant turn — *"What was my name again, and what loan type did I ask for?"* — can
  only be answered correctly if the earlier turns are still visible to the model.
- **(a) broken_send()** sends only that one question, with no history. The system prompt tells
  Claude to admit when it lacks context rather than guess — watch it do exactly that.
- **(b) ConversationManager.send()** resends the full turn list every call. The same question gets
  answered correctly, because "Priya Sharma" and "home loan" are still sitting right there in
  `messages`.
- Neither version has any help from the server — the Claude API doesn't remember anything between
  calls either way. The only difference between (a) and (b) is what the **client** chooses to
  include in the request.
- [`01-stateless-vs-stateful.html`](../../01-stateless-vs-stateful.html) shows this same contrast
  offline, with no API calls.
