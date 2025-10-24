from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask import jsonify
from werkzeug.exceptions import abort

from auth import login_required
from db import get_db

chat = Blueprint("chat", __name__, url_prefix='/chat')

def add_message(conn, author_id, content):
    cur = conn.cursor()
    cur.execute("INSERT INTO messages (author_id, content) VALUES (?, ?)", (author_id, content))
    conn.commit()
    return cur.lastrowid


@chat.route("/api-get")
def api_get():

    print("g.user = "+str(g.user))

    print('am here')
    last = 0
    #last = request.form['last']
    db = get_db()
    latest = db.execute('SELECT MAX(id) AS latest_id FROM messages;').fetchone()['latest_id']

    print(latest)
    if not latest: latest = 0
    if not last:
        if int(latest) > 30:
            last = latest - 30
    
    results = db.execute("""
        SELECT m.id, m.author_id, m.created, m.content
        FROM messages m
        JOIN user u ON m.author_id = u.id
        ORDER BY m.created ASC
    """).fetchall()
    return jsonify(results)



    
    # posts = db.execute(
    #     "SELECT p.id, title, body, created, author_id, username"
    #     " FROM post p JOIN user u ON p.author_id = u.id"
    #     " ORDER BY created DESC"
    # ).fetchall()
    # print(posts)
    #return render_template("blog/index.html", posts=posts)
    print("g.user = "+g.user)


@chat.route("/api-send", methods=("GET", "POST"))
@login_required
def send():
  
    if request.method == "POST":
        message = request.form["message"]
        error = None

        if not message:
            error = "Title is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "INSERT INTO messages (content, author_id) VALUES (?, ?)",
                (message, g.user["id"]),
            )
            db.commit()
            return redirect(url_for("index"))

    return redirect(url_for("index"))

