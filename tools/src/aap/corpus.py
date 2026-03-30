"""
HTML corpus generator for benchmarking — builds a large self-contained dashboard.
"""
import random
import string

CHUNK_SIZE = 30  # chars per flush

# ── fake data generators ──────────────────────────────────────────────────────

FIRST = [
    "Alice", "Bob", "Carol", "Dave", "Eve", "Frank", "Grace", "Hank", "Iris", "Jack",
    "Karen", "Leo", "Mia", "Ned", "Olivia", "Paul", "Quinn", "Rita", "Sam", "Tina",
    "Uma", "Victor", "Wendy", "Xander", "Yara", "Zoe", "Aaron", "Beth", "Caleb", "Diana",
]
LAST = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
    "Wilson", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin",
    "Thompson", "Moore", "Young", "Allen", "King", "Wright", "Scott", "Hill", "Green",
]
ROLES = ["Admin", "Editor", "Viewer", "Manager", "Developer", "Support"]
STATUSES = ["Active", "Inactive", "Pending", "Suspended"]
PRODUCTS = [
    "Widget Pro", "Gadget Plus", "Doohickey Max", "Thingamajig Lite",
    "Whatsit Premium", "Gizmo Basic", "Contraption Ultra", "Doodad Standard",
]
ORDER_ST = ["Shipped", "Processing", "Delivered", "Cancelled", "Refunded"]


def rname():
    return f"{random.choice(FIRST)} {random.choice(LAST)}"


def remail(name):
    return f"{name.lower().replace(' ', '.')}{random.randint(1, 99)}@example.com"


def rdate(y0=2020, y1=2025):
    y = random.randint(y0, y1)
    m = random.randint(1, 12)
    d = random.randint(1, 28)
    return f"{y}-{m:02d}-{d:02d}"


def rid():
    return "ORD-" + "".join(random.choices(string.digits, k=6))


# ── HTML builder ─────────────────────────────────────────────────────────────


