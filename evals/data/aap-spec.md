## AAP Target Markers

Wrap each major block and individually-updatable value with target markers:

```
<aap:target id="ID">content</aap:target>
```

Targets nest — coarse blocks contain fine-grained value targets:

```html
<aap:target id="stats">
  <div class="card">
    <h3>Revenue</h3>
    <span><aap:target id="revenue-value">$12,340</aap:target></span>
  </div>
</aap:target>
```

Target IDs describe the role, not the current value (e.g., "total-revenue" not "12345").

## AAP Diff Envelope

To edit an artifact, produce a JSON envelope with `name: "diff"`:

```json
{
  "protocol": "aap/0.1",
  "id": "artifact-id",
  "version": 2,
  "name": "diff",
  "operation": {"direction": "output", "format": "text/html"},
  "content": [
    {"op": "replace", "target": {"type": "id", "value": "revenue-value"}, "content": "$15,720"}
  ]
}
```

Target by ID only: `{"type": "id", "value": "target-id"}`. Reference existing target IDs from the artifact.
Ops: `replace`, `delete`, `insert_before`, `insert_after`.
