# Message Jar

A web app messaging application built with python and flask

![Message Jar logo](https://raw.githubusercontent.com/gavhu10/MessageJar/refs/heads/main/static/jar.svg)

## Installation

First, install flask with `pip install Flask`, preferably in a virtual environment. Then, run `flask init` to create the database and secret key. Now you can start Message Jar! If you are developing or debugging, start flask with
```
flask run --debug
```
Otherwise, use one of the options detailed by the flask documentation [here](https://flask.palletsprojects.com/en/stable/deploying/).


## API

On failure, the server returns an HTTP 4xx error with a JSON body `{"error": "Error message"}`.

### Create account

This endpoint takes a username and password arguments. It should return `{"status": "ok"}`. Here is an example curl request:

```bash
curl -d "username=user&password=pass123" http://127.0.0.1:5000/api/user/new
```

### Verify account

This is another username and password endpoint. It also should also return `{"status": "ok"}`

```bash
curl -d "username=user&password=pass123" http://127.0.0.1:5000/api/user/verify
```

### Generate token

This generates a token if the given username and password are valid. It returns 
```json
{"token": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"}
````

This is an example curl command for it:
```bash
curl -d "username=user&password=pass123&name=test" http://127.0.0.1:5000/api/user/generate
```

### List tokens

This endpoint lists the tokens for the user so that they can use them or revoke them.  
A request like this:

```bash
curl -d "username=user&password=pass123" http://127.0.0.1:5000/api/user/tokens
```
Should return something like this:

```json
[{"token":"”XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX","tokenname":"test"}]
```

### Verify token

This endpoint verifies the token and returns the associated username:

```bash
curl -d "token=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" http://127.0.0.1:5000/api/token/username
```

One response could look like this:

```json
{"username":"user"}
```

### Create room

This creates a room. The creator is automatically made the admin.
It should return the `{"status": "ok"}` response.
```bash
curl -d "token=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX&room=test" http://127.0.0.1:5000/api/rooms/create
```

### List rooms

This lists the user’s rooms and returns them as a json list. Here is an example request and the appropriate response:

```bash
curl -d "token=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" http://127.0.0.1:5000/api/rooms/list
```

```json
["lobby","test"]
```

### Send message

This endpoint is simple: it adds a specified message to the specified room. A command like this one sends a message “testing123” to the “test” room from the user who owns the api token. If it succeeds, it returns `{"status": "ok"}`.
```bash
curl -d "token=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX&room=test&message=testing123" http://127.0.0.1:5000/api/send
```


### Get messages

This api endpoint is for getting messages. 

```bash
curl -d "token=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX&room=test" http://127.0.0.1:5000/api/get
```
It should return something like this if the room has just been made and a message has been sent. The times are in EST. (note: the server assumes it is running in a UTC timezone.)
```json
[
  {
    "author": "Message Jar",
    "content": "Room test created by t. Commands: Use \"/delete yes\" to delete the room.              Use \"/add user\" to add a user. Use \"/leave\" to leave the room.",
    "created": "2035-12-25 15:39:40",
    "id": 1
  },
  {
    "author": "user",
    "content": "testing123",
    "created": "2035-12-25 15:41:40",
    "id": 2
  }
]
```

### Revoke token

This endpoint revokes the token used to make the request. To revoke a token that you do not have, you will have to have the username and password, and make a request from /api/user/tokens. It will return `{"status": "ok"}` on success.

```bash
curl -d "token=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX" http://127.0.0.1:5000/api/token/revoke
```

### Change password

This endpoint is for changing the user’s password. It also returns `{"status": "ok"}` on success.

```bash
curl -d "username=user&password=pass123&newpass=long and much more secure password194827349!" http://127.0.0.1:5000/api/user/changepass
```




## Todo  

 - [x] better css
 - [x] multiple rooms
 - [ ] create client for [cardputer](https://github.com/terremoth/awesome-m5stack-cardputer)
 - [x] optimize for mobile use

 [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Credit:  
  
Authentication and some database code from the [flaskr tutorial](https://github.com/pallets/flask/tree/3.1.2/examples/tutorial)  
Some inspireation and ideas from [a chat room by ClaudiasLibrary](https://github.com/ClaudiasLibrary/chat_room) and [ntfy](https://ntfy.sh)
