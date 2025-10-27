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
    return render_template("chat_main.html")
    


@chat.route("/room/<room_name>")
def room(room_name):

    if cb.member_count(room_name) > 0:
        return render_template("chat.html", room_name=room_name)

@chat.route("/endpoint/<room_name>", methods=("GET", "POST"))
@login_required
def endpoint(room_name):
    if cb.member_count(room_name) > 0:
        if request.method == 'GET':
            return jsonify(cb.get_messages(room_name))
        elif request.method == 'POST':
            content = request.form["message"]
            cb.add_message(str(g.user["username"]), content, room_name)
            return "ok"
    
    return jsonify("no such room")


@chat.route("/api-get")
def api_get():

    username = request.form["username"]
    password = request.form["password"]
    room = request.form["room"]
    error = None

    error, _ = check_user(username, password)

    if error is not None:
        return "Error"+str(error)
    else:

        return jsonify(cb.get_messages(room))


@chat.route("/api-send", methods=["POST"])
def send():
  
    username = request.form["username"]
    password = request.form["password"]
    message = request.form["message"]
    room = request.form["room"]
    error = None

    if not message:
        error = "No message!"

    error, user = check_user(username, password)

    if error is not None:
        return "Error "+str(error)
    else:
        
        cb.add_message(user["username"], message, room)
        return redirect(url_for("chat.index"))


