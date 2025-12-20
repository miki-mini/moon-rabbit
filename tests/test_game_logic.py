import pytest
from datetime import datetime, date
from unittest.mock import MagicMock, patch
import game_logic

@pytest.fixture
def mock_firestore():
    """Mock the Firestore client and document reference."""
    with patch("game_logic.init_db") as mock_init:
        mock_db = MagicMock()
        mock_init.return_value = mock_db

        mock_doc_ref = MagicMock()
        mock_db.collection.return_value.document.return_value = mock_doc_ref
        yield mock_db, mock_doc_ref

def test_moon_info():
    """Test that moon info returns a string containing an emoji."""
    moon_info = game_logic.get_moon_info()
    assert isinstance(moon_info, str)
    # Check if any common moon emoji is present
    emojis = ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘"]
    assert any(e in moon_info for e in emojis)

def test_get_or_create_user_new(mock_firestore):
    """Test creating a new user."""
    _, mock_doc_ref = mock_firestore

    # Simulate non-existent document
    mock_doc = MagicMock()
    mock_doc.exists = False
    mock_doc_ref.get.return_value = mock_doc

    user_data, _ = game_logic.get_or_create_user("test_user_123")

    # should return default data
    assert user_data["user_id"] == "test_user_123"
    assert user_data["carrot_count"] == 0
    # should call set()
    mock_doc_ref.set.assert_called_once()

def test_morning_greeting_streak(mock_firestore):
    """Test that streak increases by 1 if logged in yesterday."""
    _, mock_doc_ref = mock_firestore

    today = datetime.now().date()
    yesterday = today.replace(day=today.day - 1) # simple logic, might fail on 1st of month but okay for mock
    # Use patch for datetime to be safe if rigorous, but for simple logic check:
    # Let's mock the user data returned

    mock_doc = MagicMock()
    mock_doc.exists = True
    # Fake user data: logged in yesterday
    yesterday_str = "2023-01-01" # dummy
    # Actually, the logic calculates delta. We need to control 'today'.

    # To test logic involving "today", we usually mock datetime.now()
    # But here we can simply trust the logic if we manipulate the input 'last_login' relative to real today
    # OR we use freezegun (not installed).
    # Let's try a logic test without mocking datetime by setting last_login to yesterday's real date.

    real_yesterday = (datetime.now().date() - pd.Timedelta(days=1)) if 'pd' in locals() else None
    # Just use python datetime
    from datetime import timedelta
    real_yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    mock_doc.to_dict.return_value = {
        "user_id": "test",
        "carrot_count": 10,
        "current_streak": 5,
        "last_login": real_yesterday_str,
        "items": []
    }
    mock_doc_ref.get.return_value = mock_doc

    # Run logic
    msg = game_logic.process_morning_greeting("test")

    assert "6日連続" in msg
    mock_doc_ref.update.assert_called_with({
        "carrot_count": 11,
        "last_login": datetime.now().strftime("%Y-%m-%d"),
        "current_streak": 6,
        "items": []
    })
