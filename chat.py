from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask import jsonify
from werkzeug.exceptions import abort

from auth import login_required, check_user
from db import get_db

chat = Blueprint("chat", __name__, url_prefix='/chat')

def add_message(author_id, content):
    db = get_db()

    db.execute("INSERT INTO messages (author_id, content) VALUES (?, ?)", (author_id, content))
    db.commit()

    return db.lastrowid



def get_messages(last_seen=0):
    db = get_db()

    latest = db.execute('SELECT MAX(id) AS latest_id FROM messages;').fetchone()['latest_id']
    if not latest: latest = 0

    print(latest)
    
    if not last_seen:
        if int(latest) > 30:
            last_seen = latest - 30
    
    results = db.execute("""
        SELECT m.id, m.author_id, m.created, m.content
        FROM messages m
        JOIN user u ON m.author_id = u.id
        ORDER BY m.created ASC
    """).fetchall()

    return jsonify(results)


@chat.route('/')
@login_required
def index():
    return get_messages()
    


@chat.route("/api-get", methods=("GET", "POST"))
def api_get():

    username = request.form["username"]
    password = request.form["password"]
    message = request.form["message"]
    error = None

    if not message:
        error = "Title is required."

    error, user = check_user(username, password)

    if error is not None:
        return "Error"+str(error)
    else:

        return get_messages()


@chat.route("/api-send", methods=["POST"])
def send():
  
    username = request.form["username"]
    password = request.form["password"]
    message = request.form["message"]
    error = None

    if not message:
        error = "Title is required."

    error, user = check_user(username, password)

    if error is not None:
        return "Error"+str(error)
    else:
        
        add_message(user["id"], message)
        
        
        return redirect(url_for("chat.index"))


