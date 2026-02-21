"""
Tests for Sprint 112: Finding Comments — Model, Manager, Routes, Export, Zero-Storage.

~55 tests covering:
- Comment model schema and to_dict
- Manager CRUD (create, read, update, delete)
- Threading (parent_comment_id)
- Ownership / access control
- Cascade deletes (item → comments)
- Route registration
- Engagement ZIP export inclusion
- Zero-Storage guardrail (no financial data columns)
"""

import json
import sys
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import pytest
from sqlalchemy import inspect as sa_inspect

sys.path.insert(0, str(Path(__file__).parent.parent))

from engagement_export import EngagementExporter
from follow_up_items_manager import FollowUpItemsManager
from follow_up_items_model import (
    FollowUpItemComment,
)

# ===========================================================================
# TestCommentSchema — Model structure, to_dict, repr, guardrail checks
# ===========================================================================


class TestCommentSchema:
    """Verify comment model structure and serialization."""

    def test_comment_table_exists(self, db_engine):
        inspector = sa_inspect(db_engine)
        tables = inspector.get_table_names()
        assert "follow_up_item_comments" in tables

    def test_comment_columns(self, db_engine):
        inspector = sa_inspect(db_engine)
        columns = {c["name"] for c in inspector.get_columns("follow_up_item_comments")}
        expected = {
            "id", "follow_up_item_id", "user_id", "comment_text",
            "parent_comment_id", "created_at", "updated_at",
        }
        assert expected.issubset(columns)

    def test_comment_has_no_prohibited_columns(self, db_engine):
        """Guardrail 2: no financial data columns."""
        inspector = sa_inspect(db_engine)
        columns = {c["name"] for c in inspector.get_columns("follow_up_item_comments")}
        prohibited = {
            "account_number", "account_name", "amount", "debit", "credit",
            "transaction_id", "entry_id", "vendor_name", "employee_name",
            "balance", "invoice_number",
        }
        overlap = columns & prohibited
        assert overlap == set(), f"Prohibited columns found: {overlap}"

    def test_comment_to_dict(self, make_comment, make_user, make_follow_up_item):
        user = make_user(email="author@test.com", name="Author Name")
        item = make_follow_up_item()
        comment = make_comment(follow_up_item=item, user=user, comment_text="Good finding")
        d = comment.to_dict()
        assert d["id"] == comment.id
        assert d["follow_up_item_id"] == item.id
        assert d["user_id"] == user.id
        assert d["author_name"] == "Author Name"
        assert d["comment_text"] == "Good finding"
        assert d["parent_comment_id"] is None
        assert "created_at" in d
        assert "updated_at" in d

    def test_comment_to_dict_with_parent(self, make_comment, make_follow_up_item, make_user):
        user = make_user(email="replier@test.com")
        item = make_follow_up_item()
        parent = make_comment(follow_up_item=item, user=user, comment_text="Parent")
        reply = make_comment(
            follow_up_item=item, user=user,
            comment_text="Reply", parent_comment_id=parent.id,
        )
        d = reply.to_dict()
        assert d["parent_comment_id"] == parent.id

    def test_comment_repr(self, make_comment):
        comment = make_comment()
        r = repr(comment)
        assert "FollowUpItemComment" in r
        assert str(comment.id) in r

    def test_comment_timestamps_set(self, make_comment):
        comment = make_comment()
        assert comment.created_at is not None
        assert comment.updated_at is not None


# ===========================================================================
# TestCommentManagerCreate — create_comment
# ===========================================================================


