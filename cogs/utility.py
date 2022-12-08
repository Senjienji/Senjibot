import discord
from discord.ext import commands
import datetime
import pymongo
import os

client = pymongo.MongoClient(
    f'mongodb+srv://Senjienji:{os.environ["PASSWORD"]}@senjienji.czypcav.mongodb.net/?retryWrites=true&w=majority',
    server_api = pymongo.server_api.ServerApi('1'),
)
db = client.senjibot
snipe_col = db.snipe

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
        ).set_footer(
            text = ctx.author.display_name,
            icon_url = ctx.author.display_avatar.url
        ))
    
    @commands.command()
    async def embed(self, ctx, title, *, description):
        embed = discord.Embed(
            title = title,
            description = description,
            color = 0xffe5ce
        )
        if ctx.message.attachments != []:
            embed.set_image(url = ctx.message.attachments[0].url)
        await ctx.send(embed = embed)
    
    @commands.command(name = 'edit-embed', hidden = True)
    @commands.is_owner()
    async def edit_embed(self, ctx, msg_id: int, title, desc, channel: discord.TextChannel = None):
        if channel == None:
            channel = ctx.channel
        message = await channel.fetch_message(msg_id)
        if message.author != ctx.me or message.embeds == []: return
        
        embed = message.embeds[0]
        embed.title = title
        embed.description = desc
        if ctx.message.attachments != []:
            embed.set_image(url = ctx.message.attachments[0].url)
        await message.edit(embed = embed)
    
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.guild.id == None: return
        
        doc = snipe_col.find_one({'guild': message.guild.id})
        if doc == None:
            doc = {
                'guild': message.guild.id,
                'channels': {} #{channel.id: {}}
            }
            snipe_col.insert_one(doc)
        doc['channels'][str(message.channel.id)] = {
            'attachment': None if message.attachments == [] else message.attachments[0].proxy_url,
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
    async def snipe(self, ctx, channel: discord.TextChannel = None):
        if channel == None:
            channel = ctx.channel
        doc = snipe_col.find_one({'guild': ctx.guild.id})
        if doc == None or str(channel.id) not in doc['channels']:
            await ctx.reply('Nothing found.')
        else:
            fields = doc['channels'][str(channel.id)]
            author = ctx.guild.get_member(fields['author'])
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
                embed.description = f'> {(chr(10) + ">").join(reference.content.split())}{chr(10)}{reference.author.mention} ' + embed.description
            if fields['attachment']:
                embed.set_image(url = fields['attachment'])
            embed.set_author(
                name = str(author),
                icon_url = author.display_avatar.url
            )
            await ctx.reply(embed = embed) 

async def setup(bot): 
    await bot.add_cog(Utility())
