# Message Jar

A web app messaging application built with python and flask

![Message Jar logo](https://raw.githubusercontent.com/gavhu10/MessageJar/refs/heads/main/static/jar.svg)

## Installation

First, install flask with `pip install Flask`, preferably in a virtual environment. Then, run `flask init` to create the database and secret key. Now you can start Message Jar! If you are developing or debugging, start flask with
```
flask run --debug
```
Otherwise, use one of the options detailed by the flask documentation [here](https://flask.palletsprojects.com/en/stable/deploying/).


## Todo  

 - [x] better css
 - [x] multiple rooms
 - [ ] create client for [cardputer](https://github.com/terremoth/awesome-m5stack-cardputer)
 - [x] optimize for mobile use

 [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Credit:  
  
Authentication and some data base code from the [flaskr tutorial](https://github.com/pallets/flask/tree/3.1.2/examples/tutorial)  
Some inspireation and ideas from [a chat room by ClaudiasLibrary](https://github.com/ClaudiasLibrary/chat_room) and [ntfy](https://ntfy.sh)
