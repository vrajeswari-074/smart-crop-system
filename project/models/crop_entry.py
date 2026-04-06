class CropEntry:
    def __init__(self, id, user_id, state, district, mandal, village, crop_name, area_acres, season, year, created_at=None):
        self.id = id
        self.user_id = user_id
        self.state = state
        self.district = district
        self.mandal = mandal
        self.village = village
        self.crop_name = crop_name
        self.area_acres = area_acres
        self.season = season
        self.year = year
        self.created_at = created_at

    @staticmethod
    def create(db, user_id, state, district, mandal, village, crop_name, area_acres, season, year):
        db.execute(
            "INSERT INTO crop_entries (user_id, state, district, mandal, village, crop_name, area_acres, season, year) VALUES (?,?,?,?,?,?,?,?,?)",
            (user_id, state, district, mandal, village, crop_name, area_acres, season, year)
        )
        db.commit()

    @staticmethod
    def get_by_village(db, village, season=None, year=None):
        query = "SELECT * FROM crop_entries WHERE village = ?"
        params = [village]
        if season:
            query += " AND season = ?"
            params.append(season)
        if year:
            query += " AND year = ?"
            params.append(year)
        query += " ORDER BY created_at DESC"
        return db.execute(query, params).fetchall()

    @staticmethod
    def get_recent(db, limit=20):
        return db.execute(
            "SELECT ce.*, u.username FROM crop_entries ce JOIN users u ON ce.user_id=u.id ORDER BY ce.created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()

    @staticmethod
    def get_all_villages(db):
        rows = db.execute("SELECT DISTINCT village FROM crop_entries ORDER BY village").fetchall()
        return [r[0] for r in rows]

    @staticmethod
    def get_distribution(db, village, season, year):
        return db.execute(
            """SELECT crop_name, SUM(area_acres) as total_area
               FROM crop_entries
               WHERE village=? AND season=? AND year=?
               GROUP BY crop_name
               ORDER BY total_area DESC""",
            (village, season, year)
        ).fetchall()

    @staticmethod
    def get_global_distribution(db, season=None, year=None):
        query = """SELECT crop_name, SUM(area_acres) as total_area
                   FROM crop_entries"""
        params = []
        if season or year:
            query += " WHERE "
            clauses = []
            if season:
                clauses.append("season=?")
                params.append(season)
            if year:
                clauses.append("year=?")
                params.append(year)
            query += " AND ".join(clauses)
        query += " GROUP BY crop_name ORDER BY total_area DESC"
        return db.execute(query, params).fetchall()

    @staticmethod
    def get_stats(db):
        total_entries = db.execute("SELECT COUNT(*) FROM crop_entries").fetchone()[0]
        total_villages = db.execute("SELECT COUNT(DISTINCT village) FROM crop_entries").fetchone()[0]
        total_farmers = db.execute("SELECT COUNT(DISTINCT user_id) FROM crop_entries").fetchone()[0]
        total_area = db.execute("SELECT SUM(area_acres) FROM crop_entries").fetchone()[0] or 0
        return {
            'total_entries': total_entries,
            'total_villages': total_villages,
            'total_farmers': total_farmers,
            'total_area': round(total_area, 2)
        }
