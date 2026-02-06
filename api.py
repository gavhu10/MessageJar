from functools import wraps

import flask as f

import auth
import backend as cb
from auth import RegistrationError
from backend import AuthError, NotAllowedError

DEBUG = False

api = f.Blueprint("api", __name__, url_prefix="/api")


def token_required(func):
    """Decorator to require a valid API token for a view."""

    @wraps(func)
    def wrapper(**kwargs):
        token = f.request.values.get("token")

        if token is None:
            return missing_arg("token")

        try:
            username = auth.check_valid_token(token)
        except AuthError:
            return f.jsonify({"e": "Token not valid!"}), 401

        return func(username=username, **kwargs)

    return wrapper


def get_methods():
    if DEBUG:
        return ["GET", "POST"]

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


def missing_arg(arg=None):
    if arg is None:
        string = "Missing argument(s)!"
    else:
        string = f'Missing argument "{arg}"!'
    return f.jsonify({"e": string}), 400


@api.route("/get", methods=get_methods())
@token_required
def api_get(username):

    try:
        args = get_kv(f.request, ["latest", "room"], ["latest"])
    except ValueError:
        return missing_arg("room")

    try:
        latest = int(args["latest"])
    except (ValueError, TypeError):
        latest = 0

    if args["room"] not in cb.get_rooms(username):
        return f.jsonify({"e": "Not a member of this room!"}), 401
    return f.jsonify(cb.get_messages(args["room"], latest))


@api.route("/send", methods=get_methods())
@token_required
def api_send(username):

    try:
        args = get_kv(f.request, ["message", "room"])
    except ValueError:
        return missing_arg("room")

    rooms = cb.get_rooms(username)
    if args["room"] not in rooms:
        return f.jsonify({"e": "Not a member of this room!"}), 401

    cb.add_message(username, args["message"], args["room"])
    return f.jsonify({"status": "ok"})


@api.route("/rooms/<action>", methods=get_methods())
@token_required
def manage_rooms(username, action):
    try:
        args = get_kv(f.request, ["room"], ["room"])
    except ValueError:
        return missing_arg("room")

    match action:
        case "list":
            rooms = cb.get_rooms(username)
            return f.jsonify(rooms)
        case "create":
            if args["room"]:
                try:
                    cb.create_room(args["room"], username)
                except NotAllowedError as e:
                    return (
                        f.jsonify({"e": e.message}),
                        400,
                    )
                return f.jsonify({"status": "ok"})
            return missing_arg("room")
        case _:
            f.abort(404)


@api.route("/user/<action>", methods=get_methods())
def manage_user(action):
    try:
        args = get_kv(
            f.request, ["username", "password", "name", "newpass"], ["name", "newpass"]
        )
    except ValueError:
        return missing_arg()

    if action != "new":
        try:
            auth.check_user(args["username"], args["password"])
        except AuthError as e:
            return f.jsonify({"e": e.message})

    match action:
        case "new":
            try:
                auth.register_user(args["username"], args["password"])
            except RegistrationError as e:
                return f.jsonify({"e": e.message})
            return f.jsonify({"status": "ok"})
        case "tokens":
            return f.jsonify(cb.list_tokens(args["username"]))
        case "verify":
            return f.jsonify({"status": "ok"})
        case "generate":
            if args["name"]:
                try:
                    return f.jsonify(
                        {
                            "token": auth.generate_api_token(
                                args["username"], args["name"]
                            )
                        }
                    )
                except NotAllowedError as e:
                    return f.jsonify({"e": e.message}), 400
            return missing_arg("name")
        case "changepass":
            if args["newpass"]:
                auth.change_password(
                    args["username"], args["password"], args["newpass"]
                )
                return f.jsonify({"status": "ok"})
            return missing_arg("newpass")
        case _:
            f.abort(404)


@api.route("/token/<action>", methods=get_methods())
@token_required
def manage_token(username, action):
    try:
        args = get_kv(f.request, ["name", "token"], ["name"])
    except ValueError:
        return missing_arg("name")

    match action:
        case "username":
            return f.jsonify({"username": username})
        case "revoke":
            auth.revoke_api_token(args["token"])
            return f.jsonify({"status": "ok"})
        case _:
            f.abort(404)
