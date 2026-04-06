from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User
from db import get_db
from extensions import bcrypt

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        db = get_db()
        user = User.get_by_email(db, email)
        
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=request.form.get('remember'))
            flash('Welcome back, ' + user.username + '! 🌱', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash('Invalid email or password. Please try again.', 'error')
    
    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        village = request.form.get('village', '').strip()
        state = 'Andhra Pradesh'
        district = request.form.get('district', '').strip()
        mandal = request.form.get('mandal', '').strip()

        db = get_db()
        errors = []

        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        if not email or '@' not in email:
            errors.append('Invalid email address.')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm:
            errors.append('Passwords do not match.')
        if not village or not district or not mandal:
            errors.append('District, Mandal, and Village are required.')
        if User.get_by_email(db, email):
            errors.append('Email already registered.')
        if User.get_by_username(db, username):
            errors.append('Username already taken.')

        if errors:
            for e in errors:
                flash(e, 'error')
        else:
            pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')
            User.create(db, username, email, pw_hash, state, district, mandal, village)
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('auth.login'))

    from config import Config
    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
