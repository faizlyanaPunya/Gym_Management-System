import pytest
from unittest.mock import MagicMock, patch
import app as my_app

@pytest.fixture
def client():
    my_app.app.config['TESTING'] = True
    my_app.app.config['SECRET_KEY'] = 'test_secret_key'
    with my_app.app.test_client() as client:
        yield client

@pytest.fixture
def logged_in_admin(client):
    """Fixture to set admin session variables directly."""
    with client.session_transaction() as sess:
        sess['logged_in'] = True
        sess['username'] = 'eswar_123'
        sess['prof'] = 1  # Admin profile
    return client

# --- Add Trainer Unit Tests (TC_01, TC_02, TC_03) ---

@patch('app.mysql')
def test_valid_trainer_registration_tc01(mock_mysql, logged_in_admin):
    """TC_01: Verify successful trainer recruitment with valid data."""
    mock_cursor = MagicMock()
    mock_mysql.connection.cursor.return_value = mock_cursor
    
    # 1st query: SELECT username FROM info (returns existing usernames)
    # 2nd query: INSERT info, 3rd query: INSERT trainors
    mock_cursor.execute.side_effect = [1, 1, 1]
    mock_cursor.fetchall.return_value = [{'username': 'eswar_123'}]

    response = logged_in_admin.post('/addTrainor', data={
        'name': 'Marisa',
        'username': 'Marisa123',
        'password': 'marisa123',
        'confirm': 'marisa123',
        'street': 'Taman Menara',
        'city': 'Perak',
        'phone': '01122087767'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"You recruited a new Trainor!!" in response.data

@patch('app.mysql')
def test_empty_username_tc02(mock_mysql, logged_in_admin):
    """TC_02: Verify system displays validation message when username is empty."""
    mock_cursor = MagicMock()
    mock_mysql.connection.cursor.return_value = mock_cursor
    
    mock_cursor.execute.return_value = 1
    mock_cursor.fetchall.return_value = [{'username': 'eswar_123'}]

    response = logged_in_admin.post('/addTrainor', data={
        'name': 'Rina',
        'username': '', # Empty username
        'password': 'rina123',
        'confirm': 'rina123',
        'street': 'Taman Damai',
        'city': 'Johor',
        'phone': '01975567790'
    }, follow_redirects=True)

    assert response.status_code == 200
    # The page should show validation error messages
    assert b"This field is required" in response.data or b"InputRequired" in response.data or b"addTrainor" in response.request.path

@patch('app.mysql')
def test_mismatch_password_tc03(mock_mysql, logged_in_admin):
    """TC_03: Verify system displays validation message when passwords do not match."""
    mock_cursor = MagicMock()
    mock_mysql.connection.cursor.return_value = mock_cursor
    
    mock_cursor.execute.return_value = 1
    mock_cursor.fetchall.return_value = [{'username': 'eswar_123'}]

    response = logged_in_admin.post('/addTrainor', data={
        'name': 'Rose',
        'username': 'Rose123',
        'password': 'rose123',
        'confirm': 'rose321', # Mismatched password
        'street': 'Jalan Indah',
        'city': 'Melaka',
        'phone': '01879990621'
    }, follow_redirects=True)

    assert response.status_code == 200
    # Verify WTForms equal_to validation message is shown
    assert b"Passwords aren&#39;t matching pal!, check &#39;em" in response.data or b"Passwords aren't matching pal!, check 'em" in response.data
