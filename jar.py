import flask as f
from werkzeug.exceptions import BadRequestKeyError, abort

from auth import login_required

import backend as cb

status_user = "Message Jar"

jar = f.Blueprint("jar", __name__, url_prefix="/jar")


@jar.route("/")
@login_required
def index():
    return f.render_template(
        "jars/main.html", room_list=cb.get_rooms(f.g.user["username"])
    )


@jar.route("/new_room", methods=("GET", "POST"))
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
            new_location=f.url_for("jar.index"),
        )

    try:
        cb.create_room(room_name, f.g.user["username"])
    except cb.NotAllowedError as e:
        if cb.member_count(room_name) > 0:
            return f.render_template(
                "quick-error.html",
                error_message=e.message,
                new_location=f.url_for("jar.index"),
            )
    return f.redirect(f.url_for("jar.room", room_name=room_name))


@jar.route("/<room_name>")
def room(room_name):

    if cb.member_count(room_name) > 0:
        return f.render_template("jars/jar.html", room_name=room_name)
    else:
        abort(404)


@jar.route("/endpoint/<room_name>", methods=("GET", "POST"))
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
