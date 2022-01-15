from flask import Flask, redirect
from threading import Thread
import discord

app = Flask(__name__)

@app.route('/')
def home():
    return '''
<!doctype html>
<html>
    <head>
        <title> Senjibot </title>
        <meta property="og:title" content="Senjibot" />
        <meta property="og:description" content="Senjibot is a multipurpose bot that has economy system and editable guild-only shop" />
        <meta property="og:url" content="https://Senjibot.senjienji.repl.co" />
        <meta property="og:image" content="https://cdn.discordapp.com/avatars/922077126579060788/7c5bc15dcc776bcfe5af69ea7343ec34.png?size=1024" />
        <meta name="theme-color" content="#FFE5CE" data-react-helmet="true" />
    </head> <body>
        <h1> Senjibot </h1>
        <p> Senjibot is a multipurpose bot that has economy system and editable guild-only shop </p>
        <a href="https://github.com/Senjienji/Senjibot"> <img src="https://opengraph.githubassets.com/1/Senjienji/Senjibot" width="300" /> </a>
        <hr />
        <a href="https://Senjibot.senjienji.repl.co/invite"> Invite me! </a>
    </body>
</html>
    '''

@app.route('/invite')
def invite():
    return redirect(discord.utils.oauth_url(922077126579060788, permissions = discord.Permissions(
        manage_roles = True,
        kick_members = True,
        ban_members = True,
        read_messages = True,
        send_messages = True,
        manage_messages = True,
        embed_links = True,
        attach_files = True,
        read_message_history = True,
        add_reactions = True
    )))

def keep_alive():
    t = Thread(target = lambda: app.run(host = '0.0.0.0', port = 8080))
    t.start()