import flask as f

from auth import check_user, register_user

import backend as cb
from backend import NotAllowedError, AuthError
from auth import RegistrationError

status_user = "Message Jar"

api = f.Blueprint("api", __name__, url_prefix="/api")


@api.route("/api-get", methods=["GET", "POST"])
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

        if not value:
            error = f"Missing argument: {key}"
            f.abort(400)

    try:
        check_user(args["username"], args["password"])
    except AuthError:
        f.abort(403)
    else:

        return f.jsonify(cb.get_messages(args["room"], latest))


@api.route("/api-send", methods=["POST", "GET"])
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
        if not value:
            error = f"Missing argument: {key}"
            f.abort(400)

    try:
        check_user(args["username"], args["password"])
    except AuthError:
        f.abort(403)

    rooms = cb.get_rooms(args["username"])
    if not args["room"] in rooms:
        f.abort(403)

    cb.add_message(args["username"], args["message"], args["room"])
    return "Message sent."


@api.route("/api-manage", methods=["GET", "POST"])
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

        if not value:
            error = f"Missing argument: {key}"
            f.abort(400)

    if args["action"] != "new_user":
        try:
            check_user(args["username"], args["password"])
        except AuthError:
            f.abort(403)

    match args["action"]:
        case "new_user":
            try:
                register_user(args["username"], args["password"])
            except RegistrationError:
                f.abort(403)
            return "User registered."
        case "new_room":
            try:
                cb.create_room(args["room"], args["username"])
            except NotAllowedError:
                f.abort(403)
            return "Room created."
        case "list_rooms":
            rooms = cb.get_rooms(args["username"])
            return f.jsonify(rooms)
        case "verify_user":
            try:
                check_user(args["username"], args["password"])
            except AuthError:
                f.abort(403)

            return "User verified."
        case "create_room":
            try:
                cb.create_room(args["room"], args["username"])
            except NotAllowedError:
                f.abort(403)
            return "Room created."
        case _:
            return "Error: Invalid action."
