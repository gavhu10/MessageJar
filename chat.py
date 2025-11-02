import flask as f
from werkzeug.exceptions import BadRequestKeyError, abort

from auth import login_required, check_user

import chatbackend as cb

status_user = "Message Jar"

chat = f.Blueprint("chat", __name__, url_prefix="/chat")


@chat.route("/")
@login_required
def index():
    return f.render_template(
        "chat/main.html", room_list=cb.get_rooms(f.g.user["username"])
    )


@chat.route("/new_room", methods=("GET", "POST"))
@login_required
def new_room():

    try:
        room_name = f.request.form["room_name"]
    except BadRequestKeyError:
        room_name = None

    if not room_name:
        return f.render_template(
            "quick-error.html",
            error_message="Room name is required!",
            new_location=f.url_for("chat.index"),
        )

    if cb.member_count(room_name) > 0:
        return f.render_template(
            "quick-error.html",
            error_message="Room already exists!",
            new_location=f.url_for("chat.index"),
        )

    cb.add_to_room(room_name, f.g.user["username"], isadmin=1)
    cb.add_to_room(room_name, status_user)
    cb.notify(
        f'Room {room_name} created by {f.g.user['username']}. Commands: Use "/delete yes" to delete the room.\
              Use "/add user" to add a user. Use "/leave" to leave the room.',
        room_name,
    )
    return f.redirect(f.url_for("chat.room", room_name=room_name))


@chat.route("/room/<room_name>")
def room(room_name):

    if cb.member_count(room_name) > 0:
        return f.render_template("chat/chat.html", room_name=room_name)
    else:
        abort(404)


@chat.route("/endpoint/<room_name>", methods=("GET", "POST"))
@login_required
def endpoint(room_name):
    if cb.member_count(room_name) > 0:
        if f.request.method == "GET":

            try:
                latest = int(f.request.args.get("latest", 0))
            except (ValueError, TypeError):
                latest = 0

            return f.jsonify(cb.get_messages(room_name, latest))

        elif f.request.method == "POST":
            content = f.request.form["message"]
            cb.add_message(str(f.g.user["username"]), content, room_name)
            return "ok"


# ========== Note: API endpoints have not been tested; they may not work and they are unstable ==========


@chat.route("/api-get")
def api_get():

    username = f.request.args.get("username")
    password = f.request.args.get("password")
    room = f.requestargs.get("room")
    error = None

    try:
        latest = int(f.request.args.get("latest", 0))
    except (ValueError, TypeError):
        latest = 0

    if not room or not username or not password:
        error = "Missing arguments!"

    error, _ = check_user(username, password)

    if error is not None:
        return "Error" + str(error)
    else:

        return f.jsonify(cb.get_messages(room))


@chat.route("/api-send", methods=["POST"])
def send():

    username = f.request.form["username"]
    password = f.request.form["password"]
    message = f.request.form["message"]
    room = f.request.form["room"]
    error = None

    if not message:
        error = "No message!"

    error, user = check_user(username, password)

    if error is not None:
        return "Error " + str(error)
    else:

        cb.add_message(user["username"], message, room)
        return f.redirect(f.url_for("chat.index"))
