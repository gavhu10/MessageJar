from db import get_db, close_db

def add_message(author, content):
    db = get_db()

    db.execute("INSERT INTO messages (author, content) VALUES (?, ?)", (author, content))
    db.commit()

    close_db()



def get_messages(last_seen=0):
    db = get_db()

    latest = db.execute('SELECT MAX(id) AS latest_id FROM messages;').fetchone()['latest_id']
    if not latest: latest = 0

    
    if not last_seen:
        if int(latest) > 30:
            last_seen = latest - 30
    
    results = db.execute("""
        SELECT m.id, m.author, m.created, m.content
        FROM messages m
        JOIN user u ON m.author = u.username
        ORDER BY m.created ASC
    """)

    row_headers = [x[0] for x in results.description]

    json_data = []

    rv = results.fetchall()

    close_db()

    for result in rv:
        json_data.append(dict(zip(row_headers,result)))

    return json_data