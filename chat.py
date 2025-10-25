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
from db import get_db, close_db

chat = Blueprint("chat", __name__, url_prefix='/chat')

def add_message(author, content):
    db = get_db()

    db.execute("INSERT INTO messages (author, content) VALUES (?, ?)", (author, content))
    db.commit()

    close_db()




def get_messages(last_seen=0):
    db = get_db()

    latest = db.execute('SELECT MAX(id) AS latest_id FROM messages;').fetchone()['latest_id']
    if not latest: latest = 0

    print(latest)
    
    if not last_seen:
        if int(latest) > 30:
            last_seen = latest - 30
    
    results = db.execute("""
        SELECT m.id, m.author, m.created, m.content
        FROM messages m
        JOIN user u ON m.author = u.username
        ORDER BY m.created ASC
    """)

    row_headers = [x[0] for x in results.description]

    json_data = []

    rv = results.fetchall()

    close_db()

    for result in rv:
        json_data.append(dict(zip(row_headers,result)))
    return jsonify(json_data)



@chat.route('/')
@login_required
def index():
    add_message(g.user["username"], 'test')
    return render_template("chat.html")
    

@chat.route("/endpoint", methods=("GET", "POST"))
@login_required
def endpoint():
    if request.method == 'GET':
        return get_messages()
    elif request.method == 'POST':
        content = request.form["message"]
        add_message(str(g.user["username"]), content)


@chat.route("/api-get")
def api_get():

    username = request.form["username"]
    password = request.form["password"]
    error = None



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
        
        add_message(user["username"], message)
        return redirect(url_for("chat.index"))


