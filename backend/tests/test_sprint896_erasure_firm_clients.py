"""Sprint 896 (council 2026-11-25, C-01/C-02/C-03): account erasure and firm-owned clients.

Sprint 853 made a firm client the firm's, whoever created it. Erasure still
scoped by ``clients.user_id``, so a plain member deleting their account deleted
firm clients they had created, with the firm's engagements under them.
"""

from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy import func, select

from database import Base
from organization_model import Organization, OrganizationMember, OrgRole
from services.account_erasure import ErasureBlocked, check_erasable, erase_account


def _count(db, table: str, **where: Any) -> int:
    t = Base.metadata.tables[table]
    q = select(func.count()).select_from(t)
    for col, val in where.items():
        q = q.where(t.c[col] == val)
    return int(db.execute(q).scalar() or 0)


@pytest.fixture
def firm(db_session, make_user):
    owner = make_user(email="owner896@example.com")
    member = make_user(email="member896@example.com")
    org = Organization(name="Firm 896", slug="firm-896", owner_user_id=owner.id)
    db_session.add(org)
    db_session.flush()
    db_session.add(OrganizationMember(organization_id=org.id, user_id=owner.id, role=OrgRole.OWNER))
    db_session.add(OrganizationMember(organization_id=org.id, user_id=member.id, role=OrgRole.MEMBER))
    owner.organization_id = org.id
    member.organization_id = org.id
    db_session.flush()
    return {"org": org, "owner": owner, "member": member}


def test_member_erasure_keeps_the_firm_client_and_the_owners_work(db_session, firm, make_client, make_engagement):
    firm_client = make_client(user=firm["member"], name="Firm Client")
    firm_client.organization_id = firm["org"].id
    personal = make_client(user=firm["member"], name="Personal Client")  # organization_id NULL
    owners_engagement = make_engagement(client=firm_client)
    owners_engagement.created_by = firm["owner"].id  # the factory uses the client's creator
    db_session.commit()
    client_id, engagement_id, owner_id, member_id = (
        firm_client.id,
        owners_engagement.id,
        firm["owner"].id,
        firm["member"].id,
    )
    personal_id = personal.id

    check_erasable(db_session, firm["member"])
    erase_account(db_session, firm["member"])

    assert _count(db_session, "clients", id=client_id) == 1
    assert _count(db_session, "engagements", id=engagement_id) == 1
    assert _count(db_session, "clients", id=client_id, user_id=owner_id) == 1  # "created by" passes to the owner
    assert _count(db_session, "clients", id=personal_id) == 0
    assert _count(db_session, "users", id=member_id) == 0


def test_member_with_own_engagement_on_a_firm_client_is_refused_not_wiped(
    db_session, firm, make_client, make_engagement
):
    firm_client = make_client(user=firm["member"], name="Firm Client")
    firm_client.organization_id = firm["org"].id
    make_engagement(client=firm_client, user=firm["member"])
    db_session.commit()

    with pytest.raises(ErasureBlocked) as exc:
        check_erasable(db_session, firm["member"])
    assert exc.value.code == "ERASURE_FOREIGN_ENGAGEMENTS"


def test_sole_owner_erasure_removes_clients_a_removed_member_created(db_session, firm, make_client):
    """C-02: the firm's RESTRICT key used to fail the owner's erasure after Stripe was cancelled."""
    left_behind = make_client(user=firm["member"], name="Left Behind")
    left_behind.organization_id = firm["org"].id
    db_session.query(OrganizationMember).filter(OrganizationMember.user_id == firm["member"].id).delete()
    firm["member"].organization_id = None
    db_session.commit()
    org_id, client_id, member_id = firm["org"].id, left_behind.id, firm["member"].id

    check_erasable(db_session, firm["owner"])
    erase_account(db_session, firm["owner"])

    assert _count(db_session, "organizations", id=org_id) == 0
    assert _count(db_session, "clients", id=client_id) == 0
    assert _count(db_session, "users", id=member_id) == 1


def test_actual_captured_by_is_cleared_c03(db_session, firm, make_client, make_engagement):
    from analytical_expectations_model import AnalyticalExpectation

    firm_client = make_client(user=firm["owner"], name="Owner Client")
    firm_client.organization_id = firm["org"].id
    engagement = make_engagement(client=firm_client, user=firm["owner"])
    db_session.flush()
    columns = {c.name for c in AnalyticalExpectation.__table__.columns}
    assert "actual_captured_by" in columns
    from services.account_erasure import _NULLABLE_USER_REFS

    assert ("analytical_expectations", "actual_captured_by") in _NULLABLE_USER_REFS
    del engagement


def test_every_user_foreign_key_is_handled_by_erasure():
    """Guard for the class (C-03): a new column pointing at users.id must be listed, or erasure 500s."""
    import inspect

    import services.account_erasure as mod
    from model_registry import import_all_models

    import_all_models()
    source = inspect.getsource(mod)
    listed = set(mod._NULLABLE_USER_REFS)
    # Only superadmins write this, and check_erasable refuses superadmins.
    exempt = {("admin_audit_logs", "admin_user_id")}
    missing = []
    for table in Base.metadata.sorted_tables:
        for column in table.columns:
            for fk in column.foreign_keys:
                if fk.column.table.name != "users" or table.name == "users":
                    continue
                if fk.ondelete and fk.ondelete.upper() in ("CASCADE", "SET NULL"):
                    continue
                if (table.name, column.name) in listed | exempt:
                    continue
                # Deleted by user_id, or handled explicitly by name in the module.
                if f'"{table.name}"' in source:
                    continue
                missing.append(f"{table.name}.{column.name}")
    assert not missing, f"columns referencing users.id that erasure does not clear or delete: {missing}"


def test_export_still_includes_the_members_work_on_firm_clients(db_session, firm, make_client, make_engagement):
    """PR #338 review: erasure keeps firm clients, but the member's data download must still include their work."""
    from services.account_erasure import export_account

    firm_client = make_client(user=firm["member"], name="Firm Client")
    firm_client.organization_id = firm["org"].id
    engagement = make_engagement(client=firm_client)
    db_session.commit()

    data = export_account(db_session, firm["member"])
    text = repr(data)
    assert "Firm Client" in text
    assert str(engagement.id) in text
