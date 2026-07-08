import pytest
import os
from passlib.hash import sha256_crypt
import app as my_app

# Only run integration tests if a MySQL server is running and configured
# We will use a test database "gym_test" to avoid overwriting production/dev data
TEST_DB = "gym_test"

@pytest.fixture(scope="module")
def setup_database():
    """Sets up a clean test database and teardown after tests finish."""
    import MySQLdb
    
    # Safe close wrapper to prevent OperationalError (2006, '') on context teardown
    original_connect = MySQLdb.connect
    def safe_connect(*args, **kwargs):
        conn = original_connect(*args, **kwargs)
        original_close = conn.close
        def safe_close(*c_args, **c_kwargs):
            try:
                original_close(*c_args, **c_kwargs)
            except Exception:
                pass
        conn.close = safe_close
        return conn
    MySQLdb.connect = safe_connect

    # Connect without database specified to create the test database
    try:
        conn = MySQLdb.connect(
            host=my_app.app.config['MYSQL_HOST'],
            user=my_app.app.config['MYSQL_USER'],
            passwd=my_app.app.config['MYSQL_PASSWORD']
        )
    except Exception as e:
        pytest.skip(f"Local MySQL server is not running or accessible: {e}")
        return

    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {TEST_DB}")
    conn.commit()
    cursor.close()
    conn.close()

    # Re-connect to the test database and run the schema setup
    conn = MySQLdb.connect(
        host=my_app.app.config['MYSQL_HOST'],
        user=my_app.app.config['MYSQL_USER'],
        passwd=my_app.app.config['MYSQL_PASSWORD'],
        db=TEST_DB
    )
    cursor = conn.cursor()

    # Create tables based on gym.sql schema
    schema = [
        """CREATE TABLE IF NOT EXISTS info(
            username VARCHAR(200),
            password VARCHAR(500),
            name VARCHAR(100),
            prof INT,
            street VARCHAR(100),
            city VARCHAR(50),
            phone VARCHAR(32),
            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(username)
        );""",
        """CREATE TABLE IF NOT EXISTS plans(
            name VARCHAR(100),
            exercise VARCHAR(100),
            sets INT,
            reps INT,
            PRIMARY KEY(name, exercise)
        );""",
        """CREATE TABLE IF NOT EXISTS receps(
            username VARCHAR(200),
            PRIMARY KEY(username),
            FOREIGN KEY(username) REFERENCES info(username)
        );""",
        """CREATE TABLE IF NOT EXISTS trainors(
            username VARCHAR(200),
            PRIMARY KEY(username),
            FOREIGN KEY(username) REFERENCES info(username)
        );""",
        """CREATE TABLE IF NOT EXISTS members(
            username VARCHAR(200),
            plan VARCHAR(100),
            trainor VARCHAR(200),
            PRIMARY KEY(username),
            FOREIGN KEY(username) REFERENCES info(username),
            FOREIGN KEY(trainor) REFERENCES trainors(username)
        );""",
        """CREATE TABLE IF NOT EXISTS progress(
            username VARCHAR(200),
            date DATE,
            daily_result VARCHAR(200),
            rate INT,
            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(username, date),
            FOREIGN KEY(username) REFERENCES members(username)
        );""",
        """CREATE TABLE IF NOT EXISTS equip(
            name VARCHAR(100),
            count INT,
            PRIMARY KEY(name)
        );"""
    ]

    for statement in schema:
        cursor.execute(statement)
    conn.commit()
    cursor.close()
    conn.close()

    # Point Flask app config to the test database
    original_db = my_app.app.config['MYSQL_DB']
    my_app.app.config['MYSQL_DB'] = TEST_DB

    yield

    # Clean up / Teardown test database by dropping tables
    conn = MySQLdb.connect(
        host=my_app.app.config['MYSQL_HOST'],
        user=my_app.app.config['MYSQL_USER'],
        passwd=my_app.app.config['MYSQL_PASSWORD'],
        db=TEST_DB
    )
    cursor = conn.cursor()
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    for table in ["progress", "members", "receps", "trainors", "info", "plans", "equip"]:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.commit()
    cursor.close()
    conn.close()
    my_app.app.config['MYSQL_DB'] = original_db

@pytest.fixture
def client(setup_database):
    my_app.app.config['TESTING'] = True
    my_app.app.config['SECRET_KEY'] = 'test_secret_key'
    with my_app.app.test_client() as client:
        yield client

def test_database_integration_flow(client):
    """Integrates Flask client with the test database to perform user registration, login, and profile check."""
    # 1. Manually insert an admin user directly into the test database
    with my_app.app.app_context():
        cur = my_app.mysql.connection.cursor()
        
        hashed_password = sha256_crypt.hash('eswar@259522')
        cur.execute(
            "INSERT INTO info (username, password, name, prof, street, city, phone) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            ('eswar_123', hashed_password, 'Parameswar K', 1, 'Adarshnagar', 'Anantapur', '9666585361')
        )
        my_app.mysql.connection.commit()

        # Verify insertion
        cur.execute("SELECT * FROM info WHERE username = %s", ['eswar_123'])
        user = cur.fetchone()
        assert user is not None
        assert user['name'] == 'Parameswar K'
        cur.close()

    # 2. Test log in flow using client and the real database record
    response = client.post('/login', data={
        'username': 'eswar_123',
        'password': 'eswar@259522'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"You are logged in" in response.data
