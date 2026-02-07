"""Integration tests for chat endpoints."""
import pytest
from unittest.mock import patch

from .conftest import TEST_USER_A, TEST_USER_B


class TestSendChatMessage:
    """Tests for POST /api/{user_id}/chat endpoint."""

    def test_send_message_creates_new_conversation(self, client, mock_auth_user_a, auth_headers_user_a):
        """Test: Send message creates conversation."""
        with patch("api.deps.verify_user", return_value=TEST_USER_A):
            response = client.post(
                f"/api/{TEST_USER_A}/chat",
                json={"message": "Hello, this is a test message"},
                headers=auth_headers_user_a
            )

        assert response.status_code == 200
        data = response.json()
        assert "conversation_id" in data
        assert "user_message_id" in data
        assert "assistant_message_id" in data
        assert "response" in data
        assert len(data["conversation_id"]) == 36  # UUID length

    def test_send_message_to_existing_conversation(self, client, mock_auth_user_a, auth_headers_user_a):
        """Test: Send message to existing conversation."""
        with patch("api.deps.verify_user", return_value=TEST_USER_A):
            # Create first message
            response1 = client.post(
                f"/api/{TEST_USER_A}/chat",
                json={"message": "First message"},
                headers=auth_headers_user_a
            )
            conversation_id = response1.json()["conversation_id"]

            # Send second message to same conversation
            response2 = client.post(
                f"/api/{TEST_USER_A}/chat",
                json={"message": "Second message", "conversation_id": conversation_id},
                headers=auth_headers_user_a
            )

        assert response2.status_code == 200
        data = response2.json()
        assert data["conversation_id"] == conversation_id

    def test_empty_message_returns_400(self, client, mock_auth_user_a, auth_headers_user_a):
        """Test: Empty message returns 400."""
        with patch("api.deps.verify_user", return_value=TEST_USER_A):
            response = client.post(
                f"/api/{TEST_USER_A}/chat",
                json={"message": "   "},
                headers=auth_headers_user_a
            )

        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "invalid_message"

    def test_message_too_long_returns_400(self, client, mock_auth_user_a, auth_headers_user_a):
        """Test: Message too long returns 400."""
        with patch("api.deps.verify_user", return_value=TEST_USER_A):
            long_message = "x" * 10001
            response = client.post(
                f"/api/{TEST_USER_A}/chat",
                json={"message": long_message},
                headers=auth_headers_user_a
            )

        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "message_too_long"

    def test_invalid_conversation_id_returns_404(self, client, mock_auth_user_a, auth_headers_user_a):
        """Test: Invalid conversation_id returns 404."""
        with patch("api.deps.verify_user", return_value=TEST_USER_A):
            response = client.post(
                f"/api/{TEST_USER_A}/chat",
                json={"message": "Test", "conversation_id": "invalid-uuid-12345"},
                headers=auth_headers_user_a
            )

        assert response.status_code == 404
        data = response.json()
        assert data["error"] == "conversation_not_found"


class TestUserIdMismatch:
    """Tests for user_id mismatch (403)."""

    def test_wrong_user_id_returns_403(self, client, mock_auth_user_a, auth_headers_user_a):
        """Test: Wrong user_id returns 403."""
        # User A authenticated but trying to access User B's endpoint
        with patch("api.deps.get_current_user", return_value={"user_id": TEST_USER_A}):
            response = client.post(
                f"/api/{TEST_USER_B}/chat",  # Wrong user ID
                json={"message": "Test"},
                headers=auth_headers_user_a
            )

        assert response.status_code == 403


class TestListConversations:
    """Tests for GET /api/{user_id}/conversations endpoint."""

    def test_list_conversations_returns_correct_data(self, client, mock_auth_user_a, auth_headers_user_a):
        """Test: List conversations returns correct data."""
        with patch("api.deps.verify_user", return_value=TEST_USER_A):
            # Create some conversations
            client.post(f"/api/{TEST_USER_A}/chat", json={"message": "Msg 1"}, headers=auth_headers_user_a)
            client.post(f"/api/{TEST_USER_A}/chat", json={"message": "Msg 2"}, headers=auth_headers_user_a)

            response = client.get(f"/api/{TEST_USER_A}/conversations", headers=auth_headers_user_a)

        assert response.status_code == 200
        data = response.json()
        assert "conversations" in data
        assert "total" in data
        assert data["total"] >= 2

    def test_list_conversations_pagination(self, client, mock_auth_user_a, auth_headers_user_a):
        """Test: List conversations with pagination."""
        with patch("api.deps.verify_user", return_value=TEST_USER_A):
            response = client.get(
                f"/api/{TEST_USER_A}/conversations?limit=1&offset=0",
                headers=auth_headers_user_a
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["conversations"]) <= 1


class TestGetConversationDetail:
    """Tests for GET /api/{user_id}/conversations/{conversation_id} endpoint."""

    def test_get_conversation_detail_includes_messages(self, client, mock_auth_user_a, auth_headers_user_a):
        """Test: Get conversation detail includes all messages."""
        with patch("api.deps.verify_user", return_value=TEST_USER_A):
            # Create conversation with messages
            response1 = client.post(
                f"/api/{TEST_USER_A}/chat",
                json={"message": "Hello"},
                headers=auth_headers_user_a
            )
            conversation_id = response1.json()["conversation_id"]

            # Get detail
            response = client.get(
                f"/api/{TEST_USER_A}/conversations/{conversation_id}",
                headers=auth_headers_user_a
            )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == conversation_id
        assert "messages" in data
        assert len(data["messages"]) >= 2  # user + assistant


class TestDeleteConversation:
    """Tests for DELETE /api/{user_id}/conversations/{conversation_id} endpoint."""

    def test_delete_conversation_removes_from_list(self, client, mock_auth_user_a, auth_headers_user_a):
        """Test: Delete conversation removes it from list."""
        with patch("api.deps.verify_user", return_value=TEST_USER_A):
            # Create conversation
            response1 = client.post(
                f"/api/{TEST_USER_A}/chat",
                json={"message": "To be deleted"},
                headers=auth_headers_user_a
            )
            conversation_id = response1.json()["conversation_id"]

            # Delete it
            response = client.delete(
                f"/api/{TEST_USER_A}/conversations/{conversation_id}",
                headers=auth_headers_user_a
            )

        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] is True
        assert data["conversation_id"] == conversation_id
