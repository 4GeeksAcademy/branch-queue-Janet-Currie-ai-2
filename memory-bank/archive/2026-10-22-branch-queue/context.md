# Context

Build a terminal queue manager for Banco Meridional. Clients take numbered tickets for `deposit`, `withdrawal`, or `account_management`. Dedicated agents call the next client for their own service.

The repository started with `branch-queue-context.md` and no application code. The assignment requires a standard-library Python CLI, entry point `branch_queue.py`, separate in-memory queues, and design notes. Persistence, authentication, agent assignment, and a kiosk or web interface are out of scope.

Requirements live in `branch-queue-context.md`. The linked 4Geeks assignment is authoritative when the two differ.
