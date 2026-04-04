# ADR-003: Use Event Sourcing for Order Processing

Status: Accepted
Date: 2023-10-27
Deciders: Architecture Guild, Engineering Lead, Product Owner

## Context
The current CRUD-based Order Processing system suffers from significant data integrity issues. Specifically, when orders undergo complex status transitions (e.g., pending, paid, shipped, cancelled), the system only persists the final state. This leads to:
1. Loss of context: We cannot determine why an order reached its current state.
2. Race conditions: Concurrent updates to order status often lead to inconsistent database states or overwritten changes.
3. Compliance/Audit requirements: Business stakeholders require a granular, immutable history of all actions performed on an order for financial reconciliation.

## Decision
We will adopt an Event Sourcing pattern for all order-related operations.
- Event Store: An append-only log will serve as the source of truth for all Order domain events.
- Command Handlers: All state changes will be initiated via commands which are validated against current state and then committed as events.
- Projections: We will implement asynchronous read-model projections to populate relational database views for UI queries and reporting, adhering to the CQRS pattern.

## Alternatives Considered

### 1. Versioned State Machine (Optimistic Locking)
- Pros: Easier to implement than Event Sourcing; keeps standard relational schema.
- Cons: Still loses transition history; high risk of contention under load; complex handling of "undo" or retrospective status changes.

### 2. Transactional Outbox Pattern with CRUD
- Pros: Guarantees consistency between database updates and downstream messaging; lower architectural complexity.
- Cons: Does not solve the fundamental loss of historical context; audit trails must be implemented separately (e.g., database triggers or audit tables), which are often error-prone and incomplete.

## Consequences

### Positive
- Full Audit Trail: Every business decision is captured as a distinct event, providing a perfect history.
- Temporal Queries: Ability to reconstruct the state of an order at any point in time.
- Replayability: System state can be rebuilt or migrated by replaying event logs; facilitates debugging of production issues.
- Scalability: Decouples write operations from read operations, allowing for optimized read models.

### Negative
- Complexity: Higher initial development overhead and mental shift for the engineering team.
- Learning Curve: Team must learn new patterns, including handling schema evolution (event versioning) and managing event streams.
- Eventual Consistency: Read models will be eventually consistent, necessitating changes to UI/UX patterns (e.g., optimistic updates or polling).