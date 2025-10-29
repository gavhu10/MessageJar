import os


import flask as f


def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
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

    # register the database commands
    import db

    db.init_app(app)

    # apply the blueprints to the app
    import auth
 

    app.register_blueprint(auth.bp)
 
    import chat

    app.register_blueprint(chat.chat)

    return app


app = create_app()