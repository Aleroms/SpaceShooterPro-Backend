import uuid
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String
from flask_bcrypt import Bcrypt
from functools import wraps

app = Flask(__name__)
bcrypt = Bcrypt(app)

# vars
SECRET_APIKEY = 'ssp2024unityv2'

class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///spaceShooterPro.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

class User(db.Model):
    __tablename__ = "users_table"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    session_token: Mapped[str] = mapped_column(String(36), unique=True, nullable=True)  # Add session_token column

with app.app_context():
    db.create_all()

def authenticate_user(username, password):
    user = User.query.filter_by(username=username).first()
    if user and bcrypt.check_password_hash(user.password, password):
        return user
    return None

def set_session_token(user):
    if user:
        session_token = str(uuid.uuid4())
        user.session_token = session_token
    return session_token


def authenticate_token(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        session_token = request.headers.get('Authorization')
        if not session_token:
            return jsonify(error="Session token missing")

        user = User.query.filter_by(session_token=session_token).first()  # Find user by session_token
        if not user:
            return jsonify(error="Invalid session token")

        # Store user in the request context for later use
        request.user = user
        return func(*args, **kwargs)
    return wrapper


# User Authentication and Management
@app.route('/login', methods=["POST"])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    user = authenticate_user(username, password)

    if user:
        st = set_session_token(user)
        db.session.commit()
        
        return jsonify(response={
        "success":"Successfully logged in",
        "session_token":st
        })
    else:
        return jsonify(error="Invalid username or password")
    
@app.route('/register',methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        return jsonify(error={"Missing Field": "Username and password are required"})
    
    users = User.query.all()
    if any(user.username == username for user in users):
        return jsonify(error={"Duplicate Entry": "User already exists"})
    
    pw_hash = bcrypt.generate_password_hash(password)
    session_token = str(uuid.uuid4())

    new_user = User(
        username=username,
        password=pw_hash,
        session_token=session_token
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify(response={
        "success":"Successfully added new user",
        "session_token":session_token
        })


@app.route('/delete_user', methods=['DELETE'])
@authenticate_token
def delete_user():
    # Access the authenticated user from the request context
    user = request.user
    name = user.username
    db.session.delete(user)
    db.session.commit()
    return jsonify(response={"success": f"successfully deleted {name}"})


@app.route('/logout', methods=['POST'])
@authenticate_token
def logout():
    user = request.user
    user.session_token = ""
    db.session.commit()
    return jsonify(response={"success":"successfully logged out"})

if __name__ == "__main__":
    app.run(debug=True)