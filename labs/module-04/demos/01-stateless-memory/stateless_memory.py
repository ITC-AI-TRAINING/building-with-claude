"""
Stateless Memory — Message Formatting & Conversation Memory
Module 4: Conversation and Context Management
Based on: day2/loan_intake_manager.py

Runs the SAME three-turn conversation two ways:
  (a) broken_send() — sends only the latest user message each call (no
      history) — this is what "the API remembers for you" would look like,
      if it existed. It doesn't.
  (b) ConversationManager.send() — appends and resends the full history
      every call, exactly like day2/loan_intake_manager.py.

The final turn asks a question that can only be answered correctly if the
earlier turns are still visible to the model.

Run:
    uv run stateless_memory.py
"""

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

SYSTEM_PROMPT = """
You are a loan intake officer at Apex Bank. Answer briefly and directly.
If you don't have enough context to answer a question, say so plainly —
never guess at information you were never given.
"""

TURNS = [
    "Hi, I want to apply for a loan. My name is Priya Sharma and I need a home loan of 40 lakhs.",
    "My monthly salary is 80,000 rupees.",
    "What was my name again, and what loan type did I ask for?",
]


def broken_send(client: anthropic.Anthropic, system: str, user_message: str) -> str:
    """(a) The broken version — only the newest message is ever sent."""
    response = client.messages.create(
        model=MODEL, max_tokens=200, system=system,
        messages=[{"role": "user", "content": user_message}],
    )
    return next((b.text for b in response.content if b.type == "text"), "")


class ConversationManager:
    """(b) The correct version — day2/loan_intake_manager.py's pattern."""

    def __init__(self, client: anthropic.Anthropic, system: str):
        self.client = client
        self.system = system
        self.messages: list[dict] = []

    def send(self, user_message: str) -> str:
        self.messages.append({"role": "user", "content": user_message})
        response = self.client.messages.create(
            model=MODEL, max_tokens=200, system=self.system, messages=self.messages,
        )
        reply = next((b.text for b in response.content if b.type == "text"), "")
        self.messages.append({"role": "assistant", "content": reply})
        return reply


def main() -> None:
    print("=" * 70)
    print("(a) BROKEN — latest message only, no history resent")
    print("=" * 70)
    for turn in TURNS:
        print(f"\n[Applicant] {turn}")
        reply = broken_send(client, SYSTEM_PROMPT, turn)
        print(f"[Officer]   {reply}")

    print("\n" + "=" * 70)
    print("(b) CORRECT — full history resent every call")
    print("=" * 70)
    manager = ConversationManager(client, SYSTEM_PROMPT)
    for turn in TURNS:
        print(f"\n[Applicant] {turn}")
        reply = manager.send(turn)
        print(f"[Officer]   {reply}")

    print("\n" + "=" * 70)
    print("What to notice: on the final turn, (a) has no way to know Priya's name")
    print("or loan type — each call is the model's ENTIRE knowledge of the exchange.")
    print("(b) answers correctly because the full turn history was resent. Neither")
    print("version has server-side memory; the difference is entirely in what the")
    print("client chooses to send.")


if __name__ == "__main__":
    main()
