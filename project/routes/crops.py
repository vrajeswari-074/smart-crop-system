import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from config import Config
from models.crop_entry import CropEntry
from services.analysis import get_crop_distribution, detect_over_cultivation, get_village_stats, get_demand_supply_metrics
from services.recommender import get_recommendations
from services.ml_predictor import predict_price, get_price_trend, train_model
from db import get_db

crops_bp = Blueprint('crops', __name__)


@crops_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit():
    if request.method == 'POST':
        village = request.form.get('village', '').strip() or current_user.village
        mandal = request.form.get('mandal', '').strip() or current_user.mandal
        district = request.form.get('district', '').strip() or current_user.district
        state = 'Andhra Pradesh'
        crop_name = request.form.get('crop_name')
        area_acres = request.form.get('area_acres', type=float)
        season = request.form.get('season')
        year = request.form.get('year', type=int) or datetime.datetime.now().year

        errors = []
        if not village:
            errors.append('Village is required.')
        if crop_name not in Config.CROPS:
            errors.append('Invalid crop selected.')
        if not area_acres or area_acres <= 0:
            errors.append('Area must be a positive number.')
        if season not in Config.SEASONS:
            errors.append('Invalid season.')

        if errors:
            for e in errors:
                flash(e, 'error')
        else:
            db = get_db()
            CropEntry.create(db, current_user.id, state, district, mandal, village, crop_name, area_acres, season, year)
            flash(f'✅ Crop entry for {crop_name} submitted successfully!', 'success')
            return redirect(url_for('crops.analysis'))

    years = list(range(2020, datetime.datetime.now().year + 2))
    return render_template('submit.html',
        crops=Config.CROPS,
        seasons=Config.SEASONS,
        years=years,
        current_year=datetime.datetime.now().year
    )


@crops_bp.route('/analysis')
@login_required
def analysis():
    db = get_db()
    village = request.args.get('village', current_user.village)
    season = request.args.get('season', 'Kharif')
    year = request.args.get('year', datetime.datetime.now().year, type=int)

    villages = CropEntry.get_all_villages(db)
    distribution = get_crop_distribution(db, village, season, year)
    flagged = detect_over_cultivation(distribution) if distribution else []
    village_stats = get_village_stats(db, village)

    global_dist = []
    for v in villages[:10]:
        d = get_crop_distribution(db, v, season, year)
        if d:
            global_dist.append({'village': v, 'crops': d})

    # NEW: Demand vs Supply Metrics
    demand_supply_metrics = get_demand_supply_metrics(db, village, current_user.district, season, year)

    years = list(range(2020, datetime.datetime.now().year + 2))
    return render_template('analysis.html',
        village=village,
        season=season,
        year=year,
        villages=villages,
        seasons=Config.SEASONS,
        years=years,
        distribution=distribution,
        flagged=flagged,
        village_stats=village_stats,
        global_dist=global_dist,
        demand_supply_metrics=demand_supply_metrics
    )


@crops_bp.route('/recommend')
@login_required
def recommend():
    db = get_db()
    village = request.args.get('village', current_user.village)
    season = request.args.get('season', 'Kharif')
    district = request.args.get('district', current_user.district)
    soil_type = request.args.get('soil', 'Red')
    water_avail = request.args.get('water', 'Medium')

    villages = CropEntry.get_all_villages(db)
    
    # Dynamically fetch all 26 real districts
    d_rows = db.execute("SELECT name FROM districts ORDER BY name").fetchall()
    all_districts = [r[0] for r in d_rows]

    recommendations_data = get_recommendations(db, village, season, district, soil_type, water_avail)

    return render_template('recommend.html',
        village=village,
        season=season,
        district=district,
        soil_type=soil_type,
        water_avail=water_avail,
        villages=villages,
        seasons=Config.SEASONS,
        districts=all_districts,
        soil_types=Config.SOIL_TYPES,
        water_levels=Config.WATER_AVAILABILITY,
        recommendations=recommendations_data
    )


@crops_bp.route('/predict')
@login_required
def predict():
    db = get_db()
    crop = request.args.get('crop', 'Wheat')
    district = request.args.get('district', current_user.district)
    season = request.args.get('season', 'Kharif')

    historical, future_preds = get_price_trend(db, crop, district)
    single_price, err = predict_price(crop, season, datetime.datetime.now().year, district)

    d_rows = db.execute("SELECT name FROM districts ORDER BY name").fetchall()
    all_districts = [r[0] for r in d_rows]

    return render_template('predict.html',
        crops=Config.CROPS,
        seasons=Config.SEASONS,
        districts=all_districts,
        selected_crop=crop,
        selected_district=district,
        selected_season=season,
        historical=historical,
        future_preds=future_preds,
        single_price=single_price,
        predict_error=err
    )


@crops_bp.route('/train-model')
@login_required
def train():
    db = get_db()
    success, msg = train_model(db)
    flash(msg, 'success' if success else 'error')
    return redirect(url_for('dashboard.index'))
