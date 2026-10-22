# Decisions

- Target Python 3.11+. Use `dataclass(frozen=True, slots=True)` and `datetime.now(timezone.utc)`. No third-party packages.
- Keep the menu in `branch_queue.py` and the queue model in `queue_manager.py`.
- Accept only `deposit`, `withdrawal`, and `account_management` after stripping whitespace. Matching is case-sensitive.
- Strip client names and reject blank names with `InvalidClientNameError`. Allow duplicate names.
- Signal an unknown service with `InvalidServiceTypeError` and an empty valid queue with `EmptyQueueError`. Both subclass `BranchQueueError`.
- Claim a client with `deque.popleft` before returning the ticket. Do not add locks in this single-threaded program.
- Make `tests` a package so `unittest` discovery works on Python 3.13.
- Leave peek off the menu. The model still implements it.
