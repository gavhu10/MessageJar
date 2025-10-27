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

import chatbackend as cb

chat = Blueprint("chat", __name__, url_prefix='/chat')





@chat.route('/')
@login_required
def index():
    return render_template("chat.html")
    

@chat.route("/endpoint", methods=("GET", "POST"))
@login_required
def endpoint():
    if request.method == 'GET':
        return jsonify(cb.get_messages())
    elif request.method == 'POST':
        content = request.form["message"]
        cb.add_message(str(g.user["username"]), content)
        return "ok"


@chat.route("/api-get")
def api_get():

    username = request.form["username"]
    password = request.form["password"]
    error = None

    error, user = check_user(username, password)

    if error is not None:
        return "Error"+str(error)
    else:

        return jsonify(cb.get_messages())


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
        
        cb.add_message(user["username"], message)
        return redirect(url_for("chat.index"))


