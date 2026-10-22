# Branch Queue

Terminal queue manager for a bank branch. A client takes a numbered ticket for `deposit`, `withdrawal`, or `account_management`. Each service has its own waiting line. Ticket numbers come from one branch-wide sequence, starting at 1.

Requires Python 3.11 or newer. The program uses only the Python standard library.

## Run

```bash
python branch_queue.py
```

The menu issues a ticket, calls the next client for a service, lists who is waiting, shows counts, and exits. Invalid input returns to the menu.

## Test

```bash
python -m unittest discover -s tests -t . -v
```

`tests` is a package so discovery can import it.

Design notes for the per-service queues and simultaneous `call_next` are in [DESIGN.md](DESIGN.md).
