Create an Architecture Decision Record (ADR-003): "Use Event Sourcing for Order Processing".

Include:
- Title, Status (Accepted), Date, Deciders
- Context: current problems with CRUD-based order state, consistency issues, audit trail needs
- Decision: adopt event sourcing with event store, command handlers, read model projections
- Alternatives Considered: 2 other approaches with pros/cons
- Consequences: positive (audit trail, replay, temporal queries) and negative (complexity, learning curve, eventual consistency)

Use section IDs: context, decision, consequences

Use AAP section markers to delineate each major content block.
Wrap each logical section with `<aap:section id="ID">` and `</aap:section>`.


Output raw code only. No markdown fences, no explanation.