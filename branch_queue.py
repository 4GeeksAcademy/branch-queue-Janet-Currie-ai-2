"""Terminal menu for the branch queue."""

from __future__ import annotations

from collections.abc import Callable

from queue_manager import SERVICE_TYPES, BranchQueue, BranchQueueError, Ticket

InputFn = Callable[[str], str]
OutputFn = Callable[[str], None]

MENU = """\
Branch Queue
1. Issue a ticket
2. Call the next client
3. View waiting clients
4. View statistics
5. Exit\
"""


class _ExitRequested(Exception):
    """The operator closed input or interrupted the program."""


def main() -> None:
    """Run the menu against a new in-memory queue."""
    run(BranchQueue())


def run(
    queue: BranchQueue,
    input_fn: InputFn = input,
    output_fn: OutputFn = print,
) -> None:
    """Repeat the menu until the operator exits or closes input."""
    try:
        while True:
            output_fn(MENU)
            choice = _read_line(input_fn, "Select an option: ").strip()
            if choice == "1":
                _issue_ticket(queue, input_fn, output_fn)
            elif choice == "2":
                _call_next(queue, input_fn, output_fn)
            elif choice == "3":
                _show_waiting(queue, output_fn)
            elif choice == "4":
                _show_stats(queue, output_fn)
            elif choice == "5":
                output_fn("Goodbye.")
                return
            else:
                output_fn("Please enter a number from 1 to 5.")
    except _ExitRequested:
        output_fn("Goodbye.")


def _read_line(input_fn: InputFn, prompt: str) -> str:
    try:
        return input_fn(prompt)
    except (EOFError, KeyboardInterrupt) as exc:
        raise _ExitRequested from exc


def _issue_ticket(queue: BranchQueue, input_fn: InputFn, output_fn: OutputFn) -> None:
    try:
        client_name = _read_line(input_fn, "Client name: ")
        service_type = _read_line(input_fn, "Service type: ")
        ticket = queue.issue_ticket(client_name, service_type)
    except BranchQueueError as error:
        output_fn(str(error))
        return
    output_fn(
        f"Issued ticket #{ticket.number} for {ticket.client_name} — {ticket.service_type}"
    )


def _call_next(queue: BranchQueue, input_fn: InputFn, output_fn: OutputFn) -> None:
    try:
        service_type = _read_line(input_fn, "Service type: ")
        ticket = queue.call_next(service_type)
    except BranchQueueError as error:
        output_fn(str(error))
        return
    output_fn(
        f"Now serving #{ticket.number}: {ticket.client_name} ({ticket.service_type})"
    )


def _show_waiting(queue: BranchQueue, output_fn: OutputFn) -> None:
    for service, tickets in queue.list_waiting().items():
        output_fn(f"{service} ({len(tickets)}):")
        if not tickets:
            output_fn("  (none)")
            continue
        for ticket in tickets:
            output_fn(
                f"  #{ticket.number} {ticket.client_name} — issued {_format_issued_at(ticket)}"
            )


def _show_stats(queue: BranchQueue, output_fn: OutputFn) -> None:
    counts = queue.stats()
    for service in SERVICE_TYPES:
        output_fn(f"{service}: {counts[service]}")
    output_fn(f"total: {counts['total']}")


def _format_issued_at(ticket: Ticket) -> str:
    return ticket.issued_at.strftime("%Y-%m-%d %H:%M:%S UTC")


if __name__ == "__main__":
    main()
