CREATE TABLE info(
    username VARCHAR(200),
    password VARCHAR(500),
    name VARCHAR(100),
    prof INT,
    street VARCHAR(100),
    city VARCHAR(50),
    phone VARCHAR(32),
    PRIMARY KEY(username)
);

CREATE TABLE plans(
    name VARCHAR(100),
    exercise VARCHAR(100),
    sets INT,
    reps INT,
    PRIMARY KEY(name, exercise)
);

CREATE TABLE receps(
    username VARCHAR(200),
    PRIMARY KEY(username),
    FOREIGN KEY(username) REFERENCES info(username)
);

CREATE TABLE trainors(
    username VARCHAR(200),
    PRIMARY KEY(username),
    FOREIGN KEY(username) REFERENCES info(username)
);

CREATE TABLE members(
    username VARCHAR(200),
    plan VARCHAR(100),
    trainor VARCHAR(200),
    PRIMARY KEY(username),
    FOREIGN KEY(username) REFERENCES info(username),
    FOREIGN KEY(plan) REFERENCES plans(name),
    FOREIGN KEY(trainor) REFERENCES trainors(username)
);

ALTER TABLE info
ADD time TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

CREATE TABLE progress(
    username VARCHAR(200),
    date DATE,
    daily_result VARCHAR(200),
    rate INT,
    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(username, date),
    FOREIGN KEY(username) REFERENCES members(username)
);

CREATE TABLE equip(
    name VARCHAR(100),
    count INT,
    PRIMARY KEY(name)
);

INSERT INTO info(
    username,
    password,
    name,
    prof,
    street,
    city,
    phone
)
VALUES(
    'eswar_123',
    '$5$rounds=535000$6gsmZKME5DrojTtI$8WcFkNyq0vGAh7M2splCCf6ZSVDcG3xOEDWP5XBRNL2',
    'Parameswar Kurakula',
    1,
    'Adarshnagar',
    'Anantapur',
    '9666585361'
);