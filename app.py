import logging
import os

import click
import flask as f

import api
import auth
import db
import jar
import user
from limiter import limiter

SCHEMA_VERSION = 3


@click.command("update")
def update_db_command():
    db.update_db(SCHEMA_VERSION)


@click.command("init")
def init_db_command():
    """Clear existing data and create new tables."""
    db.init_db()
    click.echo("Initialized the database.")
    auth.init_auth()


def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""

    logging.getLogger().setLevel(logging.INFO)
    app = f.Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        # a default secret that should be overridden by instance config
        SECRET_KEY="dev",
        # store the database in the instance folder
        DATABASE=os.path.join(app.instance_path, "db.sqlite"),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.update(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route("/")
    def main():
        return f.render_template("main.html")

    app.add_url_rule("/i", view_func=user.invite)

    db.init_app(app)

    app.cli.add_command(init_db_command)
    app.cli.add_command(update_db_command)

    app.register_blueprint(auth.bp)
    app.register_blueprint(jar.jar)
    app.register_blueprint(api.api)
    app.register_blueprint(user.user)

    limiter.init_app(app)

    return app


app = create_app()
