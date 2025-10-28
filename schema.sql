-- Initialize the database.
-- Drop any existing data and create empty tables.

DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS rooms;

CREATE TABLE user (
--  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  author TEXT NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  content TEXT NOT NULL,
  room TEXT NOT NULL,
--  FOREIGN KEY (author) REFERENCES user (username),
 FOREIGN KEY (room) REFERENCES rooms (roomname) ON DELETE CASCADE
);

CREATE TABLE rooms (
  roomname TEXT NOT NULL,
  member TEXT NOT NULL,
  isadmin INTEGER NOT NULL DEFAULT 0,
  FOREIGN KEY (member) REFERENCES user (username)
);

INSERT INTO user (username, password) VALUES ("Message Jar", "I am good at choosing passwords");