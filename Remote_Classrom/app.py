from flask import Flask, render_template, request, redirect, session, url_for
from flask_socketio import SocketIO, send
import sqlite3
import random
import string
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret"
socketio = SocketIO(app)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ---------------- DATABASE ---------------- #

def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT,
                 email TEXT,
                 password TEXT,
                 role TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS classes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 class_name TEXT,
                 class_code TEXT,
                 teacher_id INTEGER)''')

    c.execute('''CREATE TABLE IF NOT EXISTS attendance
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 student_id INTEGER,
                 class_id INTEGER,
                 join_time TEXT,
                 participation_score INTEGER)''')

    conn.commit()
    conn.close()

init_db()

# ---------------- ROUTES ---------------- #

@app.route("/")
def home():
    return redirect("/login")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("INSERT INTO users (name,email,password,role) VALUES (?,?,?,?)",
                  (name, email, password, role))
        conn.commit()
        conn.close()
        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=? AND password=?",
                  (email, password))
        user = c.fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]
            session["role"] = user[4]
            session["name"] = user[1]
            return redirect("/dashboard")

    return render_template("login.html")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    if request.method == "POST" and session["role"] == "teacher":
        class_name = request.form["class_name"]
        class_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        c.execute("INSERT INTO classes (class_name,class_code,teacher_id) VALUES (?,?,?)",
                  (class_name, class_code, session["user_id"]))
        conn.commit()

    c.execute("SELECT * FROM classes")
    classes = c.fetchall()
    conn.close()

    return render_template("dashboard.html", classes=classes)

@app.route("/classroom/<int:class_id>", methods=["GET", "POST"])
def classroom(class_id):
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    if session["role"] == "student":
        c.execute("INSERT INTO attendance (student_id,class_id,join_time,participation_score) VALUES (?,?,?,?)",
                  (session["user_id"], class_id, datetime.now(), 0))
        conn.commit()

    if request.method == "POST":
        file = request.files["file"]
        if file:
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], file.filename))

    c.execute("SELECT * FROM attendance WHERE class_id=? ORDER BY participation_score DESC", (class_id,))
    leaderboard = c.fetchall()
    conn.close()

    return render_template("classroom.html", class_id=class_id, leaderboard=leaderboard)

# ---------------- CHAT ---------------- #

@socketio.on("message")
def handle_message(msg):
    send(msg, broadcast=True)

if __name__ == "__main__":
    socketio.run(app, debug=True)
