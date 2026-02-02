import flask as f
import auth

import backend as cb
from backend import NotAllowedError, AuthError
from auth import RegistrationError


api = f.Blueprint("api", __name__, url_prefix="/api")


def get_kv(request, keys, optional=[]):
    r = {}

    for key in keys:
        r[key] = request.values.get(key)

        if key in optional:
            continue
        if r[key] is None:
            raise ValueError(f"Missing argument: {key}")

    return r


@api.route("/get", methods=["GET", "POST"])
def api_get():

    try:
        args = get_kv(f.request, ["token", "latest", "room"], ["latest"])
    except ValueError:
        f.abort(400)

    try:
        latest = int(args["latest"])
    except (ValueError, TypeError):
        latest = 0

    try:
        username = auth.check_valid_token(args["token"])
    except AuthError:
        f.abort(403)
    else:
        if username not in cb.get_room_members(args["room"]):
            f.abort(403)
        return f.jsonify(cb.get_messages(args["room"], latest))


@api.route("/send", methods=["POST", "GET"])
def api_send():

    try:
        args = get_kv(f.request, ["token", "message", "room"])
    except ValueError:
        f.abort(400)

    try:
        username = auth.check_valid_token(args["token"])
    except AuthError:
        f.abort(403)

    rooms = cb.get_rooms(username)
    if not args["room"] in rooms:
        f.abort(403)

    cb.add_message(username, args["message"], args["room"])
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
            return f.jsonify({"status": "ok"})
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
        case "new_user":
            try:
                auth.register_user(args["username"], args["password"])
            except RegistrationError:
                f.abort(403)
            return f.jsonify({"status": "ok"})
        case "list_tokens":
            return f.jsonify(cb.list_tokens(args["username"]))
        case "verify_user":
            try:
                auth.check_user(args["username"], args["password"])
            except AuthError:
                f.abort(403)

            return f.jsonify({"status": "ok"})
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
        case "get_username":
            return f.jsonify({"username": username})
        case "revoke_token":
            auth.revoke_api_token(args["token"])
            return f.jsonify({"status": "ok"})
        case _:
            f.abort(400)
