# Implementation plan

The plan implemented here was the Branch Queue CLI plan.

1. Add `queue_manager.py` with `Ticket`, `BranchQueue`, the three service queues, and the expected errors.
2. Add `branch_queue.py` as the menu entry point, with input and output callables so the loop can be tested.
3. Explain separate queues and the `call_next` claim order in `DESIGN.md`.
4. Cover numbering, FIFO, isolation, peek, empty queues, invalid input, listing, statistics, and a scripted menu with `unittest`.
5. Document how to run and test the program, then record the finished iteration in the memory bank.

The plan excluded persistence, authentication, a peek menu item, third-party packages, and a commit.
