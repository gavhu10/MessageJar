import flask as f
from werkzeug.exceptions import abort

import backend as cb
from auth import login_required

STATUS_USER = "Message Jar"

jar = f.Blueprint("jar", __name__, url_prefix="/jar")


@jar.route("/", methods=["GET", "POST"])
@login_required
def index():
    if f.request.method == "GET":
        return f.render_template(
            "jars/main.html", room_list=cb.get_rooms(f.g.user["username"])
        )

    error = None

    room_name = f.request.form.get("room_name")

    if not room_name:
        error = "Room name is required!"

    if error is None:
        try:
            cb.create_room(room_name, f.g.user["username"])
        except cb.NotAllowedError as e:
            error = e.message

    if error is None:
        return f.redirect(f.url_for("jar.room", room_name=room_name))

    f.flash(error)
    return f.render_template(
        "jars/main.html", room_list=cb.get_rooms(f.g.user["username"])
    )


@jar.route("/<room_name>")
@login_required
def room(room_name):

    if cb.member_count(room_name) > 0 and room_name in cb.get_rooms(
        f.g.user["username"]
    ):
        return f.render_template("jars/jar.html", room_name=room_name)
    abort(404)


@jar.route("/endpoint/<room_name>", methods=("GET", "POST"))
@login_required
def endpoint(room_name):
    if cb.member_count(room_name) > 0 and room_name in cb.get_rooms(
        f.g.user["username"]
    ):
        if f.request.method == "GET":
            try:
                latest = int(f.request.args.get("latest", 0))
            except (ValueError, TypeError):
                latest = 0

            return f.jsonify(cb.get_messages(room_name, latest))

        content = f.request.form["message"]
        cb.add_message(str(f.g.user["username"]), content, room_name)
        return "ok"
    f.abort(404)
