from db import get_db, close_db

status_user = 'Message Jar'

def add_message(author, content, room, force=False):
    """Just comment"""

    messages = []
    if force or room in get_rooms(author):
        messages.append((author, content, room))
    else:
        return None
    

    if content.startswith('/'):
        command = content[1:].split(' ')[0] # remove the leading slash
        args = ' '.join(content[1:].split(' ')[1:]) # get everything after the command

        match command:
            case 'add': # add a user
                
                add_to_room(room, args)
                messages.append( (status_user, f"Added user {args} to the room.", room) )
            
            case 'delete': # delete room

                if not is_admin(author, room) or args != 'yes':
                    messages.append( (status_user, f"User {author} is not an admin and cannot delete the room.", room) )
                else:

                    messages.append( (status_user, f"Room {room} has been deleted by admin {author}.", room) )
                    db = get_db()

                    db.execute('''DELETE FROM rooms
                                WHERE roomname = ?;''',
                                (room,))
                    db.commit()
                    close_db()

            case 'leave': # leave room
                if is_admin(author, room):
                    messages.append( (status_user, f"Admin {author} cannot leave the room. Use \"/delete yes\" to delete the room", room) )
                else:
                    messages.append( (status_user, f"User {author} has left the room.", room) )
                    db = get_db()

                    db.execute('''DELETE FROM rooms
                                WHERE roomname = ? AND member = ?;''',
                                (room, author))
                    db.commit()
                    close_db()


    db = get_db()

    print(messages)

    db.executemany("INSERT INTO messages (author, content, room) VALUES (?, ?, ?)",
                messages)
    db.commit()

    close_db()

    print(content)


    
def member_count(room):
    """duh"""

    db = get_db()
    r = db.execute('''SELECT COUNT(*) AS member_count
                FROM rooms
                WHERE roomname = ?;''',
               (room,)).fetchone()
    
    return r[0]
    

def add_to_room(room_name, user, isadmin=0):
    """Add a user to a room.
    The way that the database is set up means that to add someone to a non-existent room 
    means that the room will be created. 
    """
    db = get_db()

    db.execute("INSERT INTO rooms (roomname, member, isadmin) VALUES (?, ?, ?)",
                (room_name, user, isadmin))
    db.commit()
    close_db()



def get_rooms(user):
    db = get_db()

    rooms = db.execute('''
    SELECT DISTINCT roomname
    FROM rooms
    WHERE member = ?;''', (user,)).fetchall()

    rooms = [r['roomname'] for r in rooms]

    return rooms


def is_admin(user, room):
    """Check if a user is an admin of a room."""
    db = get_db()

    r = db.execute('''
    SELECT isadmin
    FROM rooms
    WHERE roomname = ? AND member = ?;''',
    (room, user)).fetchone()

    close_db()

    if r and r['isadmin'] == 1:
        return True
    else:
        return False


def get_messages(room, last_seen=0):
    """Get all the messages from a room and return them as a list. 
    Use flask.jsonify(get_messages()) to return this as a  page
    """
    db = get_db()

    latest = db.execute('''
        SELECT MAX(id) 
        AS latest_id FROM messages 
        WHERE room = ?;''', 
        (room,)).fetchone()['latest_id']
    
    if not latest: latest = 0

    
    if not last_seen:
        if int(latest) > 30:
            last_seen = latest - 30
    
    results = db.execute("""
        SELECT m.id, m.author, m.created, m.content
        FROM messages m
        JOIN user u ON m.author = u.username
        WHERE room = ?
        ORDER BY m.created ASC
    """, (room,))

    row_headers = [x[0] for x in results.description]

    json_data = []

    rv = results.fetchall()

    close_db()

    for result in rv:
        json_data.append(dict(zip(row_headers,result)))

    return json_data