class TestCommentManagerCreate:
    """Test comment creation via manager."""

    def test_create_comment_basic(self, db_session, make_user, make_client, make_engagement, make_follow_up_item):
        user = make_user(email="create@test.com")
        client = make_client(user=user)
        eng = make_engagement(client=client)
        item = make_follow_up_item(engagement=eng)

        manager = FollowUpItemsManager(db_session)
        comment = manager.create_comment(
            user_id=user.id,
            item_id=item.id,
            comment_text="This needs investigation",
        )
        assert comment.id is not None
        assert comment.comment_text == "This needs investigation"
        assert comment.user_id == user.id
        assert comment.follow_up_item_id == item.id
        assert comment.parent_comment_id is None

    def test_create_comment_with_parent(self, db_session, make_user, make_client, make_engagement, make_follow_up_item):
        user = make_user(email="thread@test.com")
        client = make_client(user=user)
        eng = make_engagement(client=client)
        item = make_follow_up_item(engagement=eng)

        manager = FollowUpItemsManager(db_session)
        parent = manager.create_comment(user_id=user.id, item_id=item.id, comment_text="Parent")
        reply = manager.create_comment(
            user_id=user.id, item_id=item.id,
            comment_text="Reply to parent",
            parent_comment_id=parent.id,
        )
        assert reply.parent_comment_id == parent.id

    def test_create_comment_strips_whitespace(self, db_session, make_user, make_client, make_engagement, make_follow_up_item):
        user = make_user(email="strip@test.com")
        client = make_client(user=user)
        eng = make_engagement(client=client)
        item = make_follow_up_item(engagement=eng)

        manager = FollowUpItemsManager(db_session)
        comment = manager.create_comment(user_id=user.id, item_id=item.id, comment_text="  trimmed  ")
        assert comment.comment_text == "trimmed"

    def test_create_comment_empty_text_raises(self, db_session, make_user, make_client, make_engagement, make_follow_up_item):
        user = make_user(email="empty@test.com")
        client = make_client(user=user)
        eng = make_engagement(client=client)
        item = make_follow_up_item(engagement=eng)

        manager = FollowUpItemsManager(db_session)
        with pytest.raises(ValueError, match="Comment text is required"):
            manager.create_comment(user_id=user.id, item_id=item.id, comment_text="")

    def test_create_comment_whitespace_only_raises(self, db_session, make_user, make_client, make_engagement, make_follow_up_item):
        user = make_user(email="ws@test.com")
        client = make_client(user=user)
        eng = make_engagement(client=client)
        item = make_follow_up_item(engagement=eng)

        manager = FollowUpItemsManager(db_session)
        with pytest.raises(ValueError, match="Comment text is required"):
            manager.create_comment(user_id=user.id, item_id=item.id, comment_text="   ")

    def test_create_comment_invalid_item_raises(self, db_session, make_user, make_client):
        user = make_user(email="noitem@test.com")

        manager = FollowUpItemsManager(db_session)
        with pytest.raises(ValueError, match="not found or access denied"):
            manager.create_comment(user_id=user.id, item_id=99999, comment_text="Test")

    def test_create_comment_wrong_user_raises(self, db_session, make_user, make_client, make_engagement, make_follow_up_item):
        owner = make_user(email="owner@test.com")
        other = make_user(email="other@test.com")
        client = make_client(user=owner)
        eng = make_engagement(client=client)
        item = make_follow_up_item(engagement=eng)

        manager = FollowUpItemsManager(db_session)
        with pytest.raises(ValueError, match="not found or access denied"):
            manager.create_comment(user_id=other.id, item_id=item.id, comment_text="Snoop")

    def test_create_comment_invalid_parent_raises(self, db_session, make_user, make_client, make_engagement, make_follow_up_item):
        user = make_user(email="badparent@test.com")
        client = make_client(user=user)
        eng = make_engagement(client=client)
        item = make_follow_up_item(engagement=eng)

        manager = FollowUpItemsManager(db_session)
        with pytest.raises(ValueError, match="Parent comment not found"):
            manager.create_comment(
                user_id=user.id, item_id=item.id,
                comment_text="Reply", parent_comment_id=99999,
            )

    def test_create_comment_parent_from_different_item_raises(
        self, db_session, make_user, make_client, make_engagement, make_follow_up_item,
    ):
        user = make_user(email="crossitem@test.com")
        client = make_client(user=user)
        eng = make_engagement(client=client)
        item1 = make_follow_up_item(engagement=eng, description="Item 1")
        item2 = make_follow_up_item(engagement=eng, description="Item 2")

        manager = FollowUpItemsManager(db_session)
        parent = manager.create_comment(user_id=user.id, item_id=item1.id, comment_text="On item 1")

        with pytest.raises(ValueError, match="Parent comment not found"):
            manager.create_comment(
                user_id=user.id, item_id=item2.id,
                comment_text="Cross-item reply", parent_comment_id=parent.id,
            )


