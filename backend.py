from db import DBConnection

from zoneinfo import ZoneInfo

status_user = "Message Jar"


class AuthError(Exception):
    """Custom exception for authentication errors."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class NotAllowedError(Exception):
    """Custom exception for not allowed actions."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


def create_room(room_name, creator):
    """Create a new room with the given name and creator."""
    if member_count(room_name) > 0:
        raise NotAllowedError(f"Room {room_name} already exists.")
    add_to_room(room_name, creator, isadmin=1)
    add_to_room(room_name, status_user)
    notify(
        f'Room {room_name} created by {creator}. Commands: Use "/delete yes" to delete the room.\
              Use "/add user" to add a user. Use "/leave" to leave the room.',
        room_name,
    )


def notify(content, room):
    """Send a notification message to a room."""

    print(user_exists(status_user))
    print(get_rooms(status_user))

    print(f"Notifying room {room}: {content}")
    add_message(status_user, content, room)


def add_message(author, message, room, force=False):
    """Add a message to the database."""

    print(f"Adding message to room {room} from {author}: {message}")

    if not (force or room in get_rooms(author)):
        raise AuthError(f"User {author} is not a member of room {room}.")

    with DBConnection() as db:

        db.execute(
            "INSERT INTO messages (author, content, room) VALUES (?, ?, ?)",
            (author, message, room),
        )

        db.commit()

    if message.startswith("/"):
        command = message[1:].split(" ")[0]  # remove the leading slash
        args = " ".join(message[1:].split(" ")[1:])  # get everything after the command

        match command:
            case "add":  # add a user

                if user_exists(args):
                    add_to_room(room, args)
                    notify(f"{author} added user {args} to the room.", room)
                    return None  # all these return None statements are becuse adding two messages at once breaks the ordering
                else:
                    notify(f"User {args} does not exist!", room)
                    return None

            case "delete":  # delete room
                try:

                    delete_room(author, room)
                    notify(f"Room {room} has been deleted by admin {author}.", room)
                    return None
                except NotAllowedError:
                    notify(
                        f"User {author} is not an admin and cannot delete the room.",
                        room,
                    )
                    return None

            case "leave":  # leave room
                if is_admin(author, room):
                    notify(
                        f'Admin {author} cannot leave the room. Use "/delete yes" to delete the room.',
                        room,
                    )
                    return None
                else:
                    notify(f"User {author} has left the room.", room)

                    with DBConnection() as db:

                        db.execute(
                            """DELETE FROM rooms
                                    WHERE roomname = ? AND member = ?;""",
                            (room, author),
                        )
                        db.commit()

                    return None

            case "help":
                return None  # TODO implement help command

            case "remove":  # remove a user

                if author == args:
                    notify(
                        f'You cannot remove yourself! Use "/leave" to leave the room.',
                        room,
                    )
                    return None
                elif is_admin(args, room):
                    notify(
                        f"User {author} is an admin and cannot be removeed.",
                        room,
                    )
                    return None
                else:
                    notify(
                        f"User {args} has been removed from the room by {author}.", room
                    )

                    with DBConnection() as db:

                        db.execute(
                            """DELETE FROM rooms
                                    WHERE roomname = ? AND member = ?;""",
                            (room, args),
                        )
                        db.commit()

                    return None

            case _:
                return None  # not sure if this is needed


# Note: you may need to cripple this funcion if you alreay are in the EST timezone
def to_est(time):
    """Convert a datetime.datetime object to GMT time string."""
    r = time.astimezone(ZoneInfo("America/New_York"))
    return str(r)[:-6]


def delete_room(user, room):
    """Delete a room from the database."""
    if is_admin(user, room):

        with DBConnection() as db:

            db.execute(
                """DELETE FROM messages
                        WHERE room = ?;""",
                (room,),
            )

            db.commit()

    else:

        raise NotAllowedError(f"User {user} is not an admin of room {room}.")


def member_count(room):
    """duh"""

    with DBConnection() as db:
        r = db.execute(
            """SELECT COUNT(*) AS member_count
                    FROM rooms
                    WHERE roomname = ?;""",
            (room,),
        ).fetchone()

    return r[0]


def add_to_room(room_name, user, isadmin=0):
    """Add a user to a room.
    The way that the database is set up means that to add someone to a non-existent room
    means that the room will be created.
    """
    with DBConnection() as db:

        db.execute(
            "INSERT INTO rooms (roomname, member, isadmin) VALUES (?, ?, ?)",
            (room_name, user, isadmin),
        )
        db.commit()


def user_exists(user):
    """Check if a user exists in the database."""
    with DBConnection() as db:

        r = db.execute("SELECT * FROM user WHERE username = ?", (user,)).fetchone()
    if r is None:
        return False
    else:
        return True


def get_rooms(user):
    """Get a list of rooms that a user is a member of."""

    with DBConnection() as db:
        rooms = db.execute(
            """
        SELECT DISTINCT roomname
        FROM rooms
        WHERE member = ?;""",
            (user,),
        ).fetchall()

    rooms = [r["roomname"] for r in rooms]

    return rooms


def is_admin(user, room):
    """Check if a user is an admin of a room."""

    with DBConnection() as db:
        r = db.execute(
            """
        SELECT isadmin
        FROM rooms
        WHERE roomname = ? AND member = ?;""",
            (room, user),
        ).fetchone()

    if r and r["isadmin"] == 1:
        return True
    else:
        return False


def get_messages(room, message_num=0):
    """Get all the messages from a room and return them as a list.
    Use flask.jsonify(get_messages()) to return this as a page
    """

    query = """
        SELECT m.id, m.author, m.created, m.content
        FROM messages m
        JOIN user u ON m.author = u.username
        WHERE room = ?
        ORDER BY m.created ASC
    """

    data = []

    with DBConnection() as db:

        results = db.execute(query, (room,))
        row_headers = [x[0] for x in results.description]

        rv = results.fetchall()

    for result in rv:
        data.append(dict(zip(row_headers, result)))

    data.sort(key=lambda x: x["id"])

    for i in data:
        i["created"] = to_est(i["created"])

    return data[message_num:]
