class PriceHistory:
    @staticmethod
    def get_for_crop(db, crop_name, district=None):
        if district:
            return db.execute(
                "SELECT * FROM price_history WHERE crop_name=? AND district=? ORDER BY year, season",
                (crop_name, district)
            ).fetchall()
        return db.execute(
            "SELECT * FROM price_history WHERE crop_name=? ORDER BY year, season",
            (crop_name,)
        ).fetchall()

    @staticmethod
    def get_avg_by_crop(db, season=None):
        query = """SELECT crop_name, AVG(price_per_quintal) as avg_price,
                          MIN(price_per_quintal) as min_price,
                          MAX(price_per_quintal) as max_price
                   FROM price_history"""
        params = []
        if season:
            query += " WHERE season=?"
            params.append(season)
        query += " GROUP BY crop_name ORDER BY avg_price DESC"
        return db.execute(query, params).fetchall()

    @staticmethod
    def get_all_as_df(db):
        import pandas as pd
        rows = db.execute("SELECT * FROM price_history").fetchall()
        cols = ['id','crop_name','year','season','state','district','price_per_quintal','production_tonnes','demand_index']
        return pd.DataFrame(rows, columns=cols)
