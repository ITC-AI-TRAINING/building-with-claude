"""
Token-Aware Summarization — Token-Aware Design & Summarisation Memory
Module 4: Conversation and Context Management
Based on: day2/loan_intake_manager.py

Runs a longer, more talkative scripted conversation than the reference
script's 4-turn demo, checking client.messages.count_tokens() after every
turn against a deliberately LOW threshold (so it actually fires within a
short demo — day2/loan_intake_manager.py's real threshold is 50,000, which a
handful of turns never reaches) and triggering summarise_and_reset() the
moment it's crossed — the condition-based trigger, not the scripted
"if turn == 3" one.

Run:
    uv run token_aware_summarization.py
    uv run token_aware_summarization.py --threshold 400
"""

import argparse
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
You are a loan intake officer at Apex Bank.
Your job is to collect: full name, loan type (home/personal/business/vehicle),
loan amount required (INR), monthly income (INR), desired tenure (years), and
approximate credit score (if known).
Ask for one or two pieces of information at a time. Be polite and professional.
When you have collected all details, say "INTAKE COMPLETE" and summarise.
"""

# A more talkative script than day2/loan_intake_manager.py's 4-turn demo, so a
# LOW artificial threshold actually gets crossed within a short run.
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

DEFAULT_THRESHOLD = 600  # artificially low — production uses 50,000 (see the guide)


class ConversationManager:
    def __init__(self, client: anthropic.Anthropic, system: str, threshold: int):
        self.client = client
        self.system = system
        self.threshold = threshold
        self.messages: list[dict] = []

    def send(self, user_message: str) -> str:
        self.messages.append({"role": "user", "content": user_message})
        response = self.client.messages.create(
            model=MODEL, max_tokens=300, system=self.system, messages=self.messages,
        )
        reply = next((b.text for b in response.content if b.type == "text"), "")
        self.messages.append({"role": "assistant", "content": reply})
        return reply

    def token_count(self) -> int:
        result = self.client.messages.count_tokens(
            model=MODEL, system=self.system, messages=self.messages,
        )
        return result.input_tokens

    def summarise_and_reset(self) -> str:
        history_text = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in self.messages)
        response = self.client.messages.create(
            model=MODEL, max_tokens=300,
            messages=[{
                "role": "user",
                "content": (
                    "Summarise this loan intake conversation in <=150 words. "
                    "Preserve: applicant name, loan type, amount, income, tenure, credit score.\n\n"
                    f"{history_text}"
                ),
            }],
        )
        summary = next((b.text for b in response.content if b.type == "text"), "")
        self.messages = [{"role": "user", "content": f"[Session summary]\n{summary}"}]
        return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD,
                         help=f"Token threshold that triggers summarise-and-reset (default {DEFAULT_THRESHOLD}, artificially low for this demo).")
    args = parser.parse_args()

    manager = ConversationManager(client, SYSTEM_PROMPT, args.threshold)
    print(f"Threshold for this run: {args.threshold} tokens "
          f"(artificially low — production uses 50,000, see day2/loan_intake_manager.py)\n")

    resets = 0
    turns_run = 0
    for i, turn in enumerate(APPLICANT_TURNS, 1):
        turns_run = i
        print(f"[Applicant] {turn}")
        reply = manager.send(turn)
        print(f"[Officer]   {reply}")

        tokens = manager.token_count()
        print(f"  [tokens: {tokens}]")
        if tokens > manager.threshold:
            print("  [INFO] threshold crossed — summarising and resetting...")
            summary = manager.summarise_and_reset()
            resets += 1
            print(f"  [Summary #{resets}] {summary}")
            print(f"  [tokens after reset: {manager.token_count()}]")
        print()

        if "INTAKE COMPLETE" in reply:
            break

    print(f"Done. Triggered {resets} summarise-and-reset cycle(s) across {turns_run} turn(s).")


if __name__ == "__main__":
    main()
