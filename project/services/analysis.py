from config import Config


def get_crop_distribution(db, village, season, year):
    """
    Returns a list of dicts with crop_name and total_area for the given village/season/year.
    """
    from models.crop_entry import CropEntry
    rows = CropEntry.get_distribution(db, village, season, year)
    distribution = [{'crop': r[0], 'area': r[1]} for r in rows]
    return distribution


def get_global_distribution(db, season=None, year=None):
    from models.crop_entry import CropEntry
    rows = CropEntry.get_global_distribution(db, season, year)
    return [{'crop': r[0], 'area': r[1]} for r in rows]


def detect_over_cultivation(distribution):
    """
    Flag crops that occupy more than OVERCULTIVATION_THRESHOLD% of total area.
    Returns list of dicts with flags.
    """
    threshold = Config.OVERCULTIVATION_THRESHOLD
    total = sum(d['area'] for d in distribution)
    if total == 0:
        return []

    flagged = []
    for d in distribution:
        pct = (d['area'] / total) * 100
        flagged.append({
            'crop': d['crop'],
            'area': d['area'],
            'percentage': round(pct, 1),
            'over_cultivated': pct > threshold,
            'risk_level': _risk_level(pct)
        })
    return flagged


def _risk_level(pct):
    if pct > 40:
        return 'High Risk'
    elif pct > 20:
        return 'Medium Risk'
    return 'Low Risk'

def get_demand_supply_metrics(db, village, district, season, year):
    """
    Compares local village supply (area acres) with the district's historical demand index.
    """
    dist = get_crop_distribution(db, village, season, year)
    
    query = "SELECT crop_name, AVG(demand_index) FROM price_history WHERE district=? AND year>=? GROUP BY crop_name"
    # Fallback to general if district too specific, or just last 3 years
    rows = db.execute(query, (district, year - 3)).fetchall()
    
    if not rows: # fallback to all districts if somehow empty
        rows = db.execute("SELECT crop_name, AVG(demand_index) FROM price_history GROUP BY crop_name").fetchall()
        
    demand_map = {r[0]: r[1] for r in rows}
    
    total_area = sum(d['area'] for d in dist)
    
    metrics = []
    for d in dist:
        crop = d['crop']
        area = d['area']
        demand = demand_map.get(crop, 1.0)
        pct = (area / total_area * 100) if total_area else 0
        
        status = "Stable"
        status_color = "success"
        if demand < 0.95 and pct > 25:
            status = "Oversupply Risk"
            status_color = "danger"
        elif pct > 40:
            status = "Local Oversaturation"
            status_color = "warning"
        elif demand > 1.10:
            status = "High Market Demand"
            status_color = "success"
            
        metrics.append({
            'crop': crop,
            'supply_area': area,
            'supply_pct': round(pct, 1),
            'demand_index': round(demand, 2),
            'status': status,
            'status_color': status_color
        })
        
    return sorted(metrics, key=lambda x: x['supply_area'], reverse=True)


def get_village_stats(db, village):
    """Return summary stats for a specific village."""
    from models.crop_entry import CropEntry
    all_entries = CropEntry.get_by_village(db, village)
    if not all_entries:
        return None

    # all_entries columns: id, user_id, state, district, mandal, village, crop_name, area_acres, season, year, created_at
    crops = set(e[6] for e in all_entries)
    total_area = sum(e[7] for e in all_entries)
    farmers = set(e[1] for e in all_entries)
    seasons = set(e[8] for e in all_entries)

    return {
        'village': village,
        'unique_crops': len(crops),
        'total_area': round(total_area, 2),
        'total_farmers': len(farmers),
        'seasons_active': list(seasons),
        'crops_list': list(crops)
    }


def get_alert_count(db):
    """Count how many villages currently have over-cultivation alerts."""
    from models.crop_entry import CropEntry
    import datetime
    year = datetime.datetime.now().year
    villages = CropEntry.get_all_villages(db)
    alerts = 0
    for village in villages:
        for season in Config.SEASONS:
            dist = get_crop_distribution(db, village, season, year)
            if not dist:
                continue
            flagged = detect_over_cultivation(dist)
            if any(f['over_cultivated'] for f in flagged):
                alerts += 1
                break
    return alerts