def build_html():
    random.seed(42)

    user_rows = []
    for i in range(150):
        name = rname()
        email = remail(name)
        role = random.choice(ROLES)
        status = random.choice(STATUSES)
        joined = rdate()
        color = {
            "Active": "#22c55e",
            "Inactive": "#94a3b8",
            "Pending": "#f59e0b",
            "Suspended": "#ef4444",
        }[status]
        user_rows.append(
            f'<tr><td>{i+1}</td><td>{name}</td><td>{email}</td>'
            f'<td>{role}</td>'
            f'<td><span style="background:{color};color:#fff;padding:2px 8px;'
            f'border-radius:12px;font-size:12px">{status}</span></td>'
            f'<td>{joined}</td></tr>'
        )

    order_rows = []
    for i in range(100):
        oid = rid()
        prod = random.choice(PRODUCTS)
        amt = f"${random.uniform(9.99, 999.99):.2f}"
        date = rdate(2024, 2025)
        status = random.choice(ORDER_ST)
        color = {
            "Shipped": "#3b82f6",
            "Processing": "#f59e0b",
            "Delivered": "#22c55e",
            "Cancelled": "#ef4444",
            "Refunded": "#8b5cf6",
        }[status]
        order_rows.append(
            f'<tr><td>{oid}</td><td>{prod}</td><td>{amt}</td><td>{date}</td>'
            f'<td><span style="background:{color};color:#fff;padding:2px 8px;'
            f'border-radius:12px;font-size:12px">{status}</span></td></tr>'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Dashboard — AcmeCorp</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
     background:#f1f5f9;color:#1e293b;display:flex;flex-direction:column;min-height:100vh}}
nav{{background:#1e293b;color:#f8fafc;display:flex;align-items:center;
     justify-content:space-between;padding:0 24px;height:56px;position:sticky;top:0;z-index:100}}
.nav-brand{{font-weight:700;font-size:18px;letter-spacing:-0.5px}}
.nav-right{{display:flex;align-items:center;gap:16px}}
.avatar{{width:32px;height:32px;border-radius:50%;background:#3b82f6;
         display:flex;align-items:center;justify-content:center;
         font-weight:600;font-size:13px;color:#fff}}
.btn-signout{{background:transparent;border:1px solid #475569;color:#cbd5e1;
              padding:6px 14px;border-radius:6px;cursor:pointer;font-size:13px}}
.btn-signout:hover{{background:#334155}}
.layout{{display:flex;flex:1}}
aside{{width:220px;background:#fff;border-right:1px solid #e2e8f0;
       padding:24px 0;flex-shrink:0;position:sticky;top:56px;
       height:calc(100vh - 56px);overflow-y:auto}}
.sidebar-section{{padding:8px 16px;font-size:11px;font-weight:600;
                  text-transform:uppercase;letter-spacing:0.8px;color:#94a3b8;margin-top:16px}}
.sidebar-link{{display:flex;align-items:center;gap:10px;padding:9px 20px;
               font-size:14px;color:#475569;cursor:pointer;text-decoration:none}}
.sidebar-link:hover{{background:#f8fafc;color:#1e293b}}
.sidebar-link.active{{background:#eff6ff;color:#2563eb;font-weight:500;
                      border-right:2px solid #2563eb}}
main{{flex:1;padding:32px;overflow-x:auto}}
.page-title{{font-size:24px;font-weight:700;margin-bottom:4px}}
.page-sub{{color:#64748b;font-size:14px;margin-bottom:28px}}
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:20px;margin-bottom:32px}}
.card{{background:#fff;border-radius:10px;padding:20px 24px;
       box-shadow:0 1px 3px rgba(0,0,0,.07)}}
.card-label{{font-size:13px;color:#64748b;font-weight:500;margin-bottom:6px}}
.card-value{{font-size:28px;font-weight:700;line-height:1}}
.card-delta{{font-size:12px;margin-top:6px}}
.card-delta.up{{color:#22c55e}}.card-delta.down{{color:#ef4444}}
.section{{background:#fff;border-radius:10px;box-shadow:0 1px 3px rgba(0,0,0,.07);
          margin-bottom:32px;overflow:hidden}}
.section-header{{padding:18px 24px;border-bottom:1px solid #f1f5f9;
                 display:flex;align-items:center;justify-content:space-between}}
.section-title{{font-size:16px;font-weight:600}}
.section-count{{font-size:12px;color:#94a3b8;background:#f8fafc;
                padding:3px 10px;border-radius:20px}}
.table-wrap{{overflow-x:auto}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{text-align:left;padding:10px 16px;background:#f8fafc;font-weight:600;
    color:#475569;font-size:12px;text-transform:uppercase;letter-spacing:0.5px;
    border-bottom:1px solid #e2e8f0}}
td{{padding:11px 16px;border-bottom:1px solid #f1f5f9;vertical-align:middle}}
tr:last-child td{{border-bottom:none}}
tr:hover td{{background:#f8fafc}}
.form-grid{{padding:24px;display:grid;grid-template-columns:1fr 1fr;gap:20px}}
.field{{display:flex;flex-direction:column;gap:6px}}
.field.full{{grid-column:1/-1}}
label{{font-size:12px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:0.5px}}
input[type=text],input[type=email],input[type=password],select,textarea{{
  border:1px solid #e2e8f0;border-radius:7px;padding:9px 13px;font-size:14px;
  color:#1e293b;outline:none;width:100%;background:#fff}}
input:focus,select:focus,textarea:focus{{border-color:#3b82f6;
  box-shadow:0 0 0 3px rgba(59,130,246,.1)}}
textarea{{resize:vertical;min-height:90px}}
.toggle-row{{display:flex;align-items:center;justify-content:space-between;
             padding:14px 24px;border-bottom:1px solid #f1f5f9}}
.toggle-label{{font-size:14px;font-weight:500}}
.toggle-desc{{font-size:12px;color:#94a3b8;margin-top:2px}}
.toggle{{position:relative;width:44px;height:24px}}
.toggle input{{opacity:0;width:0;height:0}}
.slider{{position:absolute;inset:0;background:#cbd5e1;border-radius:24px;cursor:pointer;transition:.2s}}
.slider:before{{content:"";position:absolute;width:18px;height:18px;
                left:3px;bottom:3px;background:#fff;border-radius:50%;transition:.2s}}
input:checked+.slider{{background:#3b82f6}}
input:checked+.slider:before{{transform:translateX(20px)}}
.form-actions{{padding:16px 24px;border-top:1px solid #f1f5f9;display:flex;gap:12px}}
.btn-primary{{background:#2563eb;color:#fff;border:none;padding:9px 20px;
              border-radius:7px;font-size:14px;font-weight:500;cursor:pointer}}
.btn-primary:hover{{background:#1d4ed8}}
.btn-secondary{{background:#fff;color:#475569;border:1px solid #e2e8f0;
                padding:9px 20px;border-radius:7px;font-size:14px;cursor:pointer}}
.danger-zone{{margin:24px;border:1px solid #fecaca;border-radius:8px;padding:20px}}
.danger-title{{font-size:14px;font-weight:600;color:#dc2626;margin-bottom:8px}}
.danger-desc{{font-size:13px;color:#64748b;margin-bottom:14px}}
.btn-danger{{background:#dc2626;color:#fff;border:none;padding:9px 20px;
             border-radius:7px;font-size:14px;cursor:pointer}}
</style>
</head>
<body>
<nav>
  <span class="nav-brand">&#9679; AcmeCorp</span>
  <div class="nav-right">
    <span style="font-size:13px;color:#cbd5e1">Welcome, Jane Doe</span>
    <div class="avatar">JD</div>
    <button class="btn-signout" onclick="alert('Signed out')">Sign out</button>
  </div>
</nav>
<div class="layout">
  <aside>
    <div class="sidebar-section">Main</div>
    <a class="sidebar-link active" href="#">Dashboard</a>
    <a class="sidebar-link" href="#">Analytics</a>
    <a class="sidebar-link" href="#">Reports</a>
    <div class="sidebar-section">Management</div>
    <a class="sidebar-link" href="#">Users</a>
    <a class="sidebar-link" href="#">Orders</a>
    <a class="sidebar-link" href="#">Products</a>
    <a class="sidebar-link" href="#">Invoices</a>
    <div class="sidebar-section">System</div>
    <a class="sidebar-link" href="#">Settings</a>
    <a class="sidebar-link" href="#">Audit Log</a>
    <a class="sidebar-link" href="#">API Keys</a>
    <a class="sidebar-link" href="#">Billing</a>
    <a class="sidebar-link" href="#">Support</a>
  </aside>
  <main>
    <div class="page-title">Dashboard</div>
    <div class="page-sub">Overview</div>
    <div class="stats">
      <div class="card"><div class="card-label">Total Users</div>
        <div class="card-value">24,891</div>
        <div class="card-delta up">&#9650; 4.2% vs last month</div></div>
      <div class="card"><div class="card-label">Revenue (MTD)</div>
        <div class="card-value">$182,430</div>
        <div class="card-delta up">&#9650; 11.7% vs last month</div></div>
      <div class="card"><div class="card-label">Orders (MTD)</div>
        <div class="card-value">3,047</div>
        <div class="card-delta down">&#9660; 2.1% vs last month</div></div>
      <div class="card"><div class="card-label">Uptime</div>
        <div class="card-value">99.97%</div>
        <div class="card-delta up">SLA: 99.9%</div></div>
    </div>
    <div class="section">
      <div class="section-header">
        <span class="section-title">Users</span>
        <span class="section-count">150 records</span>
      </div>
      <div class="table-wrap"><table>
        <thead><tr><th>#</th><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th>Joined</th></tr></thead>
        <tbody>{''.join(user_rows)}</tbody>
      </table></div>
    </div>
    <div class="section">
      <div class="section-header">
        <span class="section-title">Recent Orders</span>
        <span class="section-count">100 records</span>
      </div>
      <div class="table-wrap"><table>
        <thead><tr><th>Order ID</th><th>Product</th><th>Amount</th><th>Date</th><th>Status</th></tr></thead>
        <tbody>{''.join(order_rows)}</tbody>
      </table></div>
    </div>
    <div class="section">
      <div class="section-header"><span class="section-title">Account Settings</span></div>
      <form onsubmit="return false">
        <div class="form-grid">
          <div class="field"><label>First name</label><input type="text" value="Jane"></div>
          <div class="field"><label>Last name</label><input type="text" value="Doe"></div>
          <div class="field"><label>Email</label><input type="email" value="jane.doe@acmecorp.com"></div>
          <div class="field"><label>Phone</label><input type="text" value="+1 (555) 000-1234"></div>
          <div class="field"><label>Role</label>
            <select><option>Admin</option><option>Editor</option><option>Viewer</option></select></div>
          <div class="field"><label>Time zone</label>
            <select><option>UTC-05:00 Eastern</option><option>UTC-08:00 Pacific</option></select></div>
          <div class="field full"><label>Bio</label>
            <textarea>Platform admin at AcmeCorp.</textarea></div>
          <div class="field"><label>New password</label><input type="password"></div>
          <div class="field"><label>Confirm password</label><input type="password"></div>
        </div>
        <div class="toggle-row">
          <div><div class="toggle-label">Email notifications</div>
            <div class="toggle-desc">Receive updates and alerts via email</div></div>
          <label class="toggle"><input type="checkbox" checked><span class="slider"></span></label>
        </div>
        <div class="toggle-row">
          <div><div class="toggle-label">Security alerts</div>
            <div class="toggle-desc">Sign-ins from new devices or locations</div></div>
          <label class="toggle"><input type="checkbox" checked><span class="slider"></span></label>
        </div>
        <div class="toggle-row">
          <div><div class="toggle-label">Weekly digest</div>
            <div class="toggle-desc">Summary of activity sent every Monday</div></div>
          <label class="toggle"><input type="checkbox"><span class="slider"></span></label>
        </div>
        <div class="form-actions">
          <button class="btn-primary" type="submit">Save changes</button>
          <button class="btn-secondary" type="button">Discard</button>
        </div>
      </form>
      <div class="danger-zone">
        <div class="danger-title">Danger Zone</div>
        <div class="danger-desc">Permanently delete your account. This cannot be undone.</div>
        <button class="btn-danger" onclick="confirm('Delete your account?')">Delete account</button>
      </div>
    </div>
  </main>
</div>
</body>
</html>"""
