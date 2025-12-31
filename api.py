
import flask as f 

from auth import check_user, register_user

import backend as cb

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
        return f.redirect(f.url_for("jar.index"))


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
            return "Error: " + str(error)

    error, _ = check_user(args["username"], args["password"])
    if error is not None or args["action"] == "new_user":
        return "Error: " + str(error)

    match args["action"]:
        case "new_user":
            if register_user(args["room"], args["username"]) is not None:
                return "Error: User registration failed."
            return "User registered."
        case "new_room":
            cb.create_room(args["room"], args["username"])
        case "delete_room":
            cb.delete_room(args["room"], args["username"])
        case "list_rooms":
            rooms = cb.get_rooms(args["username"])
            return f.jsonify(rooms)
        case "verify_user":
            error, _ = check_user(args["username"], args["password"])
            if error is not None:
                return "Error: " + str(error)
            else:
                return "User verified."
        case "create_room":
            cb.create_room(args["room"], args["username"])
            return "Room created."
        case _:
            return "Error: Invalid action."
