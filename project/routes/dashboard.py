import datetime
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models.crop_entry import CropEntry
from models.price_history import PriceHistory
from services.analysis import get_global_distribution, detect_over_cultivation, get_alert_count
from db import get_db

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    db = get_db()
    stats = CropEntry.get_stats(db)
    recent_entries = CropEntry.get_recent(db, limit=8)
    
    year = datetime.datetime.now().year
    
    # Global distribution across all seasons this year
    global_dist = get_global_distribution(db, year=year)
    alert_count = get_alert_count(db)
    
    # Average prices for price cards
    avg_prices = PriceHistory.get_avg_by_crop(db)
    price_cards = [{'crop': r[0], 'avg': round(r[1], 0), 'min': round(r[2], 0), 'max': round(r[3], 0)} for r in avg_prices[:5]]

    return render_template('dashboard.html',
        stats=stats,
        recent_entries=recent_entries,
        global_dist=global_dist,
        alert_count=alert_count,
        price_cards=price_cards,
        current_year=year
    )
