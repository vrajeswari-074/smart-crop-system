from flask_login import UserMixin


class User(UserMixin):
    def __init__(self, id, username, email, password_hash, state, district, mandal, village, created_at=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.state = state
        self.district = district
        self.mandal = mandal
        self.village = village
        self.created_at = created_at

    @staticmethod
    def get_by_id(db, user_id):
        row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if row:
            return User(*row)
        return None

    @staticmethod
    def get_by_email(db, email):
        row = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if row:
            return User(*row)
        return None

    @staticmethod
    def get_by_username(db, username):
        row = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if row:
            return User(*row)
        return None

    @staticmethod
    def create(db, username, email, password_hash, state, district, mandal, village):
        db.execute(
            "INSERT INTO users (username, email, password_hash, state, district, mandal, village) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (username, email, password_hash, state, district, mandal, village)
        )
        db.commit()
        return db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
