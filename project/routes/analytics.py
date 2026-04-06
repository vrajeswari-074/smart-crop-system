import datetime
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models.price_history import PriceHistory
from db import get_db

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/district')
@login_required
def district_analytics():
    db = get_db()
    
    # Query price history focusing on User's district
    district = current_user.district
    
    # Use pandas to easily aggregate 
    df = PriceHistory.get_all_as_df(db)
    
    district_data = {}
    
    if not df.empty:
        # Filter for current user's district
        df_dist = df[df['district'] == district]
        
        # Aggregate by year and crop
        if not df_dist.empty:
            yearly = df_dist.groupby(['year', 'crop_name'])['price_per_quintal'].mean().reset_index()
            
            # Format into Chart.js datasets format
            years = sorted([int(y) for y in df_dist['year'].unique()])
            crops = [str(c) for c in df_dist['crop_name'].unique()]
            
            datasets = []
            colors = ['#f87171', '#4ade80', '#60a5fa', '#facc15', '#c084fc', '#f472b6', '#fb923c', '#2dd4bf']
            
            for i, crop in enumerate(crops):
                crop_df = yearly[yearly['crop_name'] == crop]
                # Match years
                data = []
                for y in years:
                    match = crop_df[crop_df['year'] == y]
                    if not match.empty:
                        data.append(float(match.iloc[0]['price_per_quintal']))
                    else:
                        data.append(None)
                
                datasets.append({
                    'label': crop,
                    'data': data,
                    'borderColor': colors[i % len(colors)],
                    'backgroundColor': colors[i % len(colors)],
                    'tension': 0.3
                })
                
            district_data = {
                'labels': years,
                'datasets': datasets
            }
            
    return render_template('district_analytics.html', district=district, district_data=district_data)
