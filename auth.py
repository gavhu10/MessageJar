import functools
import flask as f
from werkzeug.security import check_password_hash, generate_password_hash

import backend as cb
from db import DBConnection

status_user = "Message Jar"

bp = f.Blueprint("auth", __name__, url_prefix="/auth")


def login_required(view):
    """View decorator that redirects anonymous users to the login page."""

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if f.g.user is None:
            return f.redirect(f.url_for("auth.login"))

        return view(**kwargs)

    return wrapped_view


@bp.before_app_request
def load_logged_in_user():
    """If a user id is stored in the session, load the user object from
    the database into ``g.user``."""
    username = f.session.get("username")

    if not username:
        f.g.user = None
    else:
        with DBConnection() as db:
            f.g.user = db.execute(
                "SELECT * FROM user WHERE username = ?", (username,)
            ).fetchone()


@bp.route("/register", methods=("GET", "POST"))
def register():
    """Register a new user.

    Validates that the username is not already taken. Hashes the
    password for security.
    """
    if f.request.method == "POST":
        username = f.request.form["username"]
        password = f.request.form["password"]

        if not username:
            error = "Username is required."
        elif not password:
            error = "Password is required."

        error = register_user(username, password)

        if error is None:
            return f.redirect(f.url_for("auth.login"))

        f.flash(error)

    return f.render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    """Log in a registered user by adding the user id to the session."""
    if f.request.method == "POST":
        username = f.request.form["username"]
        password = f.request.form["password"]

        error, user = check_user(username, password)

        if error is None:
            # store the user id in a new session and return to the index
            f.session.clear()
            f.session["username"] = user["username"]
            return f.redirect(f.url_for("jar.index"))

        f.flash(error)

    return f.render_template("auth/login.html")


@bp.route("/logout")
def logout():
    """Clear the current session, including the stored user id."""
    f.session.clear()
    return f.redirect(f.url_for("jar.index"))


def register_user(username, password):
    """Register a new user programmatically.

    Validates that the username is not already taken. Hashes the
    password for security.
    """
    
    error = None

    if not username:
        error = "Username is required."
    elif not password:
        error = "Password is required."

    if error is None:
        with DBConnection() as db:
            try:
                db.execute(
                    "INSERT INTO user (username, password) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                db.commit()
            except db.IntegrityError:
                # The username was already taken, which caused the
                # commit to fail. Show a validation error.
                error = f"User {username} is already registered."
            else:
                cb.add_to_room("lobby", username)
                # Success
                return None

    return error


def check_user(user, password):
    """Check a user's credentials programmatically."""
    error = None

    with DBConnection() as db:
        r = db.execute("SELECT * FROM user WHERE username = ?", (user,)).fetchone()

    if r is None:
        error = "Incorrect username."
        r = ""
    elif not check_password_hash(r["password"], password):
        error = "Incorrect password."  # TODO security risk
        r = ""
    if user == status_user:
        error = "Nice try."
        r = ""

    return (error, r)
