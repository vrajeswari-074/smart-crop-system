CREATE TABLE IF NOT EXISTS districts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS mandals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    district_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (district_id) REFERENCES districts(id)
);

CREATE TABLE IF NOT EXISTS villages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mandal_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (mandal_id) REFERENCES mandals(id)
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'Andhra Pradesh',
    district TEXT NOT NULL,
    mandal TEXT NOT NULL,
    village TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS crop_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    state TEXT NOT NULL DEFAULT 'Andhra Pradesh',
    district TEXT NOT NULL,
    mandal TEXT NOT NULL,
    village TEXT NOT NULL,
    crop_name TEXT NOT NULL,
    area_acres REAL NOT NULL,
    season TEXT NOT NULL,
    year INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    crop_name TEXT NOT NULL,
    year INTEGER NOT NULL,
    season TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'Andhra Pradesh',
    district TEXT NOT NULL,
    price_per_quintal REAL NOT NULL,
    production_tonnes REAL,
    demand_index REAL
);

CREATE TABLE IF NOT EXISTS recommendations_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    village TEXT NOT NULL,
    season TEXT NOT NULL,
    year INTEGER NOT NULL,
    recommended_crops TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
