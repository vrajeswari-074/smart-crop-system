"""
Seed historical price data into the database.
Run once: python database/seed_data.py
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sqlite3
import random
import math
from config import Config

# Base prices per crop (₹/quintal)
BASE_PRICES = {
    'Wheat':     1800,
    'Rice':      2200,
    'Maize':     1400,
    'Tomato':    1200,
    'Onion':     1000,
    'Potato':     900,
    'Cotton':    5500,
    'Soybean':   3800,
    'Sugarcane':  350,
    'Barley':    1500,
}

# Season modifiers
SEASON_MODIFIERS = {
    'Kharif':  1.05,
    'Rabi':    1.10,
    'Zaid':    0.95,
    'Annual':  1.00,
}

# Crops that fit each season
SEASON_CROPS = {
    'Kharif':  ['Rice', 'Maize', 'Cotton', 'Soybean', 'Tomato', 'Sugarcane'],
    'Rabi':    ['Wheat', 'Barley', 'Potato', 'Onion', 'Sugarcane'],
    'Zaid':    ['Maize', 'Tomato', 'Onion', 'Potato'],
    'Annual':  ['Sugarcane', 'Cotton'],
}

def generate_seed_data(conn):
    cur = conn.cursor()
    d_rows = cur.execute("SELECT name FROM districts").fetchall()
    districts = [r[0] for r in d_rows]
    if not districts:
        districts = ['Chittoor', 'Guntur', 'Krishna'] # Fallback
        
    district_modifiers = {d: random.uniform(0.9, 1.15) for d in districts}

    rows = []
    years = list(range(2018, 2026))
    seasons = list(SEASON_CROPS.keys())
    state = "Andhra Pradesh"

    for year in years:
        for season in seasons:
            for district in districts:
                crops = SEASON_CROPS[season]
                for crop in crops:
                    base = BASE_PRICES[crop]
                    s_mod = SEASON_MODIFIERS[season]
                    d_mod = district_modifiers[district]
                    # Add year trend (slight inflation ~4% per year)
                    y_mod = (1.04 ** (year - 2018))
                    # Add random variance ±15%
                    variance = random.uniform(0.85, 1.15)
                    price = round(base * s_mod * d_mod * y_mod * variance, 2)
                    production = round(random.uniform(50, 500), 2)
                    demand_idx = round(random.uniform(0.6, 1.4), 3)
                    rows.append((crop, year, season, state, district, price, production, demand_idx))
    return rows


def seed():
    conn = sqlite3.connect(Config.DATABASE)
    cur = conn.cursor()
    # Clear existing seed data
    cur.execute("DELETE FROM price_history")
    rows = generate_seed_data(conn)
    cur.executemany(
        "INSERT INTO price_history (crop_name, year, season, state, district, price_per_quintal, production_tonnes, demand_index) VALUES (?,?,?,?,?,?,?,?)",
        rows
    )
    conn.commit()
    conn.close()
    print(f"✅ Seeded {len(rows)} price history records.")


if __name__ == '__main__':
    seed()
