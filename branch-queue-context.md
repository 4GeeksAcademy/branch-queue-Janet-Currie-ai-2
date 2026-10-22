# Branch Queue — Project Context

## Context Purpose

This document defines the business problem, required scope, constraints, and success conditions for the Branch Queue project. It is intended to give a separate implementation-planning agent enough context to produce a detailed implementation plan without having to infer requirements from an empty repository.

This is context only. It does not prescribe a step-by-step implementation plan and does not represent completed application code.

## Source of Truth

- Assignment: [Branch Queue — Tagged Service Queue Manager](https://github.com/4GeeksAcademy/ai-engineering-syllabus/blob/main/content/projects/branch-queue/README.md)
- Source reviewed: October 21, 2026
- Repository state at the start of this iteration: brand new Git repository, no commits, application code, tests, dependency files, or existing project conventions.
- When this document and the linked assignment differ, the linked assignment is authoritative unless the project owner explicitly changes the requirements.

## Project Goal

Build a small terminal-based queue manager that models how a bank branch issues numbered tickets and calls clients for service. The model is a precursor to possible future touchscreen-kiosk integration, but this project itself is only a command-line, in-memory Python application.

The primary engineering objective is to model independent service queues correctly and efficiently. An agent assigned to one service must be able to retrieve that service's next waiting client immediately, without scanning clients waiting for other services.

## Business Background and Reason for the Project

Banco Meridional has replaced physical standing lines with numbered tickets. A client takes a ticket, selects the service they need, and waits to be called. The supported services are:

- `deposit`
- `withdrawal`
- `account_management`

The branch has dedicated agents for each service type. Each agent operates independently and serves only clients waiting for that agent's assigned service.

The current paper-based approach effectively mixes clients into one general list. This makes it difficult for a free agent to find the oldest waiting client for their own service without scanning unrelated entries. The problem becomes more pronounced as the waiting room fills.

The new system must therefore maintain distinct waiting order by service while preserving a single, branch-wide ticket-number sequence. It must make the next client for any service directly available, regardless of how many clients are waiting for other services.

## Intended Users and Interactions

The immediate user is a terminal operator modeling branch activity. Through a repeating text menu, the operator must be able to:

1. Issue a ticket by entering a client's name and service type.
2. Call the next client for a selected service type.
3. View all waiting clients, grouped by service and ordered within each group.
4. View queue statistics.
5. Exit the program cleanly.

The core queue model must also support peeking at the next client for a service without removing that client, even though the assignment does not explicitly require a dedicated CLI menu option for peek.

## Required Domain Model

### Ticket

A `Ticket` class or dataclass represents one client's place in the branch queue. At minimum, each ticket must contain:

- `number`: an integer assigned from a single global sequence across all service types.
- `client_name`: the name supplied when the ticket is issued.
- `service_type`: one of the three exact supported service identifiers.
- `issued_at`: the ticket's arrival/issuance timestamp.

The ticket number and issuance timestamp are assigned when a ticket is successfully issued. Ticket numbers begin at `1` and increase sequentially.

### BranchQueue

A `BranchQueue` class owns and coordinates the queue state. It must maintain:

- One internal queue for each supported service type.
- One branch-wide ticket counter shared by all service queues.

The service queues must remain independent: removing a ticket from one queue cannot disturb or reorder another queue.

## Required Core Operations

The public behavior must include all five operations below. Exact return types should follow the assignment's contracts and remain easy for tests and the CLI to consume.

### `issue_ticket(client_name, service_type)`

- Validate that `service_type` is supported.
- Create a ticket with the next global number and a current issuance timestamp.
- Add the ticket to the queue matching its service type.
- Return the newly issued ticket.
- Invalid service types must be rejected with a clear, meaningful message rather than silently creating another queue.
- A rejected ticket request must not consume a ticket number or mutate queue state.

### `call_next(service_type)`

- Select the client who has waited longest in the specified service queue.
- Remove and return that ticket.
- Never return a ticket from another service.
- If the specified service queue is empty, signal the condition meaningfully and allow the CLI to continue instead of terminating unexpectedly.
- Invalid service types must also be handled deliberately rather than causing an unhelpful low-level failure.

### `peek_next(service_type)`

- Return the next ticket in the specified service queue without removing it.
- Preserve all queue state and ordering.
- If the queue is empty, signal the condition meaningfully and allow the application to continue.
- Invalid service types must be handled clearly.

### `list_waiting()`

- Return a dictionary keyed by service type.
- Each value is the ordered collection of tickets currently waiting for that service.
- Tickets within each service must appear in the exact order in which they will be called.
- The result must cover all supported service types, including services with no waiting tickets, so consumers can present a stable grouped view.
- Reading the waiting list must not mutate queue state.

### `stats()`

- Return a dictionary containing the current waiting count for each supported service type.
- Include a `total` key equal to the sum of all service counts.
- Counts reflect clients still waiting, not all tickets ever issued.
- Reading statistics must not mutate queue state.

## Queue Semantics and Invariants

The implementation plan must preserve these invariants:

1. **Global ticket numbering:** Ticket numbers are unique and sequential across the entire branch, not per service. If ticket 1 is a deposit and ticket 2 is a withdrawal, the next ticket is 3 regardless of service.
2. **Per-service FIFO:** Within one service queue, clients are called in strict arrival/issuance order: first in, first out.
3. **Service isolation:** An operation targeting one service never dequeues, reorders, or otherwise mutates tickets in another service.
4. **Direct next-client access:** Calling the next client for a service must not require scanning a combined list of clients from all services. The assignment expects a separate queue per service type; Python's `collections.deque` is the intended standard-library structure.
5. **Peek is non-destructive:** Repeated peeks return the same next ticket until a call or another relevant mutation occurs.
6. **Read operations are non-destructive:** Listing and statistics do not change queues or the ticket counter.
7. **Failed operations are safe:** Invalid service input and empty-queue operations do not corrupt state or crash the interactive program.
8. **Successful dequeue happens once:** A called ticket is removed before it can be returned by a later call.

## CLI Expectations

The CLI is a simple terminal loop, with `branch_queue.py` as the assignment's required entry point. It must remain usable until the operator explicitly exits.

The interface should:

- Present understandable menu choices.
- Prompt for the client name and service type when issuing a ticket.
- Prompt for a service type when calling the next client.
- Display issued and called ticket information clearly enough for an operator to identify the ticket and client.
- Display waiting clients grouped under their service type and in service-specific FIFO order.
- Display per-service counts and the overall total.
- Reject invalid menu choices, invalid service types, and empty-queue requests with clear feedback.
- Return to the menu after recoverable invalid input rather than crashing.
- Exit cleanly on the exit option.

No graphical interface, web interface, API, database, or kiosk integration is part of this iteration.

## Error and Edge-Case Context

The implementation plan and tests should explicitly address realistic edge cases, especially:

- Calling next on an empty but valid service queue.
- Peeking at an empty but valid service queue.
- Supplying an unsupported service type during ticket issuance.
- Supplying an unsupported service type to other service-specific operations.
- Entering an invalid CLI menu selection.
- Mixing tickets across services while retaining one global number sequence.
- Issuing multiple tickets for the same service and confirming strict FIFO behavior.
- Peeking without changing the subsequent call result.
- Calling the only remaining client in a queue and leaving that queue empty.
- Listing or calculating statistics when all queues are empty.
- Listing or calculating statistics when only some queues contain clients.

The assignment explicitly requires clear handling of invalid service types and empty queues. Requirements for blank client names, whitespace normalization, case-insensitive service input, aliases, or exact error classes/messages are not specified. The planning agent may propose a consistent policy, but should identify it as an implementation decision rather than an assignment fact.

## Concurrency Design Consideration

The runtime is only required to be a simple local CLI, and production-grade concurrency is not required. However, the assignment requires a design explanation for the scenario where two agents serving the same service call `call_next` at the same moment.

The critical state transition is removal of the next ticket from the service queue. That removal must be treated as the first exclusive/atomic mutation associated with claiming a client; only the caller that successfully removes the ticket may receive it. Reading the front ticket and removing it later as separate unprotected steps could allow two callers to announce the same client.

The final project must document this reasoning in code comments or a `DESIGN.md`. Whether to implement explicit synchronization is not mandated for the single-process CLI, but the mutation-order requirement must be understood and explained.

## Technical Constraints

- Language: Python.
- Required application entry point: `branch_queue.py`.
- Dependencies: Python standard library only.
- Relevant permitted modules named by the assignment: `collections.deque` and `datetime`.
- External packages must not be introduced.
- The repository begins with no starter code; structure, tests, and documentation will be created from scratch by the implementation agent.
- The code should be organized around classes with clear responsibilities.
- Queue operations should be separable from terminal input/output so the domain behavior can be tested directly.
- No minimum Python version is specified in the assignment; the planning agent should choose and document a reasonable supported version without relying on third-party packages.

## Required Design Documentation

The completed project must include design notes, either as comments or in `DESIGN.md`, that explain:

1. Why separate service queues make `call_next` more efficient than searching one shared ordered list. The essential distinction is direct FIFO removal from the correct service queue versus a search whose work grows with unrelated waiting clients.
2. What can go wrong if two agents for the same service call simultaneously, and why the ticket must be removed/claimed atomically before it is reported to a caller.

## Explicitly Out of Scope

The assignment states that the following are not required and will not be evaluated:

- Persistence between program runs.
- A database or file-based storage layer.
- Authentication or authorization.
- Agent identities, schedules, availability tracking, or agent assignment management.

The following are also outside the described deliverable:

- Touchscreen kiosk integration.
- Web, mobile, or graphical interfaces.
- Network APIs or distributed services.
- Customer notifications.
- Priority/VIP queues or reprioritization.
- Ticket cancellation, transfer, or editing.
- Estimated wait-time calculation.
- Historical reporting for clients already served.
- Multiple branch support.
- Localization requirements.
- Production deployment or infrastructure.

These capabilities should not be added unless the project owner explicitly expands the scope.

## Acceptance and Evaluation Context

The implementation will be considered aligned with the assignment when all of the following are demonstrably true:

- `BranchQueue` maintains a distinct internal queue for every supported service type.
- Ticket numbering is globally sequential across service types.
- FIFO order is strictly maintained within each service queue.
- `issue_ticket`, `call_next`, `peek_next`, `list_waiting`, and `stats` all behave according to their contracts.
- Invalid service types are rejected clearly.
- Calling or peeking an empty queue does not crash the application.
- The CLI menu supports ticket issuance, calling next, grouped waiting-list display, statistics, and clean exit.
- Invalid CLI input is recoverable and does not terminate the program unexpectedly.
- Classes have clear, focused responsibilities.
- The design notes justify the per-service queue structure.
- The design notes address simultaneous calls and correct mutation order.
- Only the Python standard library is used.

## Validation Expectations for the Future Implementation

No test framework is mandated. Because external packages are prohibited, validation should use standard-library facilities such as `unittest` if automated tests are added.

The implementation plan should include focused validation of:

- Ticket fields and timestamp creation.
- Cross-service global numbering.
- Same-service FIFO ordering.
- Service isolation.
- Correct dequeue and non-destructive peek behavior.
- Correct grouped waiting-list results.
- Correct per-service and total statistics before and after calls.
- Empty-queue behavior.
- Invalid-service behavior and absence of unintended state mutation.
- A CLI smoke test or equivalent verification of the menu loop and error recovery.

Automated tests should target the public behavior of the queue model rather than private storage details, while still demonstrating the required observable per-service behavior.

## Planning Handoff Notes

The next agent should use this context to produce a detailed implementation plan, not assume that implementation already exists. Before planning, that agent should inspect the repository again in case files were added after this document was written.

The plan should resolve—but not silently invent—unspecified details such as exact exception types, client-name validation, CLI parsing/normalization, display formatting, test-file organization, and the documented Python version. Any decision in these areas must preserve the explicit assignment behavior and avoid expanding the project beyond a small standard-library CLI.

