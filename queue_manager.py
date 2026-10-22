"""In-memory branch queue: one FIFO line per service, one ticket sequence."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone

SERVICE_TYPES = ("deposit", "withdrawal", "account_management")


class BranchQueueError(Exception):
    """Expected failure from a branch-queue operation."""


class InvalidServiceTypeError(BranchQueueError):
    """Raised when a service type is not one of the supported identifiers."""

    def __init__(self, service_type: object) -> None:
        self.service_type = service_type
        valid = ", ".join(SERVICE_TYPES)
        super().__init__(
            f"Unknown service type {service_type!r}. Choose one of: {valid}."
        )


class EmptyQueueError(BranchQueueError):
    """Raised when a service queue has no waiting clients."""

    def __init__(self, service_type: str) -> None:
        self.service_type = service_type
        super().__init__(f"No clients are waiting for {service_type}.")


class InvalidClientNameError(BranchQueueError):
    """Raised when a client name is blank."""

    def __init__(self) -> None:
        super().__init__("Client name cannot be blank.")


@dataclass(frozen=True, slots=True)
class Ticket:
    """One client's place in a service queue."""

    number: int
    client_name: str
    service_type: str
    issued_at: datetime


class BranchQueue:
    """Coordinates per-service waiting lines and the shared ticket counter."""

    def __init__(self) -> None:
        self._queues: dict[str, deque[Ticket]] = {
            service: deque() for service in SERVICE_TYPES
        }
        self._next_number = 1

    def issue_ticket(self, client_name: str, service_type: str) -> Ticket:
        """Validate, number, and enqueue a ticket. Return the issued ticket."""
        normalized_service = self._normalize_service_type(service_type)
        normalized_name = self._normalize_client_name(client_name)
        ticket = Ticket(
            number=self._next_number,
            client_name=normalized_name,
            service_type=normalized_service,
            issued_at=datetime.now(timezone.utc),
        )
        self._queues[normalized_service].append(ticket)
        self._next_number += 1
        return ticket

    def call_next(self, service_type: str) -> Ticket:
        """Remove and return the client who has waited longest for this service."""
        normalized = self._normalize_service_type(service_type)
        queue = self._queues[normalized]
        try:
            # Claim the client by removing the ticket before it is returned.
            # See DESIGN.md.
            return queue.popleft()
        except IndexError:
            raise EmptyQueueError(normalized) from None

    def peek_next(self, service_type: str) -> Ticket:
        """Return the next ticket for this service without removing it."""
        normalized = self._normalize_service_type(service_type)
        queue = self._queues[normalized]
        try:
            return queue[0]
        except IndexError:
            raise EmptyQueueError(normalized) from None

    def list_waiting(self) -> dict[str, list[Ticket]]:
        """Return every service queue in call order, including empty services."""
        return {service: list(self._queues[service]) for service in SERVICE_TYPES}

    def stats(self) -> dict[str, int]:
        """Return the waiting count for each service and the overall total."""
        counts = {service: len(self._queues[service]) for service in SERVICE_TYPES}
        counts["total"] = sum(counts.values())
        return counts

    def _normalize_service_type(self, service_type: object) -> str:
        if isinstance(service_type, str):
            candidate = service_type.strip()
            if candidate in SERVICE_TYPES:
                return candidate
        raise InvalidServiceTypeError(service_type)

    def _normalize_client_name(self, client_name: object) -> str:
        if isinstance(client_name, str):
            normalized = client_name.strip()
            if normalized:
                return normalized
        raise InvalidClientNameError()
