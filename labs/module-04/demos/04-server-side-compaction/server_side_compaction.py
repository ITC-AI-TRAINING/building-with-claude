"""
Server-Side Compaction — Automatic Context Management via the Beta API
Module 4: Conversation and Context Management
Based on: day2/loan_intake_manager.py, and contrasts with this module's own
02-token-aware-summarization/ demo.

Demo 2 (02-token-aware-summarization/) shows the MANUAL pattern: your own code
calls count_tokens() after every turn and, once a (deliberately low) threshold
is crossed, your own code calls the model a second time to summarise the
history and reset it. This demo shows the SERVER-SIDE alternative: the beta
`compact-2026-01-12` compaction feature. You pass
`context_management={"edits": [{"type": "compact_20260112", "trigger": ...}]}`
on every request, and once the conversation's input tokens approach the
trigger, the API itself returns an extra `compaction` content block that
summarises everything so far — no second call, no do-it-yourself
summarise_and_reset(). You still MUST append the full `response.content`
(compaction block included) back onto `messages`, or the server has nothing
to compact against next turn and silently keeps re-sending the entire history.

The real production default trigger is 150,000 input tokens — far more than a
short scripted demo would ever reach turn-by-turn. Rather than waiting for
that (or lowering the trigger below what the API allows — 50,000 is the
enforced floor), this demo pre-loads the very first turn with a large block
of repeated "policy reference" filler text, sized with count_tokens() so it
comfortably clears the trigger by itself. That one oversized first turn
stands in for "150K tokens of real conversation already happened" — the
compaction fires almost immediately, and every turn afterward shows the
server-compacted, much smaller `usage.input_tokens` in its place.

Run:
    uv run server_side_compaction.py
    uv run server_side_compaction.py --trigger 60000
"""

import argparse
import math
import os

import anthropic
from dotenv import load_dotenv

load_dotenv()

if not os.environ.get("ANTHROPIC_API_KEY"):
    raise EnvironmentError(
        "ANTHROPIC_API_KEY is not set.\n"
        "Copy .env.example to .env in this folder and add your key, e.g.:\n"
        "    cp .env.example .env"
    )

client = anthropic.Anthropic()
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")

# Compaction (compact_20260112) only works on this specific set of models —
# unlike demo 2, plugging in e.g. Haiku (a normally-fine cost-saving swap)
# fails outright with a 400. `load_dotenv()` above walks UP from this folder
# looking for a .env, so if you haven't run `cp .env.example .env` in this
# folder specifically, ANTHROPIC_MODEL is silently inherited from the repo
# root's .env (which defaults to claude-haiku-4-5 for cost reasons across
# Days 2-5) — this check catches that before it reaches the API as a 400.
COMPACTION_SUPPORTED_MODEL_PREFIXES = (
    "claude-sonnet-4-6",
    "claude-sonnet-5",
    "claude-opus-4-6",
    "claude-opus-4-7",
    "claude-opus-4-8",
    "claude-fable-5",
    "claude-mythos-5",
)
if not MODEL.startswith(COMPACTION_SUPPORTED_MODEL_PREFIXES):
    raise EnvironmentError(
        f"ANTHROPIC_MODEL is set to '{MODEL}', which does not support the "
        "compact_20260112 context management strategy this demo requires.\n"
        "Supported models: claude-sonnet-4-6, claude-sonnet-5, claude-opus-4-6, "
        "claude-opus-4-7, claude-opus-4-8, claude-fable-5.\n\n"
        "If you didn't set ANTHROPIC_MODEL yourself, this is almost certainly "
        "being inherited from the repo root's .env. Fix it by creating this "
        "folder's OWN .env (which takes precedence once it exists):\n"
        "    cp .env.example .env\n"
        "and confirming it sets ANTHROPIC_MODEL=claude-sonnet-4-6 (or another "
        "supported model above)."
    )

COMPACTION_BETA = "compact-2026-01-12"

# API-enforced floor for context_management.edits[].trigger.value — the real
# production default is 150,000; this is just the lowest value the API will
# accept, same role as demo 2's artificially-low --threshold.
MIN_TRIGGER_TOKENS = 50_000
DEFAULT_TRIGGER_TOKENS = 50_000
DEFAULT_SEED_BUFFER = 4_000  # headroom above the trigger so the seed reliably clears it

SYSTEM_PROMPT = """
You are a loan intake officer at Apex Bank.
Your job is to collect: full name, loan type (home/personal/business/vehicle),
loan amount required (INR), monthly income (INR), desired tenure (years), and
approximate credit score (if known).
Ask for one or two pieces of information at a time. Be polite and professional.
When you have collected all details, say "INTAKE COMPLETE" and summarise.
"""

# Same 6-turn script as 02-token-aware-summarization/, so the two demos are
# directly comparable: same conversation, two different context-management
# strategies (manual reset vs. server-side compaction).
APPLICANT_TURNS = [
    "Hi there, I've been thinking about applying for a home loan for a while "
    "now and I finally have some time to sit down and go through the process "
    "properly, so I'd like to get started today if that's alright.",
    "Sure — my full name is Ananya Desai, and I currently work as a senior "
    "product manager at a mid-sized software company here in Bengaluru. I've "
    "been with the same employer for about four years now.",
    "The property I'm interested in is a 3-bedroom apartment, and the loan "
    "amount I'm looking for is around 65 lakhs, though I might adjust that "
    "depending on what you tell me about eligibility and interest rates.",
    "My monthly take-home salary after all deductions is roughly 1,40,000 "
    "rupees, and I also receive an annual bonus that's usually another two "
    "months of salary, though that varies year to year.",
    "For tenure, I was thinking somewhere between 15 and 20 years would be "
    "comfortable, but I'm open to your recommendation based on the EMI it "
    "would work out to at each length.",
    "As for my credit score, I checked it last month through one of those "
    "free apps and it showed around 765, though I know the bank might pull a "
    "slightly different number from the official bureau.",
]

