import flask 
from threading import Thread
import discord

app = flask.Flask(__name__)

@app.route("/")
def home():
    return """
<!doctype html>
<html>
    <head>
        <title>Senjibot</title>
    </head>
    <body>
        <h1>WIP</h1>
    </body>
</html>
    """

@app.route("/invite")
def invite():
    return flask.redirect(discord.utils.oauth_url(929244105320570931, permissions = discord.Permissions(
        read_messages = True,
        send_messages = True,
        manage_messages = True,
        embed_links = True
    )))

def host():
    t = threading.Thread(target = lambda: app.run(host = "0.0.0.0", port = 8080))
    t.start()
