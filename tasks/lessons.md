# Lessons Learned

> **Protocol:** After ANY correction from the CEO or discovery of a better pattern, document it here. Review at session start.

---

## Template

When adding a lesson, use this format:

```
### [DATE] — [Short Title]
**Trigger:** What happened that led to this lesson?
**Pattern:** What's the rule or principle to follow?
**Example:** Concrete example of the right way to do it.
```

---

## Lessons

### 2026-02-01 — Audit Infrastructure First
**Trigger:** Project audit scored 2.9/5 due to missing workflow artifacts (todo.md, lessons.md, git history).
**Pattern:** Before diving into features, establish the tracking infrastructure. Good code without documentation is hard to maintain.
**Example:** Day 7 directive prioritized workflow setup over new features.

---

### 2026-02-01 — datetime.utcnow() is Deprecated
**Trigger:** Running pytest revealed 212 deprecation warnings about `datetime.utcnow()` in security_utils.py and audit_engine.py.
**Pattern:** Python 3.12+ deprecates `datetime.datetime.utcnow()`. Use timezone-aware objects instead: `datetime.datetime.now(datetime.UTC)`.
**Example:**
```python
# OLD (deprecated)
from datetime import datetime
timestamp = datetime.utcnow().isoformat()

# NEW (correct)
from datetime import datetime, UTC
timestamp = datetime.now(UTC).isoformat()
```
**Action:** Schedule fix for Day 9 or as technical debt cleanup.

---

### 2026-02-01 — Test Fixtures Make Tests Readable
**Trigger:** Writing test_audit_engine.py required generating various CSV test data repeatedly.
**Pattern:** Use pytest fixtures to create reusable test data. Name fixtures descriptively (e.g., `small_balanced_csv`, `abnormal_balances_csv`).
**Example:**
```python
@pytest.fixture
def small_balanced_csv() -> bytes:
    """Generate a small balanced CSV (10 rows)."""
    data = """Account Name,Debit,Credit
Cash,10000,
Revenue,,10000
"""
    return data.encode('utf-8')
```

---

*Add new lessons below this line. Newest at bottom.*