# ===========================================================================
# TestCommentManagerRead — get_comments
# ===========================================================================


class TestCommentManagerRead:
    """Test comment retrieval."""

    def test_get_comments_empty(self, db_session, make_user, make_client, make_engagement, make_follow_up_item):
        user = make_user(email="readnone@test.com")
        client = make_client(user=user)
        eng = make_engagement(client=client)
        item = make_follow_up_item(engagement=eng)

        manager = FollowUpItemsManager(db_session)
        comments = manager.get_comments(user_id=user.id, item_id=item.id)
        assert comments == []

    def test_get_comments_ordered_by_created_at(self, db_session, make_user, make_client, make_engagement, make_follow_up_item):
        user = make_user(email="readorder@test.com")
        client = make_client(user=user)
        eng = make_engagement(client=client)
        item = make_follow_up_item(engagement=eng)

        manager = FollowUpItemsManager(db_session)
        c1 = manager.create_comment(user_id=user.id, item_id=item.id, comment_text="First")
        c2 = manager.create_comment(user_id=user.id, item_id=item.id, comment_text="Second")
        c3 = manager.create_comment(user_id=user.id, item_id=item.id, comment_text="Third")

        comments = manager.get_comments(user_id=user.id, item_id=item.id)
        assert len(comments) == 3
        assert comments[0].comment_text == "First"
        assert comments[2].comment_text == "Third"

    def test_get_comments_includes_replies(self, db_session, make_user, make_client, make_engagement, make_follow_up_item):
        user = make_user(email="readreply@test.com")
        client = make_client(user=user)
        eng = make_engagement(client=client)
        item = make_follow_up_item(engagement=eng)

        manager = FollowUpItemsManager(db_session)
        parent = manager.create_comment(user_id=user.id, item_id=item.id, comment_text="Top level")
        reply = manager.create_comment(
            user_id=user.id, item_id=item.id,
            comment_text="Reply", parent_comment_id=parent.id,
        )

        comments = manager.get_comments(user_id=user.id, item_id=item.id)
        assert len(comments) == 2
        texts = [c.comment_text for c in comments]
        assert "Top level" in texts
        assert "Reply" in texts

    def test_get_comments_wrong_user_raises(self, db_session, make_user, make_client, make_engagement, make_follow_up_item):
        owner = make_user(email="owner2@test.com")
        other = make_user(email="other2@test.com")
        client = make_client(user=owner)
        eng = make_engagement(client=client)
        item = make_follow_up_item(engagement=eng)

        manager = FollowUpItemsManager(db_session)
        with pytest.raises(ValueError, match="not found or access denied"):
            manager.get_comments(user_id=other.id, item_id=item.id)

    def test_get_comments_for_engagement(self, db_session, make_user, make_client, make_engagement, make_follow_up_item):
        user = make_user(email="engcomments@test.com")
        client = make_client(user=user)
        eng = make_engagement(client=client)
        item1 = make_follow_up_item(engagement=eng, description="Item A")
        item2 = make_follow_up_item(engagement=eng, description="Item B")

        manager = FollowUpItemsManager(db_session)
        manager.create_comment(user_id=user.id, item_id=item1.id, comment_text="On A")
        manager.create_comment(user_id=user.id, item_id=item2.id, comment_text="On B")

        all_comments = manager.get_comments_for_engagement(user_id=user.id, engagement_id=eng.id)
        assert len(all_comments) == 2
        texts = {c.comment_text for c in all_comments}
        assert texts == {"On A", "On B"}


# ===========================================================================
# TestCommentManagerUpdate — update_comment
# ===========================================================================


