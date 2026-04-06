"""
Shared Flask extensions — initialized here to avoid circular imports.
"""
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

login_manager = LoginManager()
bcrypt = Bcrypt()
