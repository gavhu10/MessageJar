import flask as f
import auth

import backend as cb
from backend import NotAllowedError, AuthError
from auth import RegistrationError
from functools import wraps

DEBUG = False

api = f.Blueprint("api", __name__, url_prefix="/api")


def token_required(func):
    """Decorator to require a valid API token for a view."""

    @wraps(func)
    def wrapper(**kwargs):
        token = f.request.values.get("token")

        if token is None:
            f.abort(400)

        try:
            username = auth.check_valid_token(token)
        except AuthError:
            f.abort(401)

        return func(username=username, **kwargs)

    return wrapper


def get_methods():
    if DEBUG:
        return ["GET", "POST"]
    else:
        return ["POST"]


def get_kv(request, keys, optional=None):
    optional = optional or []
    r = {}

    for key in keys:
        r[key] = request.values.get(key)

        if key in optional:
            continue
        if r[key] is None:
            raise ValueError(f"Missing argument: {key}")

    return r


@api.route("/get", methods=get_methods())
@token_required
def api_get(username):

    try:
        args = get_kv(f.request, ["latest", "room"], ["latest"])
    except ValueError:
        f.abort(400)

    try:
        latest = int(args["latest"])
    except (ValueError, TypeError):
        latest = 0

    if username not in cb.get_room_members(args["room"]):
        f.abort(403)
    return f.jsonify(cb.get_messages(args["room"], latest))


@api.route("/send", methods=get_methods())
@token_required
def api_send(username):

    try:
        args = get_kv(f.request, ["message", "room"])
    except ValueError:
        f.abort(400)

    rooms = cb.get_rooms(username)
    if not args["room"] in rooms:
        f.abort(403)

    cb.add_message(username, args["message"], args["room"])
    return f.jsonify({"status": "ok"})


@api.route("/rooms/<action>", methods=get_methods())
@token_required
def manage_rooms(username, action):
    try:
        args = get_kv(f.request, ["room"], ["room"])
    except ValueError:
        f.abort(400)

    match action:
        case "list":
            rooms = cb.get_rooms(username)
            return f.jsonify(rooms)
        case "create":
            try:
                cb.create_room(args["room"], username)
            except NotAllowedError:
                f.abort(403)
            return f.jsonify({"status": "ok"})
        case _:
            f.abort(404)


@api.route("/user/<action>", methods=get_methods())
def manage_user(action):
    try:
        args = get_kv(f.request, ["username", "password", "name", "newpass"], ["name", "newpass"])
    except ValueError:
        f.abort(400)

    if action != "new":
        try:
            auth.check_user(args["username"], args["password"])
        except AuthError:
            f.abort(403)

    match action:
        case "new":
            try:
                auth.register_user(args["username"], args["password"])
            except RegistrationError:
                f.abort(403)
            return f.jsonify({"status": "ok"})
        case "tokens":
            return f.jsonify(cb.list_tokens(args["username"]))
        case "verify":
            return f.jsonify({"status": "ok"})
        case "generate":
            if args["name"]:
                return f.jsonify(
                    {"token": auth.generate_api_token(args["username"], args["name"])}
                )
            f.abort(400)
        case "changepass":
            if args["newpass"]:
                auth.change_password(args["username"], args["password"], args["newpass"])
                return f.jsonify({"status": "ok"})
            f.abort(400)
        case _:
            f.abort(404)


@api.route("/token/<action>", methods=get_methods())
@token_required
def manage_token(username, action):
    try:
        args = get_kv(f.request, ["name"], ["name"])
    except ValueError:
        f.abort(400)

    match action:
        case "username":
            return f.jsonify({"username": username})
        case "revoke":
            auth.revoke_api_token(args["token"])
            return f.jsonify({"status": "ok"})
        case _:
            f.abort(404)
