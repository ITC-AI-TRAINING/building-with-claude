# Module 2 Demos — Prompt Engineering for Applications

Three small, single-concept demos that build on the
[`day1/credit_policy_assistant.py`](../../../day1/credit_policy_assistant.py) reference and the
[Module 2 guide](../../../guides/module-02-prompt-engineering-for-applications.md).
Each demo isolates **one** idea instead of combining all of Module 2 into one file, so you can run
them in order and see exactly where each concept lives.

Each demo is its own independent [`uv`](https://docs.astral.sh/uv/) project — its own
`pyproject.toml`, lockfile, and `.venv` — so you can `cd` into just one folder and run it without
touching the others, or hand out a single demo folder on its own.

## The three demos

| # | Project | Concept | Needs a real API key? |
|---|---------|---------|------------------------|
| 1 | [`01-prompt-layers/`](01-prompt-layers/) | System prompts, instruction hierarchy, few-shot — runs the same question through four increasingly complete system prompts | Yes |
| 2 | [`02-grounding-eval/`](02-grounding-eval/) | Reducing unsupported output — an automated pass/fail battery checking section citations and exact fallback wording | Yes — has a `--dry-run` mode |
| 3 | [`03-context-and-caching/`](03-context-and-caching/) | Long-context handling — `count_tokens()` pre-flight and prompt caching (`cache_control: ephemeral`) across repeated calls | Yes |

Each has its own README with setup/run instructions, but the shape is the same for all three:

```bash
cd labs/module-02/demos/01-prompt-layers   # or 02-... / 03-...

uv sync                # creates that project's own .venv
cp .env.example .env
# edit .env and set ANTHROPIC_API_KEY=sk-ant-...

uv run <script>.py
```

## Notes

- Same security rule as the rest of the course: never hardcode a key, never commit `.env` (the
  repo's root `.gitignore` already excludes `.env` and every project's `.venv/` here).
- All three demos read the same source document,
  [`shared/data/apex_bank_credit_policy.md`](../../../shared/data/apex_bank_credit_policy.md), via
  a path resolved from `__file__` — no relative-`cwd` assumptions, so `uv run` works from inside
  each demo folder exactly as shown above.
- Demo 2's `--dry-run` mode grades canned example answers (a "good" set and a deliberately "weak"
  set) instead of calling the API — useful for seeing the grading logic itself before spending any
  tokens. Demos 1 and 3 always call the real API; there's no offline mode for them because the
  concepts they teach (model behaviour under a layered prompt, and server-side prompt caching) only
  exist once a real request is sent.
- Dollar figures are deliberately not printed by any of these demos. If you compute one from a
  token count, check current per-model rates at
  [platform.claude.com/docs](https://platform.claude.com/docs) first.
- Pair each demo with its matching interactive visualization for an offline walkthrough of the same
  idea: [`01-instruction-hierarchy.html`](../01-instruction-hierarchy.html),
  [`02-grounding-and-fallback.html`](../02-grounding-and-fallback.html),
  [`03-long-context-and-caching.html`](../03-long-context-and-caching.html).
