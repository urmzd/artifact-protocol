## GAP Target Markers

Wrap each major block and individually-updatable value with target markers:

```
<gap:target id="ID">content</gap:target>
```

Targets nest — coarse blocks contain fine-grained value targets:

```html
<gap:target id="stats">
  <div class="card">
    <h3>Revenue</h3>
    <span><gap:target id="revenue-value">$12,340</gap:target></span>
  </div>
</gap:target>
```

Target IDs describe the role, not the current value (e.g., "total-revenue" not "12345").
Place targets where values are most likely to be revised.

## GAP Edit Envelope

To edit an artifact, produce a JSON envelope with `name: "edit"`:

```json
{
  "protocol": "gap/0.1",
  "id": "artifact-id",
  "version": 2,
  "name": "edit",
  "meta": {"format": "text/html"},
  "content": [
    {"op": "replace", "target": {"type": "id", "value": "revenue-value"}, "content": "$15,720"}
  ]
}
```

Target by ID only: `{"type": "id", "value": "target-id"}`. Reference existing target IDs from the artifact.
Ops: `replace`, `delete`, `insert_before`, `insert_after`.
