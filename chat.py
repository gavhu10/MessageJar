import flask as f
from werkzeug.exceptions import BadRequestKeyError, abort

from auth import login_required, check_user, register_user

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

    cb.create_room(room_name, f.g.user["username"])
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


@chat.route("/api-get", methods=["GET", "POST"])
def api_get():

    args = {
        "username": "",
        "password": "",
        "latest": "",
        "room": "",
    }

    optional = ["latest"]

    for key, value in args.items():
        if f.request.method == "POST":
            args[key] = f.request.form.get(key)
        elif f.request.method == "GET":
            args[key] = f.request.args.get(key)

    try:
        latest = int(args["latest"])
    except (ValueError, TypeError):
        latest = 0

    for key, value in args.items():

        if key in optional:
            continue

        print(f"{key}: {value}")
        print(f"stored: {key}: {args[key]}")
        if not value:
            error = f"Missing argument: {key}"
            return "Error: " + str(error)

    error, _ = check_user(args["username"], args["password"])

    if error is not None:
        return "Error: " + str(error)
    else:

        return f.jsonify(cb.get_messages(args["room"], latest))


@chat.route("/api-send", methods=["POST", "GET"])
def api_send():

    args = {
        "username": "",
        "password": "",
        "message": "",
        "room": "",
    }

    for key, value in args.items():
        if f.request.method == "POST":
            args[key] = f.request.form.get(key)
        elif f.request.method == "GET":
            args[key] = f.request.args.get(key)

    for key, value in args.items():
        print(f"{key}: {value}")
        if not value:
            error = f"Missing argument: {key}"
            return "Error: " + str(error)

    error, _ = check_user(args["username"], args["password"])

    rooms = cb.get_rooms(args["username"])

    if error is not None:
        return "Error: " + str(error)
    else:

        if args["username"] not in rooms:
            return "Error: User not in room."

        cb.add_message(args["username"], args["message"], args["room"])
        return f.redirect(f.url_for("chat.index"))


@chat.route("/api-manage", methods=["GET", "POST"])
def api_manage():
    args = {
        "username": "",
        "password": "",
        "action": "",
        "room": "",
    }

    optional = ["room"]

    for key, value in args.items():
        if f.request.method == "POST":
            args[key] = f.request.form.get(key)
        elif f.request.method == "GET":
            args[key] = f.request.args.get(key)

    
    for key, value in args.items():

        if key in optional:
            continue

        print(f"{key}: {value}")
        print(f"stored: {key}: {args[key]}")
        if not value:
            error = f"Missing argument: {key}"
            return "Error: " + str(error)
        
        match args["action"]:
            case "new_user":
                register_user(args["room"], args["username"])
            case "new_room":
                cb.create_room(args["room"], args["username"])
            case _:
                return "Error: Invalid action."