"""Observable behavior of Ticket and BranchQueue."""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

from queue_manager import (
    SERVICE_TYPES,
    BranchQueue,
    EmptyQueueError,
    InvalidClientNameError,
    InvalidServiceTypeError,
    Ticket,
)


def waiting_counts(**counts: int) -> dict[str, int]:
    stats = {service: 0 for service in SERVICE_TYPES}
    stats.update(counts)
    stats["total"] = sum(stats[service] for service in SERVICE_TYPES)
    return stats


class IssueTicketTests(unittest.TestCase):
    def test_ticket_records_number_name_service_and_utc_timestamp(self) -> None:
        before = datetime.now(timezone.utc)
        ticket = BranchQueue().issue_ticket("Ana", "deposit")
        after = datetime.now(timezone.utc)

        self.assertIsInstance(ticket, Ticket)
        self.assertEqual(ticket.number, 1)
        self.assertEqual(ticket.client_name, "Ana")
        self.assertEqual(ticket.service_type, "deposit")
        self.assertEqual(ticket.issued_at.tzinfo, timezone.utc)
        self.assertLessEqual(before, ticket.issued_at)
        self.assertGreaterEqual(after, ticket.issued_at)

    def test_issued_ticket_cannot_be_edited(self) -> None:
        ticket = BranchQueue().issue_ticket("Ana", "deposit")
        with self.assertRaises(FrozenInstanceError):
            ticket.client_name = "Luis"  # type: ignore[misc]

    def test_numbers_increase_across_services(self) -> None:
        queue = BranchQueue()
        first = queue.issue_ticket("Ana", "deposit")
        second = queue.issue_ticket("Luis", "withdrawal")
        third = queue.issue_ticket("Maya", "deposit")
        fourth = queue.issue_ticket("Omar", "account_management")

        self.assertEqual(
            [first.number, second.number, third.number, fourth.number],
            [1, 2, 3, 4],
        )

    def test_duplicate_names_are_allowed(self) -> None:
        queue = BranchQueue()
        first = queue.issue_ticket("Ana", "deposit")
        second = queue.issue_ticket("Ana", "deposit")

        self.assertEqual([first.number, second.number], [1, 2])
        self.assertEqual(
            [ticket.client_name for ticket in queue.list_waiting()["deposit"]],
            ["Ana", "Ana"],
        )

    def test_surrounding_whitespace_is_stripped(self) -> None:
        ticket = BranchQueue().issue_ticket("  Ana Maria  ", "  withdrawal  ")

        self.assertEqual(ticket.client_name, "Ana Maria")
        self.assertEqual(ticket.service_type, "withdrawal")

    def test_blank_name_does_not_consume_a_number(self) -> None:
        queue = BranchQueue()
        for blank in ("", "   ", "\n\t"):
            with self.assertRaises(InvalidClientNameError):
                queue.issue_ticket(blank, "deposit")

        issued = queue.issue_ticket("Ana", "deposit")
        self.assertEqual(issued.number, 1)
        self.assertEqual(queue.stats(), waiting_counts(deposit=1))

    def test_non_string_name_is_rejected_without_consuming_a_number(self) -> None:
        queue = BranchQueue()
        with self.assertRaises(InvalidClientNameError):
            queue.issue_ticket(None, "deposit")  # type: ignore[arg-type]

        issued = queue.issue_ticket("Ana", "deposit")
        self.assertEqual(issued.number, 1)

    def test_invalid_service_does_not_consume_a_number_or_change_counts(self) -> None:
        queue = BranchQueue()
        queue.issue_ticket("Ana", "deposit")
        before = queue.stats()

        for service in ("Deposit", "loan", "   ", None):
            with self.assertRaises(InvalidServiceTypeError) as caught:
                queue.issue_ticket("Luis", service)  # type: ignore[arg-type]
            self.assertIn("deposit", str(caught.exception))
            self.assertIn("withdrawal", str(caught.exception))
            self.assertIn("account_management", str(caught.exception))

        self.assertEqual(queue.stats(), before)
        self.assertEqual(queue.issue_ticket("Luis", "withdrawal").number, 2)
        self.assertEqual(list(queue.list_waiting()), list(SERVICE_TYPES))


