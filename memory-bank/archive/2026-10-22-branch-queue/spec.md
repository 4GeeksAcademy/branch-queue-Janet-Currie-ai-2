# Spec

`Ticket` holds `number`, `client_name`, `service_type`, and `issued_at`. `BranchQueue` keeps one FIFO queue per supported service and one branch-wide counter starting at 1.

Required operations:

- `issue_ticket` validates the service and name, enqueues the ticket, and returns it. A rejected request does not take a number.
- `call_next` removes and returns the oldest ticket for that service. The removal is the claim.
- `peek_next` returns that ticket without removing it.
- `list_waiting` returns all three services, including empty ones, in call order.
- `stats` returns each waiting count and `total`.

The menu can issue, call, list, show stats, and exit. Invalid input is recoverable. Peek has no menu item.

Service identifiers are exact after stripping whitespace. Names are stripped; a blank name is rejected.