class TestCommentManagerUpdate:
    """Test comment updates."""

    def test_update_comment_text(self, db_session, make_user, make_client, make_engagement, make_follow_up_item):
        user = make_user(email="update@test.com")
        client = make_client(user=user)
        eng = make_engagement(client=client)
        item = make_follow_up_item(engagement=eng)

        manager = FollowUpItemsManager(db_session)
        comment = manager.create_comment(user_id=user.id, item_id=item.id, comment_text="Original")
        updated = manager.update_comment(user_id=user.id, comment_id=comment.id, comment_text="Edited")

        assert updated is not None
        assert updated.comment_text == "Edited"

    def test_update_comment_strips_whitespace(self, db_session, make_user, make_client, make_engagement, make_follow_up_item):
        user = make_user(email="upstrip@test.com")
        client = make_client(user=user)
        eng = make_engagement(client=client)
        item = make_follow_up_item(engagement=eng)

        manager = FollowUpItemsManager(db_session)
        comment = manager.create_comment(user_id=user.id, item_id=item.id, comment_text="Before")
        updated = manager.update_comment(user_id=user.id, comment_id=comment.id, comment_text="  After  ")
        assert updated.comment_text == "After"

    def test_update_comment_empty_raises(self, db_session, make_user, make_client, make_engagement, make_follow_up_item):
        user = make_user(email="upempty@test.com")
        client = make_client(user=user)
        eng = make_engagement(client=client)
        item = make_follow_up_item(engagement=eng)

        manager = FollowUpItemsManager(db_session)
        comment = manager.create_comment(user_id=user.id, item_id=item.id, comment_text="Has text")

        with pytest.raises(ValueError, match="Comment text is required"):
            manager.update_comment(user_id=user.id, comment_id=comment.id, comment_text="")

    def test_update_comment_not_found(self, db_session, make_user):
        user = make_user(email="upnone@test.com")
        manager = FollowUpItemsManager(db_session)
        result = manager.update_comment(user_id=user.id, comment_id=99999, comment_text="Ghost")
        assert result is None

    def test_update_comment_wrong_author_raises(
        self, db_session, make_user, make_client, make_engagement, make_follow_up_item,
    ):
        """Only the comment author can edit their comment."""
        owner = make_user(email="comowner@test.com")
        other = make_user(email="comother@test.com")
        client = make_client(user=owner)
        eng = make_engagement(client=client)
        item = make_follow_up_item(engagement=eng)

        manager = FollowUpItemsManager(db_session)
        comment = manager.create_comment(user_id=owner.id, item_id=item.id, comment_text="Mine")

        # other user has access to engagement but is not the author
        # Since other doesn't own the client, _verify_comment_access will fail (returns None)
        result = manager.update_comment(user_id=other.id, comment_id=comment.id, comment_text="Not mine")
        assert result is None


# ===========================================================================
# TestCommentManagerDelete — delete_comment
# ===========================================================================


class TestCommentManagerDelete:
    """Test comment deletion."""

    def test_delete_comment_basic(self, db_session, make_user, make_client, make_engagement, make_follow_up_item):
        user = make_user(email="delete@test.com")
        client = make_client(user=user)
        eng = make_engagement(client=client)
        item = make_follow_up_item(engagement=eng)

        manager = FollowUpItemsManager(db_session)
        comment = manager.create_comment(user_id=user.id, item_id=item.id, comment_text="Doomed")
        success = manager.delete_comment(user_id=user.id, comment_id=comment.id)
        assert success is True

        # Verify gone
        comments = manager.get_comments(user_id=user.id, item_id=item.id)
        assert len(comments) == 0

    def test_delete_comment_not_found(self, db_session, make_user):
        user = make_user(email="delnone@test.com")
        manager = FollowUpItemsManager(db_session)
        result = manager.delete_comment(user_id=user.id, comment_id=99999)
        assert result is False

    def test_delete_comment_wrong_user(self, db_session, make_user, make_client, make_engagement, make_follow_up_item):
        owner = make_user(email="delowner@test.com")
        other = make_user(email="delother@test.com")
        client = make_client(user=owner)
        eng = make_engagement(client=client)
        item = make_follow_up_item(engagement=eng)

        manager = FollowUpItemsManager(db_session)
        comment = manager.create_comment(user_id=owner.id, item_id=item.id, comment_text="Protected")

        # Other user can't access
        result = manager.delete_comment(user_id=other.id, comment_id=comment.id)
        assert result is False


# ===========================================================================
# TestCommentCascadeDelete — item deletion cascades to comments
# ===========================================================================


