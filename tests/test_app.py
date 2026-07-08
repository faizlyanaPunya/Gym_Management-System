import pytest
from unittest.mock import MagicMock, patch
import app as my_app

@pytest.fixture
def client():
    my_app.app.config['TESTING'] = True
    my_app.app.config['SECRET_KEY'] = 'test_secret_key'
    with my_app.app.test_client() as client:
        yield client

def test_home_page(client):
    """Test that the homepage loads successfully."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Home" in response.data or b"Login" in response.data

def test_login_page_get(client):
    """Test that the login page GET request loads successfully."""
    response = client.get('/login')
    assert response.status_code == 200

@patch('app.mysql')
def test_login_post_success(mock_mysql, client):
    """Test successful login using mocked mysql connection."""
    # Setup mock cursor and query execution
    mock_cursor = MagicMock()
    mock_mysql.connection.cursor.return_value = mock_cursor
    
    # Simulate finding 1 user in database
    mock_cursor.execute.return_value = 1
    # Mock passlib hashed password verification: candidate 'password' matches hash
    from passlib.hash import sha256_crypt
    hashed_password = sha256_crypt.encrypt('password')
    
    mock_cursor.fetchone.return_value = {
        'username': 'test_user',
        'password': hashed_password,
        'prof': 1 # Admin profile
    }

    # Perform POST login request
    response = client.post('/login', data={
        'username': 'test_user',
        'password': 'password'
    }, follow_redirects=True)

    assert response.status_code == 200
    # Should display logged in message and admin dashboard
    assert b"You are logged in" in response.data

@patch('app.mysql')
def test_login_post_invalid_password(mock_mysql, client):
    """Test failed login with incorrect password."""
    mock_cursor = MagicMock()
    mock_mysql.connection.cursor.return_value = mock_cursor
    mock_cursor.execute.return_value = 1
    
    from passlib.hash import sha256_crypt
    hashed_password = sha256_crypt.encrypt('correct_password')
    
    mock_cursor.fetchone.return_value = {
        'username': 'test_user',
        'password': hashed_password,
        'prof': 1
    }

    response = client.post('/login', data={
        'username': 'test_user',
        'password': 'wrong_password'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Invalid login" in response.data
