import os
import sqlite3
from flask import Flask
from config import Config
from extensions import login_manager, bcrypt
from db import get_db, close_db
from flask_cors import CORS


def init_db():
    db = sqlite3.connect(Config.DATABASE)
    with open(os.path.join(os.path.dirname(__file__), 'database', 'schema.sql'), 'r') as f:
        db.executescript(f.read())
    db.commit()
    db.close()


def create_app():
    app = Flask(__name__)
    CORS(app, supports_credentials=True)
    app.config.from_object(Config)
    app.secret_key = Config.SECRET_KEY

    # Init extensions
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please login to access this page.'
    login_manager.login_message_category = 'info'
    bcrypt.init_app(app)

    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User
        db = sqlite3.connect(Config.DATABASE)
        db.row_factory = sqlite3.Row
        user = User.get_by_id(db, int(user_id))
        db.close()
        return user

    # Register blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.crops import crops_bp
    from routes.api import api_bp
    from routes.analytics import analytics_bp
    from routes.locations import locations_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(crops_bp, url_prefix='/crops')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')
    app.register_blueprint(locations_bp, url_prefix='/api/locations')

    # Teardown
    app.teardown_appcontext(close_db)

    # Initialize DB
    init_db()

    # Auto-train model on startup if DB has data
    with app.app_context():
        try:
            db = sqlite3.connect(Config.DATABASE)
            db.row_factory = sqlite3.Row
            count = db.execute("SELECT COUNT(*) FROM price_history").fetchone()[0]
            db.close()
            if count > 0:
                from services.ml_predictor import train_model
                _db = sqlite3.connect(Config.DATABASE)
                _db.row_factory = sqlite3.Row
                success, msg = train_model(_db)
                _db.close()
                print(f"[ML] {msg}")
        except Exception as e:
            print(f"[ML] Could not auto-train: {e}")

    return app


app = create_app()

if __name__ == '__main__':
    # Seed data if DB is empty
    db = sqlite3.connect(Config.DATABASE)
    count = db.execute("SELECT COUNT(*) FROM price_history").fetchone()[0]
    db.close()
    if count == 0:
        print("⚡ Seeding database with historical price data...")
        from database.seed_data import seed
        seed()

    print("🌱 Smart Crop Planning System starting on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
