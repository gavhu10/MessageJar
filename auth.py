import functools
import flask as f
from werkzeug.security import check_password_hash, generate_password_hash
import secrets

import backend as cb
from db import DBConnection
from backend import AuthError

status_user = "Message Jar"

bp = f.Blueprint("auth", __name__, url_prefix="/auth")


class RegistrationError(Exception):
    """Custom exception for registration errors."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


def init_auth():
    f.current_app.logger.info("Initializing authentication system.")
    with f.current_app.open_instance_resource("config.py", "w") as file:
        file.write(f'SECRET_KEY = "{secrets.token_hex()}"')


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
        error = None

        if not username:
            error = "Username is required."
        elif not password:
            error = "Password is required."

        if error is None:
            try:
                register_user(username, password)
            except RegistrationError as e:
                error = e.message

        if error is None:
            return f.redirect(f.url_for("auth.login"))
        else:
            f.flash(error)

    return f.render_template("auth/register.html")


@bp.route("/login", methods=("GET", "POST"))
def login():
    """Log in a registered user by adding the user id to the session."""
    if f.request.method == "POST":
        username = f.request.form["username"]
        password = f.request.form["password"]

        try:
            user = check_user(username, password)
        except AuthError as e:
            f.flash(e.message)
        else:
            # store the user id in a new session and return to the index
            f.session.clear()
            f.session["username"] = user["username"]
            return f.redirect(f.url_for("jar.index"))

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

    if not username:
        raise RegistrationError("Username is required.")
    elif not password:
        raise RegistrationError("Password is required.")

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
            raise RegistrationError(f"User {username} is already registered.")
        else:
            f.current_app.logger.info(f"Registered new user {username}")
            cb.add_to_room("lobby", username)
            # Success


def check_user(user, password):
    """Check a user's credentials programmatically."""

    with DBConnection() as db:
        r = db.execute("SELECT * FROM user WHERE username = ?", (user,)).fetchone()

    if r is None or not check_password_hash(r["password"], password):
        raise AuthError("Incorrect username or password.")
    if user == status_user:
        raise AuthError("Cannot log in as status user.")
        f.current_app.logger.warning(f"Attempt to log in as status user {status_user}")

    f.current_app.logger.info(f"User {user} logged in successfully.")
    return r


def change_password(username, old_password, new_password):
    """Change a user's password."""

    check_user(username, old_password)

    with DBConnection() as db:
        db.execute(
            "UPDATE user SET password = ? WHERE username = ?",
            (generate_password_hash(new_password), username),
        )
        db.commit()


def check_valid_token(token):
    with DBConnection() as db:
        r = db.execute(
            "SELECT username FROM apitokens WHERE token = ?", (token,)
        ).fetchone()

    if r is None:
        raise AuthError("Token not valid")
    else:
        return r[0]


def generate_api_token(username, name):
    """Generate an API token for a user."""

    token = secrets.token_urlsafe(32)
    with DBConnection() as db:
        db.execute(
            "INSERT INTO apitokens (username, token, tokenname) VALUES (?, ?, ?)",
            (username, token, name),
        )
        db.commit()
    f.current_app.logger.info(f"Generated API token for user {username}.")
    return token


def revoke_api_token(token):
    """Revoke an API token."""

    with DBConnection() as db:
        db.execute(
            "DELETE FROM apitokens WHERE token = ?",
            (token,),
        )
        db.commit()
    f.current_app.logger.info(f"Revoked API token.")
