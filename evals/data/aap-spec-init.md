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
Place targets where values are most likely to be revised.

IMPORTANT: You MUST wrap every major section and individually-updatable value in your output with `<aap:target id="ID">…</aap:target>` markers. Use descriptive, role-based IDs (e.g., "nav", "stats-card", "total-revenue"). Nest targets: coarse section targets should contain fine-grained value targets. Place markers on ALL values that are likely to be revised later. The markers are essential for efficient future edits.
