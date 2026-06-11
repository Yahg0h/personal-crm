-- Ativa suporte a chaves estrangeiras no SQLite (desativado por padrão)
PRAGMA foreign_keys = ON;

CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categories (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    name    TEXT    NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE contacts (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id          INTEGER NOT NULL,
    category_id      INTEGER DEFAULT NULL,
    name             TEXT    NOT NULL,
    nickname         TEXT,
    phone            TEXT,
    email            TEXT,
    birthday         TEXT,  -- "YYYY-MM-DD"
    photo_path       TEXT,
    notes            TEXT,
    alert_after_days INTEGER DEFAULT 30,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)     REFERENCES users(id)      ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
);

CREATE TABLE interactions (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    contact_id       INTEGER NOT NULL,
    user_id          INTEGER NOT NULL,
    interaction_date TEXT    NOT NULL,  -- "YYYY-MM-DD"
    type             TEXT    DEFAULT 'outro'
                         CHECK(type IN ('call','message','personal meeting','video call','other')),
    summary          TEXT,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE CASCADE
);