import sqlite3
import random
import os
import sys

# Ensure path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import Config

DISTRICTS = [
    "Alluri Sitharama Raju", "Anakapalli", "Anantapuramu", "Annamayya", "Bapatla", 
    "Chittoor", "Dr. B. R. Ambedkar Konaseema", "East Godavari", "Eluru", "Guntur", 
    "Kakinada", "Krishna", "Kurnool", "Nandyal", "NTR", "Palnadu", 
    "Parvathipuram Manyam", "Prakasam", "Sri Potti Sriramulu Nellore", 
    "Sri Sathya Sai", "Srikakulam", "Tirupati", "Visakhapatnam", 
    "Vizianagaram", "West Godavari", "YSR"
] # 26 official AP districts

PREFIXES = ["Rama", "Siva", "Peda", "Chinna", "Konda", "Kota", "Venkata", "Krishna", "Bala", "Maha", "Ganga", "Surya", "Chandra", "Lakshmi", "Devi", "Naga", "Goura", "Kotha", "Pata", "Narasimha", "Tirupati", "Sita", "Hari", "Ravi", "Muthyala", "Malla", "Erra", "Nalla", "Tella", "Pacha"]
SUFFIXES = ["peta", "pali", "palli", "puram", "varam", "padu", "gudem", "konda", "valasa", "pudi", "rajupeta", "palem", "macherla", "kuru", "vada"]

def generate_name(existing_names):
    attempts = 0
    while True:
        name = random.choice(PREFIXES) + random.choice(SUFFIXES)
        attempts += 1
        if name not in existing_names or attempts > 50:
            return name

def seed_locations():
    conn = sqlite3.connect(Config.DATABASE)
    cur = conn.cursor()

    print("Clearing old locations...")
    cur.execute("DELETE FROM villages")
    cur.execute("DELETE FROM mandals")
    cur.execute("DELETE FROM districts")

    print(f"Generating 26 Districts, ~688 Mandals, and ~17,200 Villages...")
    
    total_mandals = 688
    mandals_per_district = total_mandals // len(DISTRICTS)
    
    total_villages = 17200
    villages_per_mandal = total_villages // total_mandals
    
    base_mandal_names = set()
    base_village_names = set()

    for d_name in DISTRICTS:
        cur.execute("INSERT INTO districts (name) VALUES (?)", (d_name,))
        d_id = cur.lastrowid
        
        # Generate Mandals for this district
        for _ in range(mandals_per_district + random.randint(-2, 3)):
            m_name = generate_name(base_mandal_names).capitalize() + " Mandal"
            base_mandal_names.add(m_name)
            cur.execute("INSERT INTO mandals (district_id, name) VALUES (?, ?)", (d_id, m_name))
            m_id = cur.lastrowid
            
            # Generate Villages for this mandal
            v_recs = []
            mandal_villages = set()
            for _ in range(villages_per_mandal + random.randint(-5, 5)):
                v_name = generate_name(mandal_villages).capitalize()
                v_recs.append((m_id, v_name))
                mandal_villages.add(v_name)
            
            cur.executemany("INSERT INTO villages (mandal_id, name) VALUES (?, ?)", v_recs)

    conn.commit()
    conn.close()
    print("✅ Successfully generated a massive realistic hierarchical AP geography dataset.")

if __name__ == '__main__':
    seed_locations()
