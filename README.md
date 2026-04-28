# Message Jar

A messaging web application built with Python and Flask

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

![Message Jar logo](https://raw.githubusercontent.com/gavhu10/MessageJar/refs/heads/main/static/jar.svg)

## Usage and features

Message Jar has many features, some of which might hopfully be useful to you. You can create and manage rooms, access <u>everything</u> from the API and use invite links. If you want to see your jars, click on the logo. That will bring you to a page where you can click on your jar’s names to enter them or create more jars. You can edit your user settings by clicking your username at the top of the page. There you can create invite links, API tokens, and change your password. When you want to log out, just click the button.

## Installation

You can access an online instance [here](https://messagejar.pythonanywhere.com)!

If you want to use docker to serve Message Jar with gunicorn, run

```bash
docker compose up
```

You can also do it manually if you want.
To do that, first install the dependencies with 

```bash
uv sync
```

Then, run `flask init` to create the database and secret key. Now you can start Message Jar! If you are developing or debugging, start flask with

```bash
flask run --debug
```

Otherwise, use one of the options detailed by the flask documentation [here](https://flask.palletsprojects.com/en/stable/deploying/).

If your database no longer has the right schema, run `flask update`. It will not modify anything if you are up to date.

> [!NOTE]
> You must also create a room named "logs".
> The first user to do so will have access to all of the logged messages.

## Slash commands

Slash commands are how you manage your rooms (or jars). To use them, send them like a normal message.

Send the `/help` command to print this message.
Use `/add my_friend` to add user "my_friend". The `/remove` command is remarkable similar, although it accomplishes the inverse operation.
To use it, send the message `/remove not_my_friend` to remove the user "not_my_friend".
You can leave a room by sending the `/leave` command, although if you created the room, you will have to delete the room instead.
This is done by sending the `/delete` command. But be careful: there is no recovering lost rooms.
To empty a room, send the `/clear` command. Just like the `/delete` command, only admins can perform this action.
A reload may be necessary for the `/leave`, `/delete`, `/clear`, and `/remove` commands, due to how the html client works.
To make someone an admin or remove someones admin status, you will have to be an admin.
Then you can use the `/add-admin` and `/remove-admin` commands.


## Invite links

To create an invite link, click on your username to access your user settings. Then navigate to “Your invite links”. There you can create a link for any of the rooms you are a part of, including a small message to remind yourself who and what the link is for. Then hit "Create Invite Link"! You can get the link for further use by right-clicking the message you put in and selecting “Copy Link”.

If you want to use an invite link, just click it. It will add you to the proper room.


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

### Test username

This enpoint is at `/api/v1/user/exists` has a single parameter named username. It checks if the username is valid. This is so that applications can tell if they can log in or if they need to create an account.

### Create account

This endpoint, which is at `/api/v1/user/new`, takes your username and password. It should return `{"status": "ok"}`. Here is an example curl request:

```bash
curl --json '{"username":"user", "password":"pass123"}' http://127.0.0.1:5000/api/v1/user/new
```

### Verify account

This is another username and password endpoint. It should also return `{"status": "ok"}`. The endpoint is at `/api/v1/user/verify` and accepts json data with a username and password field.

### Generate token

This generates a token if the given username and password are valid. It returns 
```json
{"token": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"}
```

The request should be posted to `/api/v1/user/generate` and it too only uses a username and password field.


### List tokens

This endpoint lists the tokens for the user so that they can use them or revoke them.  
It is a username and password endpoint, and requests with valid credentials sent to `/api/v1/user/tokens` should return something like this:

```json
[
  {
    "token": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    "tokenname": "test",
  }
]
```

### Verify token

This endpoint verifies the token and returns the associated username. It is at `/api/v1/token/username` and takes JSON with the field `token`.


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
POSTed to `/api/v1/rooms/create` should return the `{"status": "ok"}` response. Add other people to talk to with the slash commands. (see above)

### List rooms

This lists the user's rooms and returns them as a JSON list. Here is an example request and the appropriate response:

```bash
curl --json '{"token":"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"}' http://127.0.0.1:5000/api/v1/rooms/list
```

```json
["lobby","test"]
```

## Create invite

The api does not deal with invite links, but instead tokens, which is the the part after `/i?token=` in an invite link. To create an invite token, use the `/api/v1/rooms/create_invite`. You need to send along your access token and a usage message under the name `"invite_message"` and if all goes well it responds with something like this:

```json
{
  "token": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
}
```


## Accept invite

If you want to accept an invite use the `/api/v1/rooms/join` endpoint. Send your access token and your invite token like so:

```json
{
  "token": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "invite_token": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
}
```

The server will put you into the proper jar and return the room under the (aptly named) "room" json key.


### Send message

This endpoint, which is at `/api/v1/send` is simple: it adds a specified message to the specified room. Something like this this sends a message “testing123” to the “test” room from the user who owns the api token. If it succeeds, it returns `{"status": "ok"}`.

```json
{
  "token": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  "room": "my room",
  "message": "Hello World!",
}
```


### Get messages

This api endpoint is for getting messages and it is at `/api/v1/get`. The latest parameter is optional. It specifies the id of the last message that the client got.
It is intended to reduce network traffic.


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

This endpoint, which is at `/api/v1/token/revoke`, revokes the token used to make the request. To revoke a token that you do not have, you will have to have the username and password, and make a request to `/api/v1/user/tokens`. It will return `{"status": "ok"}` on success.

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






## Credit
  
Authentication and some database code from the [flaskr tutorial](https://github.com/pallets/flask/tree/3.1.2/examples/tutorial)  
Some inspiration and ideas from [a chat room by ClaudiasLibrary](https://github.com/ClaudiasLibrary/chat_room) and [ntfy](https://ntfy.sh)