# Pure token-padding filler, repeated to build the seed turn below. Not a
# real policy document — its only job is to be long and cheap to repeat.
FILLER_PARAGRAPH = (
    "Apex Bank Retail Lending Reference Note: Loan officers must verify "
    "applicant identity, income documentation, and existing credit "
    "obligations before quoting indicative terms. Standard turnaround for "
    "salaried applicants is five business days from complete document "
    "submission to conditional approval; self-employed applicants may "
    "require an additional review cycle for income averaging across the "
    "most recent two assessment years. All indicative rates quoted during "
    "intake are subject to final underwriting and may change based on "
    "bureau score, loan-to-value ratio, and the applicant's debt-to-income "
    "ratio at the time of formal approval."
)


def build_seed_text(target_tokens: int) -> str:
    """Repeat FILLER_PARAGRAPH until it comfortably clears target_tokens.

    Uses count_tokens() twice: once to measure a single paragraph, once to
    confirm the assembled seed actually clears the target — the same
    token-aware sizing idea as 02-token-aware-summarization/, just used here
    to build a seed instead of to trigger a reset.
    """
    one_paragraph_tokens = client.messages.count_tokens(
        model=MODEL, messages=[{"role": "user", "content": FILLER_PARAGRAPH}],
    ).input_tokens

    repeats = math.ceil(target_tokens / one_paragraph_tokens) + 1
    seed_text = "\n\n".join([FILLER_PARAGRAPH] * repeats)

    actual_tokens = client.messages.count_tokens(
        model=MODEL, messages=[{"role": "user", "content": seed_text}],
    ).input_tokens
    print(f"  [seed built: {repeats} paragraphs, ~{actual_tokens} tokens on their own]")

    return seed_text


def send(messages: list, context_management: dict) -> anthropic.types.Message:
    response = client.beta.messages.create(
        betas=[COMPACTION_BETA],
        model=MODEL,
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=messages,
        context_management=context_management,
    )
    # CRITICAL: append the full content list, not just the text. The
    # `compaction` block (when present) must be preserved verbatim — the API
    # uses its presence in `messages` to know what's already been summarised.
    messages.append({"role": "assistant", "content": response.content})
    return response


def report_turn(response: anthropic.types.Message) -> bool:
    reply_text = next((b.text for b in response.content if b.type == "text"), "")
    compaction_block = next((b for b in response.content if b.type == "compaction"), None)

    print(f"[Officer]   {reply_text}")
    print(f"  [usage.input_tokens this request: {response.usage.input_tokens}]")

    if compaction_block:
        preview = compaction_block.content[:220]
        if len(compaction_block.content) > 220:
            preview += "..."
        print("  [COMPACTION TRIGGERED] server condensed everything before this point:")
        print(f"    \"{preview}\"")

    return compaction_block is not None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--trigger", type=int, default=DEFAULT_TRIGGER_TOKENS,
        help=f"context_management trigger.value in input tokens (default {DEFAULT_TRIGGER_TOKENS} — "
             f"the API's own enforced floor; production default is 150,000).",
    )
    parser.add_argument(
        "--seed-buffer", type=int, default=DEFAULT_SEED_BUFFER,
        help=f"Extra tokens above --trigger to build into the seed turn (default {DEFAULT_SEED_BUFFER}).",
    )
    args = parser.parse_args()

    trigger = args.trigger
    if trigger < MIN_TRIGGER_TOKENS:
        print(f"[WARN] --trigger {trigger} is below the API's enforced floor of "
              f"{MIN_TRIGGER_TOKENS} — the request would be rejected. Clamping to {MIN_TRIGGER_TOKENS}.")
        trigger = MIN_TRIGGER_TOKENS

    context_management = {
        "edits": [{
            "type": "compact_20260112",
            "trigger": {"type": "input_tokens", "value": trigger},
        }],
    }

    print(f"Trigger for this run: {trigger} input tokens "
          f"(artificially low — production default is 150,000, the enforced floor is {MIN_TRIGGER_TOKENS})\n")

    messages: list = []
    compactions_seen = 0

    # Turn 0: an oversized seed turn standing in for "a long conversation
    # already happened". This is what actually clears the trigger — the
    # 6 real turns below are then a normal, short conversation that keeps
    # going seamlessly on top of the server-compacted history.
    print("[Applicant] (loading a large internal policy reference before we begin...)")
    seed_text = build_seed_text(trigger + args.seed_buffer)
    seed_prompt = (
        "Before we start, here is our internal lending reference material for "
        "context during this call. Just reply with a one-sentence "
        "acknowledgment that you've reviewed it — don't summarise it back to me.\n\n"
        + seed_text
    )
    messages.append({"role": "user", "content": seed_prompt})
    response = send(messages, context_management)
    if report_turn(response):
        compactions_seen += 1
    print()

    for turn in APPLICANT_TURNS:
        print(f"[Applicant] {turn}")
        messages.append({"role": "user", "content": turn})
        response = send(messages, context_management)
        if report_turn(response):
            compactions_seen += 1
        print()

        reply_text = next((b.text for b in response.content if b.type == "text"), "")
        if "INTAKE COMPLETE" in reply_text:
            break

    print(f"Done. {compactions_seen} compaction event(s) observed across "
          f"{len(APPLICANT_TURNS) + 1} request(s) — the API did the summarising, not our code.")


if __name__ == "__main__":
    main()
