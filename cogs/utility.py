import discord
from discord.ext import commands
from typing import Optional
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
    @commands.command()
    async def math(self, ctx, *, content):
        await ctx.reply(embed = discord.Embed(
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
            name = ctx.author,
            url = f'https://discord.com/users/{ctx.author.id}',
            icon_url = ctx.author.display_avatar.url
        ))
    
    @commands.command()
    async def embed(self, ctx, channel: Optional[discord.TextChannel], title, description, attachment: Optional[discord.Attachment]):
        if channel == None:
            channel = ctx.channel
        if not channel.permissions_for(ctx.author).send_messages:
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
            'author': ctx.author.id
        })
        await ctx.reply('Embed sent.')
    
    @commands.command(name = 'edit-embed')
    async def edit_embed(self, ctx, msg_id: int, channel: Optional[discord.TextChannel], title: Optional[str], description: Optional[str], attachment: Optional[discord.Attachment]):
        if channel == None:
            channel = ctx.channel
        message = await channel.fetch_message(msg_id)
        if message.author != ctx.me:
            return await ctx.reply('Not my message.')
        if message.embeds == []:
            return await ctx.reply('Embed not found.')
        
        doc = embed_col.find_one({'message': msg_id})
        if doc == None:
            doc = {
                'message': msg_id,
                'author': ctx.bot.owner_id
            }
            embed_col.insert_one(doc)
        if ctx.author.id not in (ctx.bot.owner_id, doc['author']):
            return await ctx.reply('Not your embed.')
        
        embed = message.embeds[0]
        if title:
            embed.title = title
        if description:
            embed.description = description
        if attachment:
            embed.set_image(url = attachment.url)
        await message.edit(embed = embed)
        await ctx.reply('Embed edited.')
    
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
    
    @commands.command()
    async def snipe(self, ctx, channel: Optional[discord.TextChannel]):
        if channel == None:
            channel = ctx.channel
        doc = snipe_col.find_one({'guild': ctx.guild.id})
        if doc == None or str(channel.id) not in doc['channels']:
            return await ctx.reply('Message not found.')
        
        fields = doc['channels'][str(channel.id)]
        author = ctx.guild.get_member(fields['author'])
        try:
            reference = await channel.fetch_message(fields['reference'])
        except discord.HTTPException:
            reference = None
        
        embed = discord.Embed(
            description = fields['content'],
            color = 0xffe5ce,
            timestamp = datetime.datetime.fromtimestamp(fields['created_at'])
        ).set_author(
            name = author,
            url = f'https://discord.com/users/{author.id}',
            icon_url = author.display_avatar.url
        )
        if reference:
            embed.description = '> ' + '\n> '.join(reference.content.split()) + f'\n{reference.author.mention} {embed.description}'
        await ctx.reply(embed = embed) 

async def setup(bot): 
    await bot.add_cog(Utility())
