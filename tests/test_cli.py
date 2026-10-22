"""Scripted menu coverage for the branch queue CLI."""

from __future__ import annotations

import unittest

from branch_queue import MENU, run
from queue_manager import BranchQueue


class ScriptedInput:
    def __init__(self, responses: list[str]) -> None:
        self._remaining = list(responses)

    def __call__(self, prompt: str) -> str:
        if not self._remaining:
            raise AssertionError(f"Unexpected prompt: {prompt}")
        return self._remaining.pop(0)

    @property
    def exhausted(self) -> bool:
        return not self._remaining


class CliTests(unittest.TestCase):
    def test_menu_issues_calls_lists_stats_and_recovers(self) -> None:
        queue = BranchQueue()
        scripted = ScriptedInput(
            [
                "1",
                "  Ana  ",
                " deposit ",
                "1",
                "   ",
                "deposit",
                "1",
                "Luis",
                "not-a-service",
                "3",
                "4",
                "2",
                "deposit",
                "2",
                "deposit",
                "9",
                "5",
            ]
        )
        lines: list[str] = []

        result = run(queue, scripted, lines.append)

        text = "\n".join(lines)
        self.assertIsNone(result)
        self.assertTrue(scripted.exhausted)
        self.assertIn(MENU, text)
        self.assertIn("Issued ticket #1 for Ana — deposit", text)
        self.assertNotIn("Issued ticket #2", text)
        self.assertNotIn("Luis", text)
        self.assertIn("Client name cannot be blank.", text)
        self.assertIn("Unknown service type 'not-a-service'.", text)
        self.assertIn("deposit, withdrawal, account_management", text)
        self.assertIn("deposit (1):", text)
        self.assertIn("  #1 Ana — issued ", text)
        self.assertIn("UTC", text)
        self.assertIn("withdrawal (0):", text)
        self.assertIn("  (none)", text)
        self.assertIn("account_management (0):", text)
        self.assertLess(text.index("deposit: 1"), text.index("Now serving #1: Ana (deposit)"))
        self.assertIn("withdrawal: 0", text)
        self.assertIn("account_management: 0", text)
        self.assertIn("total: 1", text)
        self.assertIn("Now serving #1: Ana (deposit)", text)
        self.assertIn("No clients are waiting for deposit.", text)
        self.assertIn("Please enter a number from 1 to 5.", text)
        self.assertEqual(lines[-1], "Goodbye.")
        self.assertEqual(queue.stats()["total"], 0)

    def test_keyboard_interrupt_exits_without_a_traceback(self) -> None:
        lines: list[str] = []

        def interrupt(prompt: str) -> str:
            raise KeyboardInterrupt

        run(BranchQueue(), interrupt, lines.append)
        self.assertEqual(lines[-1], "Goodbye.")

    def test_end_of_input_during_a_prompt_exits_cleanly(self) -> None:
        lines: list[str] = []
        responses = iter(["1"])

        def input_fn(prompt: str) -> str:
            try:
                return next(responses)
            except StopIteration as exc:
                raise EOFError from exc

        run(BranchQueue(), input_fn, lines.append)
        self.assertEqual(lines[-1], "Goodbye.")
        self.assertNotIn("Issued ticket", "\n".join(lines))


if __name__ == "__main__":
    unittest.main()
