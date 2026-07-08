import pytest
import os
from passlib.hash import sha256_crypt
import app as my_app

# Only run integration tests if a MySQL server is running and configured
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

    # Insert default admin to allow login in integration tests
    conn = MySQLdb.connect(
        host=my_app.app.config['MYSQL_HOST'],
        user=my_app.app.config['MYSQL_USER'],
        passwd=my_app.app.config['MYSQL_PASSWORD'],
        db=TEST_DB
    )
    cursor = conn.cursor()
    hashed_password = sha256_crypt.hash('eswar@259522')
    cursor.execute(
        "INSERT INTO info (username, password, name, prof, street, city, phone) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        ('eswar_123', hashed_password, 'Parameswar K', 1, 'Adarshnagar', 'Anantapur', '9666585361')
    )
    conn.commit()
    cursor.close()
    conn.close()

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
def logged_in_client(setup_database):
    """Fixture that logs in the admin user and yields the authenticated client."""
    my_app.app.config['TESTING'] = True
    my_app.app.config['SECRET_KEY'] = 'test_secret_key'
    with my_app.app.test_client() as client:
        # Perform Admin login
        client.post('/login', data={
            'username': 'eswar_123',
            'password': 'eswar@259522'
        }, follow_redirects=True)
        yield client

def test_add_trainer_integration(logged_in_client):
    """TC_IT_04: Verify admin can successfully add a trainer and store it in the database."""
    response = logged_in_client.post('/addTrainor', data={
        'name': 'Test Trainer',
        'username': 'test_trainer',
        'password': 'password123',
        'confirm': 'password123',
        'street': 'Trainer St',
        'city': 'Trainer City',
        'phone': '111222333'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"You recruited a new Trainor!!" in response.data

    # Validate database state
    with my_app.app.app_context():
        cur = my_app.mysql.connection.cursor()
        cur.execute("SELECT * FROM info WHERE username = 'test_trainer'")
        info_row = cur.fetchone()
        cur.execute("SELECT * FROM trainors WHERE username = 'test_trainer'")
        trainer_row = cur.fetchone()
        cur.close()

        assert info_row is not None
        assert info_row['name'] == 'Test Trainer'
        assert trainer_row is not None

def test_add_recep_integration(logged_in_client):
    """TC_IT_03: Verify admin can successfully add a receptionist and store it in the database."""
    response = logged_in_client.post('/addRecep', data={
        'name': 'Test Recep',
        'username': 'test_recep',
        'password': 'password123',
        'confirm': 'password123',
        'street': 'Recep St',
        'city': 'Recep City',
        'phone': '444555666'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"You recruited a new Receptionist!!" in response.data

    # Validate database state
    with my_app.app.app_context():
        cur = my_app.mysql.connection.cursor()
        cur.execute("SELECT * FROM info WHERE username = 'test_recep'")
        info_row = cur.fetchone()
        cur.execute("SELECT * FROM receps WHERE username = 'test_recep'")
        recep_row = cur.fetchone()
        cur.close()

        assert info_row is not None
        assert info_row['name'] == 'Test Recep'
        assert recep_row is not None

def test_add_equip_integration(logged_in_client):
    """TC_IT_02: Verify admin can successfully add equipment and store it in the database."""
    response = logged_in_client.post('/addEquip', data={
        'name': 'Dumbbell',
        'count': 15
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"You added a new Equipment!!" in response.data

    # Validate database state
    with my_app.app.app_context():
        cur = my_app.mysql.connection.cursor()
        cur.execute("SELECT * FROM equip WHERE name = 'Dumbbell'")
        equip_row = cur.fetchone()
        cur.close()

        assert equip_row is not None
        assert equip_row['count'] == 15

def test_add_member_integration(logged_in_client):
    """TC_IT_01: Verify admin can successfully add a member and store it in the database."""
    # First, insert parent data dependencies (a plan and a trainer) directly into the test database
    with my_app.app.app_context():
        cur = my_app.mysql.connection.cursor()
        # Insert a plan
        cur.execute("INSERT INTO plans (name, exercise, sets, reps) VALUES (%s, %s, %s, %s)", ('Gold Plan', 'Bench Press', 3, 10))
        # Insert a trainer (we already have 'test_trainer' from the previous test, but we ensure it exists)
        cur.execute("SELECT * FROM trainors WHERE username = 'test_trainer'")
        if not cur.fetchone():
            hashed_pwd = sha256_crypt.hash('password123')
            cur.execute("INSERT INTO info (username, password, name, prof, street, city, phone) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                        ('test_trainer', hashed_pwd, 'Test Trainer', 3, 'Trainer St', 'Trainer City', '111222333'))
            cur.execute("INSERT INTO trainors (username) VALUES (%s)", ('test_trainer',))
        my_app.mysql.connection.commit()
        cur.close()

    # Now run the POST addMember route
    response = logged_in_client.post('/addMember', data={
        'name': 'Test Member',
        'username': 'test_member',
        'password': 'password123',
        'confirm': 'password123',
        'plan': 'Gold Plan',
        'trainor': 'test_trainer',
        'street': 'Member St',
        'city': 'Member City',
        'phone': '777888999'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"You added a new member!!" in response.data

    # Validate database state
    with my_app.app.app_context():
        cur = my_app.mysql.connection.cursor()
        cur.execute("SELECT * FROM info WHERE username = 'test_member'")
        info_row = cur.fetchone()
        cur.execute("SELECT * FROM members WHERE username = 'test_member'")
        member_row = cur.fetchone()
        cur.close()

        assert info_row is not None
        assert info_row['name'] == 'Test Member'
        assert member_row is not None
        assert member_row['plan'] == 'Gold Plan'
        assert member_row['trainor'] == 'test_trainer'
