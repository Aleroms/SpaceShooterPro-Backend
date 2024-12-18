import uuid
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String
from flask_bcrypt import Bcrypt
from functools import wraps
import os
from dotenv import load_dotenv



load_dotenv()

app = Flask(__name__)
bcrypt = Bcrypt(app)

# vars
SECRET_APIKEY = os.environ['SSP2024-APIKEY']

class Base(DeclarativeBase):
    pass

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['SSP2024Db']
db = SQLAlchemy(model_class=Base)
db.init_app(app)

class User(db.Model):
    __tablename__ = "users_table"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)
    highscore: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
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
            return jsonify(error={"message": "Session token missing"}), 400

        user = User.query.filter_by(session_token=session_token).first()  # Find user by session_token
        if not user:
            return jsonify(error={"message":"Invalid session token"}), 400

        # Store user in the request context for later use
        request.user = user
        return func(*args, **kwargs)
    return wrapper

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = "*"
    response.headers['Access-Control-Allow-Methods'] = "GET, OPTIONS, POST, DELETE"
    response.headers['Access-Control-Allow-Headers'] = "Content-Type"
    return response

# API Documentation
@app.route('/', methods=['GET'])
def home():
    return render_template('api_docs.html')


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
        }), 200
    else:
        return jsonify(error={"message": "Invalid username or password"}), 404
    
@app.route('/register',methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        return jsonify(error={"message": "Username and password are required"}), 400
    
    users = User.query.all()
    if any(user.username == username for user in users):
        return jsonify(error={"message": "User already exists"}), 400
    
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
        }), 201


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


# Game Logic
@app.route('/update_highscore', methods=['POST'])
@authenticate_token
def update_highscore():
    try:
        new_score = int(request.form.get('score'))
    except:
        return jsonify(error={"message":"there was an error with the score provided. Please check"}), 400

    user = request.user
    
    # check if new score > highscore
    if new_score > user.highscore:
        user.highscore = new_score
        db.session.commit()
        return jsonify(response={"success":"successfully updated the user's score"})
    
    return jsonify(error={"message": "score is not new high score"})

@app.route('/highscore', methods=['GET'])
def highscore():
    username = request.args.get('username')
    offset = request.args.get('offset',0, type=int)
    limit = request.args.get('limit',10, type=int)

    if limit <= 0:
        limit = 10  
    if offset <= 0:
        offset = 0


    if username:
        user = User.query.filter_by(username=username).first()
        if user:
            return jsonify(response={"username":username, "highscore":user.highscore})
        
        return jsonify(error={"message":"user does not exist"}), 404
    
    highscores_query = User.query.offset(offset).limit(limit)
    highscores = highscores_query

    highscore_list = [{"username":user.username, "highscore": user.highscore} for user in highscores]
    return jsonify(response={"highscores":highscore_list})



if __name__ == "__main__":
    app.run(debug=True)

