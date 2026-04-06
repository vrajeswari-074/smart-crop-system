import os
import sys
import json
import sqlite3

# Ensure path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import Config

JSON_FILE_PATH = r"c:\Users\malle\Downloads\andha xl.json"

def ingest_data():
    if not os.path.exists(JSON_FILE_PATH):
        print(f"Error: Could not find file at {JSON_FILE_PATH}")
        return

    print("Loading JSON file...")
    with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        
        # The file might be a comma-separated list of objects missing the outer array brackets
        if not content.startswith('['):
            content = f"[{content}]"
            
        data = json.loads(content)

    conn = sqlite3.connect(Config.DATABASE)
    cur = conn.cursor()

    print("Clearing old locations...")
    cur.execute("DELETE FROM villages")
    cur.execute("DELETE FROM mandals")
    cur.execute("DELETE FROM districts")

    district_map = {} # name -> id
    mandal_map = {} # (district_id, mandal_name) -> id
    villages_to_insert = []

    print("Parsing JSON rows...")
    # Dictionary to collect unique names before DB insert
    districts_set = set()
    mandals_dict = {} # "district_name" -> set("mandal_name")
    villages_list = [] # ("district_name", "mandal_name", "village_name")

    for row in data:
        # Skip header if present
        if row.get("Column3") == "District Name (In English)":
            continue
            
        dist_name = row.get("Column3")
        mandal_name = row.get("Column5")
        village_name = row.get("Column8")

        if not dist_name or not mandal_name or not village_name:
            continue

        dist_name = dist_name.strip().title()
        mandal_name = mandal_name.strip().title()
        village_name = village_name.strip().title()

        districts_set.add(dist_name)
        
        if dist_name not in mandals_dict:
            mandals_dict[dist_name] = set()
        mandals_dict[dist_name].add(mandal_name)
        
        villages_list.append((dist_name, mandal_name, village_name))

    print("Inserting data into database...")
    
    # Insert Districts
    for d_name in sorted(list(districts_set)):
        cur.execute("INSERT INTO districts (name) VALUES (?)", (d_name,))
        district_map[d_name] = cur.lastrowid

    # Insert Mandals
    for d_name, m_set in mandals_dict.items():
        d_id = district_map[d_name]
        for m_name in sorted(list(m_set)):
            cur.execute("INSERT INTO mandals (district_id, name) VALUES (?, ?)", (d_id, m_name))
            mandal_map[(d_id, m_name)] = cur.lastrowid

    # Prepare Villages
    for dist_name, mandal_name, v_name in villages_list:
        d_id = district_map[dist_name]
        m_id = mandal_map[(d_id, mandal_name)]
        villages_to_insert.append((m_id, v_name))

    # Bulk Insert Villages
    cur.executemany("INSERT INTO villages (mandal_id, name) VALUES (?, ?)", villages_to_insert)

    conn.commit()
    conn.close()

    print(f"✅ Successfully ingested {len(districts_set)} Districts, {len(mandal_map)} Mandals, and {len(villages_to_insert)} Villages from real dataset!")

if __name__ == '__main__':
    ingest_data()
