import flask as f
import auth
from backend import AuthError

user = f.Blueprint("user", __name__, url_prefix="/user")


@user.route("/")
def user_index():
    return f.redirect(f.url_for("user.pass_change"))


@user.route("/passchange", methods=("GET", "POST"))
def pass_change():
    """Change the password for a logged-in user."""
    if "username" not in f.session:
        return f.redirect(f.url_for("auth.login"))

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
