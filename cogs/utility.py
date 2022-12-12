import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import datetime
import pymongo
import os

client = pymongo.MongoClient(
    f'mongodb+srv://Senjienji:{os.environ["PASSWORD"]}@senjienji.czypcav.mongodb.net/?retryWrites=true&w=majority',
    server_api = pymongo.server_api.ServerApi('1'),
)
db = client.senjibot
snipe_col = db.snipe
embed_col = db.embed

class Utility(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
    
    @app_commands.command(description = 'Compiles math for you')
    @app_commands.describe(content = 'you get the point')
    async def math(self, inter, content: str):
        await inter.response.send_message(embed = discord.Embed(
            title = 'Result',
            description = discord.utils.escape_markdown(str(eval(content, {}, {i: None for i in (
                '__import__',
                'copyright',
                'credits',
                'license',
                'print',
                'input',
                'eval',
                'exec',
                'help',
                'exit',
                'quit',
                'open'
            )}))),
            color = 0xffe5ce
        ).set_author(
            name = inter.user,
            url = f'https://discord.com/users/{inter.user.id}',
            icon_url = inter.user.display_avatar.url
        ))
    
    @app_commands.command(description = 'Sends an embed')
    @app_commands.describe(
        title = "The embed's title",
        description = "The embed's description",
        attachment = 'An attachment to put inside the embed',
        channel = 'The channel to send the embed at\nRequires the `Send Messages` permission in that channel'
    )
    async def embed(self, inter, title: str, description: str, attachment: Optional[discord.Attachment], channel: Optional[discord.TextChannel]):
        if channel == None:
            channel = inter.channel
        if not channel.permissions_for(inter.user).send_messages:
            raise commands.MissingPermissions(['send_messages'])
        
        embed = discord.Embed(
            title = title,
            description = description,
            color = 0xffe5ce
        )
        if attachment:
            embed.set_image(url = attachment.url)
        message = await channel.send(embed = embed)
        embed_col.insert_one({
            'message': message.id,
            'author': inter.user.id
        })
        await inter.response.send_message('Embed sent.', ephemeral = True)
    
    @app_commands.command(
        name = 'edit-embed',
        description = 'Edits **YOUR** embed'
    )
    @app_commands.describe(
        msg_id = "The message's ID to edit the embed",
        title = "The embed's new title",
        description = "The embed's new description",
        attachment = 'A new attachment to put inside the embed',
        channel = 'The channel to fetch the message from',
    )
    async def edit_embed(self, inter, msg_id: int, title: Optional[str], description: Optional[str], attachment: Optional[discord.Asset], channel: Optional[discord.TextChannel]):
        if channel == None:
            channel = inter.channel
        message = await channel.fetch_message(msg_id)
        if message.author != inter.client.user:
            raise commands.BadArgument('Not my message.')
        if message.embeds == []:
            raise commands.BadArgument('Embed not found.')
        
        doc = embed_col.find_one({'message': msg_id})
        if doc == None:
            doc = {
                'message': msg_id,
                'author': self.bot.owner_id
            }
            embed_col.insert_one(doc)
        if inter.user.id != doc['author']:
            raise commands.CheckFailure('Not your embed.')
        
        embed = message.embeds[0]
        if title:
            embed.title = title
        if description:
            embed.description = description
        if attachment:
            embed.set_image(url = attachment.url)
        await message.edit(embed = embed)
        await inter.response.send_message('Embed edited.', ephemeral = True)
    
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        embed_col.delete_one({'message': message.id})
        if message.guild.id == None: return
        
        doc = snipe_col.find_one({'guild': message.guild.id})
        if doc == None:
            doc = {
                'guild': message.guild.id,
                'channels': {} #{channel.id: {}}
            }
            snipe_col.insert_one(doc)
        doc['channels'][str(message.channel.id)] = {
            'content': message.content,
            'author': message.author.id,
            'created_at': message.created_at.timestamp(),
            'reference': message.reference.message_id if message.reference else None
        }
        snipe_col.update_one(
            {'_id': doc['_id']},
            {'$set': {'channels': doc['channels']}}
        )
    
    @app_commands.command(description = 'Shows the latest deleted message')
    @app_commands.describe(channel = 'The channel to fetch the message from')
    async def snipe(self, inter, channel: Optional[discord.TextChannel]):
        if channel == None:
            channel = inter.channel
        doc = snipe_col.find_one({'guild': inter.guild_id})
        if doc == None or str(channel.id) not in doc['channels']:
            raise commands.ChannelNotFound(channel)
        
        fields = doc['channels'][str(channel.id)]
        author = self.bot.get_user(fields['author'])
        created_at = datetime.datetime.fromtimestamp(fields['created_at'])
        try:
            reference = await channel.fetch_message(fields['reference'])
        except discord.HTTPException:
            reference = None
        
        embed = discord.Embed(
            description = fields['content'],
            color = 0xffe5ce,
            timestamp = created_at
        )
        if reference:
            embed.description = f'> {(chr(10) + "> ").join(reference.content.split())}\n{reference.author.mention} {embed.description}'
        embed.set_author(
            name = author,
            url = f'https://discord.com/users/{author.id}',
            icon_url = author.display_avatar.url
        )
        await inter.response.send_message(embed = embed)

async def setup(bot): 
    await bot.add_cog(Utility(bot))
