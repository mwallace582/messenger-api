CREATE TABLE IF NOT EXISTS messages (
    message text,
    sender text,
    recipients text,
    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);
