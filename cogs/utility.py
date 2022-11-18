import discord
from discord.ext import commands
import pymongo
import random
import time

'''
options = ('Trigger',)
for setting in options:
    if setting not in db:
        db[setting] = {} #{'guild.id': false}
'''

class Utility(commands.Cog):
    @commands.command(name = 'eval')
    async def evaluate(self, ctx, *, content):
        await ctx.reply(embed = discord.Embed(
            title = 'Evaluation',
            description = discord.utils.escape_markdown(str(eval(content, {
                'ctx': ctx,
                'discord': discord,
                'choose': random.choice,
                'random': random.randint,
                'timestamp': __import__('time').time,
                'shuffle': lambda x: random.sample(x, len(x))
            }, {i: None for i in (
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

'''
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.guild is None: return
        
        if str(message.guild.id) not in db['Trigger']:
            db['Trigger'][str(message.guild.id)] = False
        if db['Trigger'][str(message.guild.id)]:
            if 'im ' in message.content.lower():
                await message.reply(f"Hi {message.content[message.content.lower().index('im ') + 3:]}, I'm dad!")
            elif "i'm " in message.content.lower():
                await message.reply(f"Hi {message.content[message.content.lower().index(f'i{chr(39)}m ') + 4:]}, I'm dad!")
            elif 'i’m ' in message.content.lower():
                await message.reply(f"Hi {message.content[message.content.lower().index('i’m ') + 4:]}, I'm dad!")
            elif 'i am ' in message.content.lower():
                await message.reply(f"Hi {message.content[message.content.lower().index('i am ') + 5:]}, I'm dad!")
            if 'who asked' in message.content.lower():
                await message.reply('I asked 😎')
    
    @commands.command(help = 'Available settings:\n- ' + '\n- '.join(options))
    @commands.has_guild_permissions(manage_guild = True)
    async def settings(self, ctx, setting, value: bool):
        if setting.capitalize() in options:
            db[setting.capitalize()][str(ctx.guild.id)] = value
            await ctx.reply(f'Setting "{setting.capitalize()}" is now {"disabled enabled".split()[value]}.')
        else:
            await ctx.reply(f'Setting "{setting.capitalize()}" not found.')
'''

async def setup(bot):
    await bot.add_cog(Utility())
