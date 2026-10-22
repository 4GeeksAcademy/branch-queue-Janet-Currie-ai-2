# Design notes

## Separate queue per service

Each service has its own `collections.deque`. `call_next("deposit")` removes the oldest deposit ticket with `popleft` on that deque. The number of clients waiting for withdrawals or account management does not change how much work that call does.

A single list of every waiting client would have to be scanned on each call to find the oldest ticket for the agent's service. That scan grows as unrelated clients fill the branch. Separate queues keep the next client for a service at the front of that service's line.

## Simultaneous call_next

The dangerous moment is two agents for the same service both taking the next client. If each agent reads the front ticket and only afterward removes it, both reads can see the same client, and both agents can announce that client.

The ticket has to be removed first. Only the caller whose removal succeeds receives that ticket. A later caller then sees whoever is now at the front, or finds the queue empty.

This program is a single-threaded menu, so it does not take locks. `call_next` still claims the client with `popleft` rather than reading the front and removing it later. A threaded version would perform that removal inside a lock for the service queue, or an equivalent single removal, so only one caller can receive each ticket.