class CallAndPeekTests(unittest.TestCase):
    def test_same_service_calls_follow_arrival_order(self) -> None:
        queue = BranchQueue()
        queue.issue_ticket("Ana", "deposit")
        queue.issue_ticket("Luis", "deposit")
        queue.issue_ticket("Maya", "deposit")

        called = [queue.call_next("deposit").client_name for _ in range(3)]
        self.assertEqual(called, ["Ana", "Luis", "Maya"])

    def test_calling_one_service_leaves_other_queues_unchanged(self) -> None:
        queue = BranchQueue()
        queue.issue_ticket("Ana", "withdrawal")
        queue.issue_ticket("Luis", "deposit")
        queue.issue_ticket("Maya", "withdrawal")
        queue.issue_ticket("Omar", "deposit")

        self.assertEqual(queue.call_next("deposit").client_name, "Luis")
        self.assertEqual(
            [ticket.client_name for ticket in queue.list_waiting()["withdrawal"]],
            ["Ana", "Maya"],
        )
        self.assertEqual(queue.call_next("withdrawal").client_name, "Ana")
        self.assertEqual(queue.call_next("withdrawal").client_name, "Maya")
        self.assertEqual(queue.call_next("deposit").number, 4)

    def test_peek_is_repeatable_and_call_returns_that_ticket(self) -> None:
        queue = BranchQueue()
        queue.issue_ticket("Ana", "deposit")
        queue.issue_ticket("Luis", "deposit")
        before = queue.stats()

        first = queue.peek_next("deposit")
        second = queue.peek_next(" deposit ")
        self.assertIs(first, second)
        self.assertEqual(queue.stats(), before)
        self.assertIs(queue.call_next("deposit"), first)
        self.assertEqual(queue.peek_next("deposit").client_name, "Luis")

    def test_calling_the_last_client_leaves_the_queue_empty(self) -> None:
        queue = BranchQueue()
        queue.issue_ticket("Ana", "account_management")
        queue.call_next("account_management")

        self.assertEqual(queue.stats(), waiting_counts())
        with self.assertRaises(EmptyQueueError) as caught:
            queue.call_next("account_management")
        self.assertIn("account_management", str(caught.exception))
        self.assertEqual(queue.stats(), waiting_counts())

    def test_peek_on_an_empty_service_does_not_change_counts(self) -> None:
        queue = BranchQueue()
        queue.issue_ticket("Ana", "deposit")
        before = queue.stats()

        with self.assertRaises(EmptyQueueError):
            queue.peek_next("withdrawal")

        self.assertEqual(queue.stats(), before)
        self.assertEqual(queue.peek_next("deposit").client_name, "Ana")

    def test_invalid_service_on_call_or_peek_does_not_change_the_queue(self) -> None:
        queue = BranchQueue()
        queue.issue_ticket("Ana", "deposit")
        before = queue.stats()

        for operation in (queue.call_next, queue.peek_next):
            with self.assertRaises(InvalidServiceTypeError):
                operation("not-a-service")

        self.assertEqual(queue.stats(), before)
        self.assertEqual(queue.peek_next("deposit").client_name, "Ana")


class ReadModelTests(unittest.TestCase):
    def test_empty_queue_lists_every_service_and_zero_counts(self) -> None:
        queue = BranchQueue()

        waiting = queue.list_waiting()
        self.assertEqual(list(waiting), list(SERVICE_TYPES))
        self.assertTrue(all(tickets == [] for tickets in waiting.values()))
        self.assertTrue(all(isinstance(tickets, list) for tickets in waiting.values()))
        self.assertEqual(queue.stats(), waiting_counts())

    def test_list_waiting_preserves_call_order_for_partial_queues(self) -> None:
        queue = BranchQueue()
        queue.issue_ticket("Ana", "deposit")
        queue.issue_ticket("Luis", "withdrawal")
        queue.issue_ticket("Maya", "deposit")

        waiting = queue.list_waiting()
        self.assertEqual(
            [ticket.client_name for ticket in waiting["deposit"]],
            ["Ana", "Maya"],
        )
        self.assertEqual(
            [ticket.client_name for ticket in waiting["withdrawal"]],
            ["Luis"],
        )
        self.assertEqual(waiting["account_management"], [])
        self.assertEqual(queue.call_next("deposit").client_name, "Ana")

    def test_changing_the_returned_list_does_not_change_the_queue(self) -> None:
        queue = BranchQueue()
        queue.issue_ticket("Ana", "deposit")
        waiting = queue.list_waiting()
        waiting["deposit"].clear()
        waiting["withdrawal"].append(queue.peek_next("deposit"))

        self.assertEqual(queue.peek_next("deposit").client_name, "Ana")
        self.assertEqual(queue.stats(), waiting_counts(deposit=1))

    def test_stats_drop_after_a_call_and_total_matches_the_sum(self) -> None:
        queue = BranchQueue()
        queue.issue_ticket("Ana", "deposit")
        queue.issue_ticket("Luis", "deposit")
        queue.issue_ticket("Maya", "withdrawal")
        self.assertEqual(queue.stats(), waiting_counts(deposit=2, withdrawal=1))

        queue.call_next("deposit")
        stats = queue.stats()
        self.assertEqual(stats, waiting_counts(deposit=1, withdrawal=1))
        self.assertEqual(
            stats["total"],
            sum(stats[service] for service in SERVICE_TYPES),
        )


if __name__ == "__main__":
    unittest.main()
