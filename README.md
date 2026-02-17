# Message Jar

A messaging web application built with Python and Flask

![Message Jar logo](https://raw.githubusercontent.com/gavhu10/MessageJar/refs/heads/main/static/jar.svg)

## Installation

You can access an online instance [here](https://messagejar.pythonanywhere.com)!

First, install the dependencies with `pip install -r requirements.txt`, preferably in a virtual environment. Then, run `flask init` to create the database and secret key. Now you can start Message Jar! If you are developing or debugging, start flask with

```
flask run --debug
```

Otherwise, use one of the options detailed by the flask documentation [here](https://flask.palletsprojects.com/en/stable/deploying/).

## Slash commands

Slash commands are how you manage your rooms (or jars). To use them, send them like a normal message.

Send the `/help` command to print this message. Use `/add my_friend` to add user "my_friend". The `/remove` command is remarkable similar, although it accomplishes the inverse operation. To use it, send the message `/remove not_my_friend` to remove the user "not_my_friend". You can leave a room by sending the `/leave` command, although if you created the room, you will have to delete the room instead. This is done by sending the `/delete` command. (you will have to reload to see the effects.) But be careful: there is no recovering lost rooms.


<details>

<summary>API Specification</summary>

## API Specification

Each endpoint takes JSON POST data. On failure, the server returns an HTTP 4xx error with a JSON body `{"e": "Error message"}`. Endpoints that take tokens use the form
```json
{
  "token": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  // Other data
}
```
whereas endpoints that use your username and password use the form 
```json
{
  "username": "user",
  "password": "pass123",
  // Other data
}
```

### Create account

This endpoint, which is at `/api/user/new`, takes your username and password. It should return `{"status": "ok"}`. Here is an example curl request:

```bash
curl --json '{"username":"user", "password":"pass123"}' http://127.0.0.1:5000/api/user/new
```

### Verify account

This is another username and password endpoint. It should also return `{"status": "ok"}`. The endpoint is at `/api/user/verify` and accepts json data with a username and password field.

### Generate token

This generates a token if the given username and password are valid. It returns 
```json
{"token": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"}
```

The request should be posted to `/api/user/generate` and it too only uses a username and password field.


### List tokens

This endpoint lists the tokens for the user so that they can use them or revoke them.  
It is a username and password endpoint, and requests with valid credentials sent to `/api/user/tokens` should return something like this:

```json
[
  {
    "token": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "tokenname": "test",
  }
]
```

### Verify token

This endpoint verifies the token and returns the associated username. It is at `/api/token/username` and takes JSON with the field `token`.


One response could look like this:

```json
{
  "username": "user"
}
```

### Create room

This creates a room. The creator is automatically made the admin. JSON data like this
```json
{
  "token": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "room": "my room"
}
```
POSTed to `/api/rooms/create` should return the `{"status": "ok"}` response.

### List rooms

This lists the user's rooms and returns them as a JSON list. Here is an example request and the appropriate response:

```bash
curl --json '{"token":"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"}' http://127.0.0.1:5000/api/rooms/list
```

```json
["lobby","test"]
```

### Send message

This endpoint, which is at `/api/send` is simple: it adds a specified message to the specified room. Something like this this sends a message “testing123” to the “test” room from the user who owns the api token. If it succeeds, it returns `{"status": "ok"}`.

```json
{
  "token": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "room": "my room",
  "message": "Hello World!",
}
```


### Get messages

This api endpoint is for getting messages and it is at `/api/get`.


```json
{
  "token": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "room": "my room",
}
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

This endpoint, which is at `/api/token/revoke`, revokes the token used to make the request. To revoke a token that you do not have, you will have to have the username and password, and make a request to `/api/user/tokens`. It will return `{"status": "ok"}` on success.

### Change password

This endpoint is for changing the user's password. It also returns `{"status": "ok"}` on success.

```json
{
  "username": "user",
  "password": "pass123",
  "newpass": "long and much more secure password194827349!",
}
```
</details>



## Todo  

 - [x] better css
 - [x] multiple rooms
 - [ ] create client for [cardputer](https://github.com/terremoth/awesome-m5stack-cardputer)
 - [x] optimize for mobile use

 [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Credit:  
  
Authentication and some database code from the [flaskr tutorial](https://github.com/pallets/flask/tree/3.1.2/examples/tutorial)  
Some inspiration and ideas from [a chat room by ClaudiasLibrary](https://github.com/ClaudiasLibrary/chat_room) and [ntfy](https://ntfy.sh)