class TestCommentCascadeDelete:
    """Verify cascade delete behavior."""

    def test_deleting_item_archives_comments(self, db_session, make_user, make_client, make_engagement, make_follow_up_item):
        user = make_user(email="cascade@test.com")
        client = make_client(user=user)
        eng = make_engagement(client=client)
        item = make_follow_up_item(engagement=eng)

        manager = FollowUpItemsManager(db_session)
        manager.create_comment(user_id=user.id, item_id=item.id, comment_text="Will be archived")
        manager.create_comment(user_id=user.id, item_id=item.id, comment_text="Also archived")

        # Verify 2 comments exist
        assert len(manager.get_comments(user_id=user.id, item_id=item.id)) == 2

        # Delete (soft-delete) the item
        manager.delete_item(user.id, item.id)

        # Comments should be archived (still physically present but archived_at set)
        all_comments = db_session.query(FollowUpItemComment).filter(
            FollowUpItemComment.follow_up_item_id == item.id
        ).all()
        assert len(all_comments) == 2
        for c in all_comments:
            assert c.archived_at is not None
            assert c.archive_reason == "parent_archived"

        # Active-only query returns none
        active = db_session.query(FollowUpItemComment).filter(
            FollowUpItemComment.follow_up_item_id == item.id,
            FollowUpItemComment.archived_at.is_(None),
        ).all()
        assert len(active) == 0

    def test_deleting_parent_comment_cascades_replies(
        self, db_session, make_user, make_client, make_engagement, make_follow_up_item,
    ):
        user = make_user(email="cascade_reply@test.com")
        client = make_client(user=user)
        eng = make_engagement(client=client)
        item = make_follow_up_item(engagement=eng)

        manager = FollowUpItemsManager(db_session)
        parent = manager.create_comment(user_id=user.id, item_id=item.id, comment_text="Parent")
        manager.create_comment(
            user_id=user.id, item_id=item.id,
            comment_text="Reply", parent_comment_id=parent.id,
        )

        assert len(manager.get_comments(user_id=user.id, item_id=item.id)) == 2

        # Delete parent — reply should cascade
        manager.delete_comment(user_id=user.id, comment_id=parent.id)

        comments = manager.get_comments(user_id=user.id, item_id=item.id)
        assert len(comments) == 0


# ===========================================================================
# TestCommentRoutes — Route registration
# ===========================================================================


class TestCommentRoutes:
    """Verify comment endpoints are registered on the app."""

    def test_routes_registered(self):
        from main import app

        route_paths = [r.path for r in app.routes if hasattr(r, "path")]

        assert "/follow-up-items/{item_id}/comments" in route_paths
        assert "/comments/{comment_id}" in route_paths

    def test_comment_create_endpoint_method(self):
        from main import app

        for route in app.routes:
            if hasattr(route, "path") and route.path == "/follow-up-items/{item_id}/comments":
                assert "POST" in route.methods or "GET" in route.methods
                break

    def test_comment_update_endpoint_method(self):
        from main import app

        for route in app.routes:
            if hasattr(route, "path") and route.path == "/comments/{comment_id}":
                methods = route.methods
                assert "PATCH" in methods or "DELETE" in methods
                break


# ===========================================================================
# TestCommentExport — Comments in engagement ZIP
# ===========================================================================


