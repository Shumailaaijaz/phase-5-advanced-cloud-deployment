"""Integration tests for conversation management."""
import pytest
from unittest.mock import patch

from .conftest import TEST_USER_A
from crud.conversation import (
    create_conversation,
    add_message,
    list_conversations,
    get_message_count,
)


class TestListConversations:
    """Tests for conversation listing."""

    def test_list_conversations_returns_correct_data(self, test_session):
        """Test: List conversations returns correct data."""
        # Create conversations
        conv1 = create_conversation(test_session, TEST_USER_A, "Conv 1")
        conv2 = create_conversation(test_session, TEST_USER_A, "Conv 2")

        conversations, total = list_conversations(test_session, TEST_USER_A)

        assert total == 2
        assert len(conversations) == 2

    def test_list_conversations_sorted_by_updated_at_desc(self, test_session):
        """Test: List conversations sorted by updated_at DESC."""
        import time

        # Create conversations with slight delay
        conv1 = create_conversation(test_session, TEST_USER_A, "First")
        time.sleep(0.01)  # Small delay
        conv2 = create_conversation(test_session, TEST_USER_A, "Second")
        time.sleep(0.01)
        conv3 = create_conversation(test_session, TEST_USER_A, "Third")

        conversations, _ = list_conversations(test_session, TEST_USER_A)

        # Most recent first
        assert conversations[0].title == "Third"
        assert conversations[1].title == "Second"
        assert conversations[2].title == "First"

    def test_list_conversations_includes_message_count(self, test_session):
        """Test: List includes message count for each conversation."""
        conv = create_conversation(test_session, TEST_USER_A, "With messages")
        add_message(test_session, conv.id, TEST_USER_A, "user", "Msg 1")
        add_message(test_session, conv.id, TEST_USER_A, "assistant", "Msg 2")
        add_message(test_session, conv.id, TEST_USER_A, "user", "Msg 3")

        count = get_message_count(test_session, conv.id, TEST_USER_A)
        assert count == 3


class TestConversationDetail:
    """Tests for conversation detail view."""

    def test_get_conversation_detail_includes_all_messages(self, client, auth_headers_user_a):
        """Test: Get conversation detail includes all messages."""
        with patch("api.deps.verify_user", return_value=TEST_USER_A):
            # Create conversation with multiple messages
            response1 = client.post(
                f"/api/{TEST_USER_A}/chat",
                json={"message": "First user message"},
                headers=auth_headers_user_a
            )
            conversation_id = response1.json()["conversation_id"]

            # Add more messages
            client.post(
                f"/api/{TEST_USER_A}/chat",
                json={"message": "Second user message", "conversation_id": conversation_id},
                headers=auth_headers_user_a
            )

            # Get detail
            response = client.get(
                f"/api/{TEST_USER_A}/conversations/{conversation_id}",
                headers=auth_headers_user_a
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) >= 4  # 2 user + 2 assistant messages


class TestDeleteConversation:
    """Tests for conversation deletion."""

    def test_delete_conversation_removes_it_from_list(self, client, auth_headers_user_a):
        """Test: Delete conversation removes it from list."""
        with patch("api.deps.verify_user", return_value=TEST_USER_A):
            # Create conversation
            response1 = client.post(
                f"/api/{TEST_USER_A}/chat",
                json={"message": "To delete"},
                headers=auth_headers_user_a
            )
            conversation_id = response1.json()["conversation_id"]

            # Get list before delete
            list_before = client.get(
                f"/api/{TEST_USER_A}/conversations",
                headers=auth_headers_user_a
            )
            total_before = list_before.json()["total"]

            # Delete
            client.delete(
                f"/api/{TEST_USER_A}/conversations/{conversation_id}",
                headers=auth_headers_user_a
            )

            # Get list after delete
            list_after = client.get(
                f"/api/{TEST_USER_A}/conversations",
                headers=auth_headers_user_a
            )
            total_after = list_after.json()["total"]

        assert total_after == total_before - 1

    def test_delete_nonexistent_conversation_returns_404(self, client, auth_headers_user_a):
        """Test: Delete nonexistent conversation returns 404."""
        with patch("api.deps.verify_user", return_value=TEST_USER_A):
            response = client.delete(
                f"/api/{TEST_USER_A}/conversations/nonexistent-id",
                headers=auth_headers_user_a
            )

        assert response.status_code == 404
        assert response.json()["error"] == "conversation_not_found"
