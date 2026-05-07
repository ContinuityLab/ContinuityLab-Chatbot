"""Console / scripted IO adapters for the engine.

The state machine talks to the world through a `Console` so that:
- Production runs use the live stdin/stdout console.
- Tests script answers deterministically without monkey-patching `input()`.
"""
from __future__ import annotations

from collections import deque
from typing import Iterable, Optional, Protocol


class Console(Protocol):
    def say(self, message: str) -> None: ...

    def ask(self, prompt: str) -> str: ...


class StdConsole:
    def say(self, message: str) -> None:
        print(message)

    def ask(self, prompt: str) -> str:
        return input(prompt).strip()


class ScriptedConsole:
    """Replay a queue of pre-written answers, capturing every emitted line.

    Raises if the script runs out — that means the test under-specified the
    branch the engine ended up taking.
    """

    def __init__(self, answers: Iterable[str]) -> None:
        self._answers = deque(answers)
        self.transcript: list[tuple[str, str]] = []  # (kind, text)

    def say(self, message: str) -> None:
        self.transcript.append(("say", message))

    def ask(self, prompt: str) -> str:
        if not self._answers:
            raise AssertionError(
                f"ScriptedConsole ran out of answers; last prompt was: {prompt!r}"
            )
        answer = self._answers.popleft()
        self.transcript.append(("ask", f"{prompt} -> {answer}"))
        return answer


def prompt_yes_no(console: Console, prompt: str) -> bool:
    while True:
        ans = console.ask(prompt).lower()
        if ans.startswith("y"):
            return True
        if ans.startswith("n"):
            return False
        console.say("Please answer Yes or No.")


def prompt_choice(console: Console, prompt: str, valid: Iterable[str]) -> str:
    valid_set = {v.upper() for v in valid}
    while True:
        ans = console.ask(prompt).upper()
        if ans in valid_set:
            return ans
        console.say(f"Please choose one of: {', '.join(sorted(valid_set))}.")


def prompt_int(console: Console, prompt: str, *, low: int, high: int) -> int:
    while True:
        raw = console.ask(prompt)
        try:
            value = int(raw)
        except ValueError:
            console.say(f"Please enter a whole number between {low} and {high}.")
            continue
        if low <= value <= high:
            return value
        console.say(f"Value must be between {low} and {high}.")


def prompt_optional(console: Console, prompt: str) -> Optional[str]:
    raw = console.ask(prompt)
    return raw or None