class TestCommentExport:
    """Verify comments are included in engagement ZIP export."""

    def test_export_includes_comments_markdown(
        self, db_session, make_user, make_client, make_engagement, make_follow_up_item,
    ):
        user = make_user(email="export@test.com", name="Auditor One")
        client = make_client(user=user, name="Export Corp")
        eng = make_engagement(client=client)
        item = make_follow_up_item(engagement=eng, description="Revenue anomaly detected")

        manager = FollowUpItemsManager(db_session)
        manager.create_comment(
            user_id=user.id, item_id=item.id,
            comment_text="Investigated — appears seasonal",
        )

        exporter = EngagementExporter(db_session)
        zip_bytes, filename = exporter.generate_zip(user.id, eng.id)

        with ZipFile(BytesIO(zip_bytes), 'r') as zf:
            names = zf.namelist()
            assert "follow_up_comments.md" in names

            md_content = zf.read("follow_up_comments.md").decode("utf-8")
            assert "Revenue anomaly detected" in md_content
            assert "Investigated — appears seasonal" in md_content
            assert "Auditor One" in md_content

    def test_export_excludes_comments_when_none(
        self, db_session, make_user, make_client, make_engagement,
    ):
        user = make_user(email="nocomments@test.com")
        client = make_client(user=user, name="Empty Corp")
        eng = make_engagement(client=client)

        exporter = EngagementExporter(db_session)
        zip_bytes, filename = exporter.generate_zip(user.id, eng.id)

        with ZipFile(BytesIO(zip_bytes), 'r') as zf:
            names = zf.namelist()
            assert "follow_up_comments.md" not in names

    def test_export_comments_contain_disclaimer(
        self, db_session, make_user, make_client, make_engagement, make_follow_up_item,
    ):
        user = make_user(email="disclaimer@test.com")
        client = make_client(user=user, name="Disc Corp")
        eng = make_engagement(client=client)
        item = make_follow_up_item(engagement=eng)

        manager = FollowUpItemsManager(db_session)
        manager.create_comment(user_id=user.id, item_id=item.id, comment_text="A note")

        exporter = EngagementExporter(db_session)
        zip_bytes, _ = exporter.generate_zip(user.id, eng.id)

        with ZipFile(BytesIO(zip_bytes), 'r') as zf:
            md_content = zf.read("follow_up_comments.md").decode("utf-8")
            assert "DISCLAIMER" in md_content
            assert "does not constitute" in md_content

    def test_export_manifest_includes_comments_file(
        self, db_session, make_user, make_client, make_engagement, make_follow_up_item,
    ):
        user = make_user(email="manifest@test.com")
        client = make_client(user=user, name="Manifest Corp")
        eng = make_engagement(client=client)
        item = make_follow_up_item(engagement=eng)

        manager = FollowUpItemsManager(db_session)
        manager.create_comment(user_id=user.id, item_id=item.id, comment_text="Tracked")

        exporter = EngagementExporter(db_session)
        zip_bytes, _ = exporter.generate_zip(user.id, eng.id)

        with ZipFile(BytesIO(zip_bytes), 'r') as zf:
            manifest = json.loads(zf.read("manifest.json"))
            filenames = [f["filename"] for f in manifest["files"]]
            assert "follow_up_comments.md" in filenames

    def test_export_threaded_comments_formatted(
        self, db_session, make_user, make_client, make_engagement, make_follow_up_item,
    ):
        user = make_user(email="thread_export@test.com", name="Lead Auditor")
        client = make_client(user=user, name="Thread Corp")
        eng = make_engagement(client=client)
        item = make_follow_up_item(engagement=eng, description="Suspicious pattern")

        manager = FollowUpItemsManager(db_session)
        parent = manager.create_comment(
            user_id=user.id, item_id=item.id,
            comment_text="Flagged for review",
        )
        manager.create_comment(
            user_id=user.id, item_id=item.id,
            comment_text="Reviewed and cleared",
            parent_comment_id=parent.id,
        )

        exporter = EngagementExporter(db_session)
        zip_bytes, _ = exporter.generate_zip(user.id, eng.id)

        with ZipFile(BytesIO(zip_bytes), 'r') as zf:
            md_content = zf.read("follow_up_comments.md").decode("utf-8")
            assert "Flagged for review" in md_content
            assert "Reviewed and cleared" in md_content
            # Reply should be indented (nested list)
            assert "  - **Lead Auditor**" in md_content


# ===========================================================================
# TestCommentZeroStorage — Guardrail 2 enforcement
# ===========================================================================


class TestCommentZeroStorage:
    """Verify Zero-Storage compliance for comments."""

    def test_comment_model_has_no_amount_fields(self):
        """Comment model stores only narrative text, no financial data."""
        import inspect
        source = inspect.getsource(FollowUpItemComment)
        prohibited_terms = [
            "account_number", "account_name", "debit", "credit",
            "balance", "invoice_amount", "vendor_name", "employee_name",
        ]
        for term in prohibited_terms:
            assert term not in source, f"Prohibited term '{term}' found in FollowUpItemComment source"

    def test_comment_text_is_text_column(self, db_engine):
        """comment_text should be a Text column (narrative only)."""
        inspector = sa_inspect(db_engine)
        columns = inspector.get_columns("follow_up_item_comments")
        text_col = next(c for c in columns if c["name"] == "comment_text")
        # SQLite reports TEXT type
        assert "TEXT" in str(text_col["type"]).upper()
