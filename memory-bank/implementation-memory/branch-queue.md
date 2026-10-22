# Branch Queue

## Purpose

Model a bank branch where clients take numbered tickets for deposit, withdrawal, or account management, and an agent can call the next client for one service without scanning the other lines.

## Final Behavior

`python branch_queue.py` opens a menu that can issue a ticket, call the next client for a service, list waiting clients grouped by service, show waiting counts, and exit. Invalid menu choices, blank names, unknown services, and empty queues print a message and return to the menu. End of input and keyboard interrupt print `Goodbye.` and exit.

Ticket numbers start at 1 and increase across every service. Within one service, clients are called first in, first out. Peeking is available on `BranchQueue` and is not a menu option.

## Architecture and Data Flow

`branch_queue.py` owns the menu. It calls `queue_manager.BranchQueue` and prints the results. `run` accepts input and output callables so tests can drive the menu without a terminal.

`BranchQueue` keeps one `collections.deque` per service and one `_next_number` counter. Issuing appends to the right of the matching deque. Calling uses `popleft`, and that removal is the claim. Listing and statistics copy or count the current contents and leave the queues unchanged.

There is no persistence, network API, authentication, or third-party dependency.

## Important Files

- `branch_queue.py` — menu entry point
- `queue_manager.py` — `Ticket`, `BranchQueue`, service identifiers, and expected errors
- `DESIGN.md` — why each service has its own queue, and why a ticket must be removed before it is announced
- `tests/test_queue_manager.py` — domain behavior
- `tests/test_cli.py` — scripted menu
- `tests/__init__.py` — makes `tests` importable for `unittest` discovery on Python 3.13
- `README.md` — how to run and test

## Interfaces and Contracts

Supported services, after stripping surrounding whitespace, are exactly `deposit`, `withdrawal`, and `account_management`. Matching is case-sensitive.

`issue_ticket(client_name, service_type)` returns a frozen `Ticket` with `number`, `client_name`, `service_type`, and a timezone-aware UTC `issued_at`. Blank names and unknown services raise `InvalidClientNameError` or `InvalidServiceTypeError` and do not take a number.

`call_next` and `peek_next` use the same service check. An empty valid service raises `EmptyQueueError`. `call_next` removes the ticket with `popleft` before returning it. `peek_next` returns the same front ticket until a call changes that queue.

`list_waiting()` returns a dictionary with all three services in that order. Each value is a new list of tickets in call order. `stats()` returns the waiting count for each service and a `total` key.

These errors subclass `BranchQueueError`. The menu prints `str(error)`.

## Decisions and Constraints

- Python 3.11 or newer, standard library only. Developed and tested with Python 3.13.
- Client names are stripped. Internal spaces remain. Duplicate names are allowed. There is no length limit.
- Unknown services do not create new queues.
- The single-threaded menu does not take locks. `call_next` still claims with `popleft`. A future threaded version would need that removal inside a lock, or an equivalent single removal, for the service queue.
- No peek menu item, persistence, auth, or agent assignment.

## Validation

On Python 3.13.14:

- `python3 -m unittest discover -s tests -t . -v` — 21 tests, all passed.
- `python3 -m compileall -q queue_manager.py branch_queue.py tests` — succeeded.
- A piped run of `python3 branch_queue.py` issued ticket 1 for Ana, showed a deposit count of 1, called Ana, reported an empty withdrawal queue, rejected menu choice 9, and exited 0.

No browser check applies. This is a terminal program.

## Maintenance Notes

Keep queue operations in `queue_manager.py` so tests do not need the menu. Add a service only by extending `SERVICE_TYPES` and the queues created in `BranchQueue`; invalid input must not add a key. Preserve global numbering and per-service FIFO. Keep `popleft` as the claim in `call_next`, and update `DESIGN.md` if that mutation order changes.
