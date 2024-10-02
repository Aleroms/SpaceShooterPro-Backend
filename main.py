from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, relationship, mapped_column
from sqlalchemy import Integer, String, ForeignKey
from flask_bcrypt import Bcrypt

app = Flask(__name__)

# vars
SECRET_APIKEY = 'ssp2024unityv2'

class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///spaceShooterPro.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

class Users(db.Model):
    __tablename__ = "users_table"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(250), nullable=False)

# class Score(model_class=Base):
#     __tablename__ = "score_table"
#     id: Mapped[int] = mapped_column(Integer,primary_key=True, autoincrement=True)
#     user_id: Mapped[int] = mapped_column(ForeignKey("users_table.id"))
#     score: Mapped[int] = mapped_column(Integer, nullable=False)

with app.app_context():
    db.create_all()

    
@app.route('/')
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)