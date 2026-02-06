import flask as f
import backend as cb
import auth
from backend import AuthError

user = f.Blueprint("user", __name__, url_prefix="/user")


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
        error = None

        username = f.session["username"]

        if not new_password:
            error = "New password is required."

        try:
            auth.change_password(username, old_password, new_password)
            f.flash("Password successfully changed.")
            f.current_app.logger.info(f"User {username} changed their password.")
            return f.redirect(f.url_for("jar.index"))
        except AuthError:
            error = "Old password is incorrect."

        f.flash(error)

    return f.render_template("user/pass_change.html")


@user.route("/rmtoken")
@auth.login_required
def rmtoken():
    message = None

    token = f.request.args.get("token")

    if token is None:
        message = "Token is required!"
    else:
        try:
            if auth.check_valid_token(token) != f.g.user["username"]:
                raise AuthError
            else:
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
