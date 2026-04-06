from flask import Blueprint, jsonify, request
from db import get_db

locations_bp = Blueprint('locations', __name__)

@locations_bp.route('/districts')
def get_districts():
    db = get_db()
    rows = db.execute("SELECT name FROM districts ORDER BY name").fetchall()
    return jsonify([r[0] for r in rows])

@locations_bp.route('/mandals')
def get_mandals():
    db = get_db()
    district_name = request.args.get('district')
    if not district_name:
        return jsonify([])
    
    rows = db.execute("""
        SELECT m.name 
        FROM mandals m 
        JOIN districts d ON m.district_id = d.id 
        WHERE d.name = ? 
        ORDER BY m.name
    """, (district_name,)).fetchall()
    return jsonify([r[0] for r in rows])

@locations_bp.route('/villages')
def get_villages():
    db = get_db()
    district_name = request.args.get('district')
    mandal_name = request.args.get('mandal')
    
    if not district_name or not mandal_name:
        return jsonify([])
        
    rows = db.execute("""
        SELECT v.name 
        FROM villages v
        JOIN mandals m ON v.mandal_id = m.id
        JOIN districts d ON m.district_id = d.id
        WHERE d.name = ? AND m.name = ?
        ORDER BY v.name
    """, (district_name, mandal_name)).fetchall()
    return jsonify([r[0] for r in rows])
