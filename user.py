import re
import secrets

import flask as f

import auth
import backend as cb
from backend import AuthError
from db import DBConnection

user = f.Blueprint("user", __name__, url_prefix="/user")


class InviteError(Exception):
    """Custom exception for invitation errors."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


@user.route("/")
@auth.login_required
def index():
    return f.render_template("user/main.html")


@user.route("/passchange", methods=["GET", "POST"])
@auth.login_required
def pass_change():
    """Change the password for a logged-in user."""

    if f.request.method == "POST":
        old_password = f.request.form["old_password"]
        new_password = f.request.form["new_password"]
        new_password_rep = f.request.form["new_password_rep"]
        error = None

        username = f.session["username"]

        if not new_password:
            error = "New password is required."
        elif new_password != new_password_rep:
            error = "Passwords must match."
        elif not re.match(r"^(?=.*[a-z])(?=.*\d).{8,}$", new_password):
            error = "Password must contain at least one number and one lowercase letter and be at least 8 characters"

        if error is None:
            try:
                auth.change_password(username, old_password, new_password)
                f.flash("Password successfully changed.")
                f.current_app.logger.info(f"User {username} changed their password.")
                return f.redirect(f.url_for("jar.index"))
            except AuthError:
                error = "Old password is incorrect."

        f.flash(error)

    return f.render_template("user/pass_change.html")


@user.route("/rmtoken", methods=["POST"])
@auth.login_required
def rmtoken():
    message = None

    token = f.request.form.get("token")

    if token is None:
        message = "Token is required!"
    else:
        try:
            if auth.check_valid_token(token) != f.g.user["username"]:
                raise AuthError
            auth.revoke_api_token(token)
        except AuthError:
            message = "Invalid token!"

    if message is None:
        message = "Token revoked."

    f.flash(message)
    return f.redirect(f.url_for("user.tokens"))


@user.route("/tokens", methods=["GET", "POST"])
@auth.login_required
def tokens():
    if f.request.method == "GET":
        return f.render_template(
            "user/token.html", token_list=cb.list_tokens(f.g.user["username"])
        )

    message = None

    token_name = f.request.form.get("token_name")

    if not token_name:
        message = "Token name is required!"

    if message is None:
        try:
            auth.generate_api_token(f.g.user["username"], token_name)
            message = "Token sucsessfully created."
        except auth.NotAllowedError as e:
            message = e.message

    f.flash(message)
    return f.redirect(f.url_for("user.tokens"))


def create_invite(username, room, name):
    """Create an invite and return the token. Raises InviteError on failure."""

    if room not in cb.get_rooms(username):
        raise InviteError("Invalid room!")

    if not name:
        raise InviteError("Empty usage name!")

    with DBConnection() as db:
        r = db.execute(
            "SELECT token FROM invitelinks WHERE username = ? AND invite_name = ?",
            (username, name),
        ).fetchone()

    if r is not None:
        raise InviteError(f'Link with name "{name}" already exists!')

    token = secrets.token_urlsafe(32)
    with DBConnection() as db:
        db.execute(
            "INSERT INTO invitelinks (username, token, room, invite_name) VALUES (?, ?, ?, ?)",
            (username, token, room, name),
        )
        db.commit()

    f.current_app.logger.info(f"Created invite for user {username} and room {room}.")
    return token


def remove_invite(token):
    """Delete an invite."""

    with DBConnection() as db:
        db.execute(
            "DELETE FROM invitelinks WHERE token = ?",
            (token,),
        )
        db.commit()


def list_invite(user):
    """List all API tokens for a user."""

    with DBConnection() as db:
        tokens = db.execute(
            """
        SELECT room, token, invite_name
        FROM invitelinks
        WHERE username = ?;""",
            (user,),
        ).fetchall()

    token_list = [
        {"invite_name": t["invite_name"], "token": t["token"], "room": t["room"]}
        for t in tokens
    ]

    return token_list


def invite_details(token):
    """Returns the room and inviting user for a token. Raises InviteError on failure"""

    with DBConnection() as db:
        r = db.execute(
            "SELECT room, username FROM invitelinks WHERE token = ?", (token,)
        ).fetchall()

    if r is None:
        raise InviteError("Invite not valid")

    return r[0]


@user.route("/rmlink", methods=["POST"])
@auth.login_required
def rmlink():
    message = None

    link = f.request.form.get("link")

    if link is None:
        message = "Link is required!"
    else:
        invites = list_invite(f.g.user["username"])
        # check that the user owns the key
        if any((i["token"] == link for i in invites)):
            remove_invite(link)
        else:
            message = "Invalid link!"

    if message is None:
        message = "Invite deleted"

    f.flash(message)
    return f.redirect(f.url_for("user.invite_page"))


@user.route("/invite", methods=["GET", "POST"])
@auth.login_required
def invite_page():
    if f.request.method == "GET":
        return f.render_template(
            "user/invite.html",
            invite_links=list_invite(f.g.user["username"]),
            room_list=cb.get_rooms(f.g.user["username"]),
        )

    message = None

    room = f.request.form.get("room")
    name = f.request.form.get("invite_name")

    if not name:
        message = "Name is required!"

    if not room:
        message = "Room is required!"

    try:
        if not message:
            create_invite(f.g.user["username"], room, name)
            message = "Invite sucsessfully created."
    except InviteError as e:
        message = e.message

    f.flash(message)
    return f.redirect(f.url_for("user.invite_page"))


@auth.login_required("You must be logged in to accept an invite.")
def invite():
    token = f.request.args.get("token")

    try:
        room, link_owner = invite_details(token)

        if not cb.list_users(room):
            raise InviteError("Room does not exist. It may have been deleted.")

        if room not in cb.get_rooms(f.g.user["username"]):
            cb.add_to_room(room, f.g.user["username"])
            cb.notify(
                f"User {f.g.user['username']} added to room by {link_owner}", room
            )

    except InviteError as e:
        return e.message, 400

    return f.redirect(f.url_for("jar.room", room_name=room))
