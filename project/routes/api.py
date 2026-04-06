import datetime
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models.crop_entry import CropEntry
from models.price_history import PriceHistory
from services.analysis import get_crop_distribution, get_global_distribution, detect_over_cultivation, get_alert_count
from services.ml_predictor import predict_all_crops
from services.recommender import get_recommendations
from flask_login import login_user, logout_user
from models.user import User
from extensions import bcrypt
from db import get_db

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/me', methods=['GET'])
@login_required
def get_me():
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'village': current_user.village,
        'region': current_user.region
    })


@api_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    db = get_db()
    user = User.get_by_email(db, email)
    
    if user and bcrypt.check_password_hash(user.password_hash, password):
        login_user(user, remember=data.get('remember', True))
        return jsonify({'success': True, 'message': f'Welcome back, {user.username}!'})
    return jsonify({'success': False, 'message': 'Invalid email or password.'}), 401


@api_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    village = data.get('village', '').strip()
    region = data.get('region', 'North')
    
    db = get_db()
    
    if not username or not email or len(password) < 6 or not village:
        return jsonify({'success': False, 'message': 'Missing fields or password too short.'}), 400
        
    if User.get_by_email(db, email) or User.get_by_username(db, username):
        return jsonify({'success': False, 'message': 'Email or Username already taken.'}), 400
        
    pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    User.create(db, username, email, pw_hash, village, region)
    return jsonify({'success': True, 'message': 'Account created successfully!'})


@api_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'success': True, 'message': 'Logged out.'})


@api_bp.route('/distribution')
@login_required
def distribution():
    db = get_db()
    village = request.args.get('village', current_user.village)
    season = request.args.get('season', 'Kharif')
    year = request.args.get('year', datetime.datetime.now().year, type=int)

    dist = get_crop_distribution(db, village, season, year)
    return jsonify({
        'labels': [d['crop'] for d in dist],
        'data': [d['area'] for d in dist]
    })


@api_bp.route('/global-distribution')
@login_required
def global_distribution():
    db = get_db()
    season = request.args.get('season')
    year = request.args.get('year', type=int)
    dist = get_global_distribution(db, season, year)
    return jsonify({
        'labels': [d['crop'] for d in dist],
        'data': [d['area'] for d in dist]
    })


@api_bp.route('/price-history')
@login_required
def price_history():
    db = get_db()
    crop = request.args.get('crop', 'Wheat')
    region = request.args.get('region', 'North')
    rows = db.execute(
        "SELECT year, season, AVG(price_per_quintal) as avg_price FROM price_history WHERE crop_name=? AND region=? GROUP BY year, season ORDER BY year",
        (crop, region)
    ).fetchall()
    labels = [f"{r[0]} {r[1]}" for r in rows]
    prices = [round(r[2], 2) for r in rows]
    return jsonify({'labels': labels, 'prices': prices})


@api_bp.route('/predictions')
@login_required
def predictions():
    season = request.args.get('season', 'Kharif')
    region = request.args.get('region', 'North')
    year = request.args.get('year', datetime.datetime.now().year, type=int)
    
    preds = predict_all_crops(season, year, region)
    labels = list(preds.keys())
    prices = [preds[c].get('price') or 0 for c in labels]
    return jsonify({'labels': labels, 'prices': prices})


@api_bp.route('/alerts')
@login_required
def alerts():
    db = get_db()
    year = datetime.datetime.now().year
    villages = CropEntry.get_all_villages(db)
    alert_list = []
    for village in villages:
        for season in ['Kharif', 'Rabi', 'Zaid', 'Annual']:
            dist = get_crop_distribution(db, village, season, year)
            if not dist:
                continue
            flagged = detect_over_cultivation(dist)
            over = [f for f in flagged if f['over_cultivated']]
            if over:
                for f in over:
                    alert_list.append({
                        'village': village,
                        'season': season,
                        'crop': f['crop'],
                        'percentage': f['percentage'],
                        'risk': f['risk_level']
                    })
    return jsonify({'alerts': alert_list})


@api_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard_stats():
    db = get_db()
    stats = CropEntry.get_stats(db)
    recent_entries = CropEntry.get_recent(db, limit=8)
    alert_count = get_alert_count(db)
    avg_prices = PriceHistory.get_avg_by_crop(db)
    price_cards = [{'crop': r[0], 'avg': round(r[1], 0), 'min': round(r[2], 0), 'max': round(r[3], 0)} for r in avg_prices[:5]]
    
    # Sqlite3.Row is not directly json serializable, so convert to dict
    return jsonify({
        'stats': {'total_entries': stats.get('total_entries', 0), 'total_villages': stats.get('total_villages', 0), 'total_farmers': stats.get('total_farmers', 0)},
        'recent_entries': [dict(r) for r in recent_entries],
        'alert_count': alert_count,
        'price_cards': price_cards
    })


@api_bp.route('/submit-crop', methods=['POST'])
@login_required
def submit_crop():
    data = request.get_json() or {}
    village = data.get('village', '').strip() or current_user.village
    region = data.get('region', current_user.region)
    crop_name = data.get('crop_name')
    area_acres = data.get('area_acres')
    season = data.get('season')
    year = data.get('year') or datetime.datetime.now().year
    
    try:
        area_acres = float(area_acres)
    except:
        return jsonify({'success': False, 'message': 'Invalid area acres'}), 400
        
    db = get_db()
    CropEntry.create(db, current_user.id, village, region, crop_name, area_acres, season, year)
    return jsonify({'success': True, 'message': 'Crop entry submitted successfully!'})


@api_bp.route('/recommendations', methods=['GET'])
@login_required
def get_recommendations_api():
    db = get_db()
    village = request.args.get('village', current_user.village)
    season = request.args.get('season', 'Kharif')
    region = request.args.get('region', current_user.region)
    
    recommendations = get_recommendations(db, village, season, region)
    return jsonify({'recommendations': recommendations})
