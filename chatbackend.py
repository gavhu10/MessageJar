from db import get_db, close_db

from datetime import datetime
from zoneinfo import ZoneInfo

status_user = "Message Jar"


def notify(content, room):
    """Send a notification message to a room."""

    print(user_exists(status_user))
    print(get_rooms(status_user))

    print(f"Notifying room {room}: {content}")
    add_message(status_user, content, room)


def add_message(author, content, room, force=False):
    """Just comment"""

    print(f"Adding message to room {room} from {author}: {content}")

    if not (force or room in get_rooms(author)):
        return None

    if content.startswith("/"):
        command = content[1:].split(" ")[0]  # remove the leading slash
        args = " ".join(content[1:].split(" ")[1:])  # get everything after the command

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

                if not is_admin(author, room) or args != "yes":
                    notify(
                        f"User {author} is not an admin and cannot delete the room.",
                        room,
                    )
                    return None
                else:

                    notify(f"Room {room} has been deleted by admin {author}.", room)
                    db = get_db()

                    db.execute(
                        """DELETE FROM rooms
                                WHERE roomname = ?;""",
                        (room,),
                    )
                    db.commit()
                    close_db()

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

                    db = get_db()

                    db.execute(
                        """DELETE FROM rooms
                                WHERE roomname = ? AND member = ?;""",
                        (room, author),
                    )
                    db.commit()
                    close_db()
                    return None

    db = get_db()

    db.execute(
        "INSERT INTO messages (author, content, room) VALUES (?, ?, ?)",
        (author, content, room),
    )

    db.commit()

    close_db()

    print(content)


# Note: you may need to cripple this funcion if you alreay are in the EST timezone
def to_est(time):
    """Convert a datetime.datetime object to GMT time string."""
    r = time.astimezone(ZoneInfo("America/New_York"))
    return str(r)[:-6]


def member_count(room):
    """duh"""

    db = get_db()
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
    db = get_db()

    db.execute(
        "INSERT INTO rooms (roomname, member, isadmin) VALUES (?, ?, ?)",
        (room_name, user, isadmin),
    )
    db.commit()
    close_db()


def user_exists(user):
    """Check if a user exists in the database."""
    db = get_db()

    r = db.execute("SELECT * FROM user WHERE username = ?", (user,)).fetchone()

    close_db()

    if r is None:
        return False
    else:
        return True


def get_rooms(user):
    db = get_db()

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
    db = get_db()

    r = db.execute(
        """
    SELECT isadmin
    FROM rooms
    WHERE roomname = ? AND member = ?;""",
        (room, user),
    ).fetchone()

    close_db()

    if r and r["isadmin"] == 1:
        return True
    else:
        return False


def get_messages(room, message_num=0):
    """Get all the messages from a room and return them as a list.
    Use flask.jsonify(get_messages()) to return this as a page
    """
    db = get_db()


    query = """
        SELECT m.id, m.author, m.created, m.content
        FROM messages m
        JOIN user u ON m.author = u.username
        WHERE room = ?
        ORDER BY m.created ASC
    """

    data = []

    results = db.execute(query, (room,))
    row_headers = [x[0] for x in results.description]

    rv = results.fetchall()
    close_db()

    for result in rv:
        data.append(dict(zip(row_headers, result)))

    data.sort(key=lambda x: x["id"], reverse=True)

    for i in data:
        i["created"] = to_est(i["created"])

    for i in range(0, len(data)):
        data[i]["id"] = i

    message_num = len(data) - (message_num + 1)

    print("Returning " + str(message_num + 1) + " messages.")

    return data[: message_num + 1]
