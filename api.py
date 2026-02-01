import flask as f
import user
import auth

import backend as cb
from backend import NotAllowedError, AuthError
from auth import RegistrationError

status_user = "Message Jar"

api = f.Blueprint("api", __name__, url_prefix="/api")


def get_kv(request, keys, optional=[]):
    r = {}

    for key in keys:
        r[key] = request.values.get(key)

        if key in optional:
            continue
        if key not in r or not r[key]:
            raise ValueError(f"Missing argument: {key}")

    return r


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
        auth.check_user(args["username"], args["password"])
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
        auth.check_user(args["username"], args["password"])
    except AuthError:
        f.abort(403)

    rooms = cb.get_rooms(args["username"])
    if not args["room"] in rooms:
        f.abort(403)

    cb.add_message(args["username"], args["message"], args["room"])
    return "OK"


@api.route("/manage/rooms", methods=["GET", "POST"])
def manage_rooms():
    try:
        args = get_kv(f.request, ["token", "action", "room"], ["room"])
    except ValueError:
        f.abort(400)

    try:
        username = auth.check_valid_token(args["token"])
    except AuthError:
        f.abort(403)

    match args["action"]:
        case "list_rooms":
            rooms = cb.get_rooms(username)
            return f.jsonify(rooms)
        
        case "create_room":
            try:
                cb.create_room(args["room"], username)
            except NotAllowedError:
                f.abort(403)
            return "OK"
        case _:
            f.abort(400)


@api.route("/manage/user", methods=["GET", "POST"])
def manage_user():
    try:
        args = get_kv(f.request, ["username", "password", "action", "name"], ["name"])
    except ValueError:
        f.abort(400)

    if args["action"] != "new_user":
        try:
            auth.check_user(args["username"], args["password"])
        except AuthError:
            f.abort(403)

    match args["action"]:
        case "get_username":
            try:
                return auth.check_valid_token(args["token"])
            except AuthError:
                f.abort(403)
        case "new_user":
            try:
                auth.register_user(args["username"], args["password"])
            except RegistrationError:
                f.abort(403)
            return "OK"
        case "verify_user":
            try:
                auth.check_user(args["username"], args["password"])
            except AuthError:
                f.abort(403)

            return "OK"
        case "generate_token":
            if args["name"]:
                return f.jsonify(
                    {"token": auth.generate_api_token(args["username"], args["name"])}
                )
            f.abort(400)
        case _:
            f.abort(400)


@api.route("/manage/token", methods=["GET", "POST"])
def manage_token():
    try:
        args = get_kv(f.request, ["token", "action", "name"], ["name"])
    except ValueError:
        f.abort(400)

    try:
        username = auth.check_valid_token(args["token"])
    except AuthError:
        f.abort(403)

    match args["action"]:
        case "list_tokens":
            return f.jsonify(cb.list_tokens(username))
        case "revoke_token":
            auth.revoke_api_token(args["token"])
            return "OK"
        case "get_token_by_name":
            if args["name"]:
                tokens = cb.list_tokens(username)
                token = [i for i in tokens if i["tokenname"] == args["name"]][0][
                    "token"
                ]
                if token:
                    return f.jsonify({"token": token})
                else:
                    f.abort(404)
            f.abort(400)
        case _:
            f.abort(400)
