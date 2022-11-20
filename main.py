import discord
from discord.ext import commands
import pymongo
import random
import time
import os

client = pymongo.MongoClient(
    f'mongodb+srv://Senjienji:{os.getenv("PASSWORD")}@senjienji.czypcav.mongodb.net/?retryWrites=true&w=majority',
    server_api = pymongo.server_api.ServerApi('1'),
)
db = client.db
prefix_cl = db.prefix

class MinimalHelpCommand(commands.MinimalHelpCommand):
    async def send_pages(self):
        await self.context.reply(embed = discord.Embed(
            title = 'Help',
            description = self.paginator.pages[0],
            color = 0xffe5ce
        ).set_footer(
            text = self.context.author.display_name,
            icon_url = self.context.author.display_avatar.url
        ))

def get_prefix(bot, message):
    if message.guild == None:
        return 's!'
    if prefix_cl.find_one({'guild': message.guild.id, 'bot': bot.user.id}) == None: 
        prefix_cl.insert_one({
            'guild': message.guild.id,
            'bot': bot.user.id,
            'prefix': 's!'
        })
    return prefix_cl.find_one({'guild': message.guild.id, 'bot': bot.user.id})['prefix']

bot = commands.Bot(
    command_prefix = get_prefix,
    activity = discord.Game('Python'),
    owner_id = 902371374033670224,
    help_command = MinimalHelpCommand(verify_checks = False),
    allowed_mentions = discord.AllowedMentions(
        everyone = False,
        roles = False,
        replied_user = False
    ), intents = discord.Intents(
        guilds = True,
        members = True,
        messages = True,
        message_content = True
    )
)

@bot.before_invoke
async def before_invoke(ctx):
    await bot.wait_until_ready()
    await ctx.channel.typing()

@bot.event
async def on_connect():
    print('Connected')
    for extension in os.listdir('./cogs'):
        if extension.endswith('.py'):
            await bot.load_extension(f'cogs.{extension[:-3]}')

@bot.event
async def on_ready():
    bot.launch_time = __import__('datetime').datetime.today()
    print('Ready')
    #await bot.get_user(bot.owner_id).send(f'Online since {discord.utils.format_dt(bot.launch_time, "d")} {discord.utils.format_dt(bot.launch_time, "T")}')

@bot.event
async def on_command_error(ctx, error):
    print(f'{str(type(error))[8:-2]}: {error}')
    content = str(error)
    if isinstance(error, commands.CommandOnCooldown):
        content = f'You are on cooldown. Try again {discord.utils.format_dt(__import__("datetime").datetime.fromtimestamp(time.time() + error.retry_after), "R")}'
    elif isinstance(error, commands.MissingRequiredArgument):
        return await ctx.send_help(ctx.command)
    elif isinstance(error, (commands.CommandNotFound, commands.NotOwner)):
        return
    try:
        await ctx.reply(content)
    except discord.HTTPException:
        await ctx.send(f'{ctx.author.mention} {content}')
    except discord.Forbidden:
        pass

@bot.event
async def on_guild_join(guild):
    await bot.get_user(bot.owner_id).send(f'Added to `{guild.name}`.')

@bot.event
async def on_guild_remove(guild):
    await bot.get_user(bot.owner_id).send(f'Removed from `{guild.name}`.')

@bot.command(hidden = True)
@commands.is_owner()
async def load(ctx, extension = None):
    if extension == None:
        for extension in os.listdir('./cogs'):
            if extension.endswith('py'):
                await bot.load_extension(f'cogs.{extension[:-3]}')
        await ctx.reply(f'`{", ".join(i[5:] for i in bot.extensions.keys())}` are loaded')
    else:
        await bot.load_extension(f'cogs.{extension}')
        await ctx.reply(f'`{extension}` loaded.')

@bot.command(hidden = True)
@commands.is_owner()
async def reload(ctx, extension = None):
    if extension == None:
        extensions = tuple(bot.extensions.keys())
        for extension in extensions:
            await bot.reload_extension(extension)
        await ctx.reply(f'`{", ".join(i[5:] for i in bot.extensions.keys())}` are reloaded.')
    else:
        await bot.reload_extension(f'cogs.{extension}')
        await ctx.reply(f'`{extension}` reloaded.')

@bot.command(hidden = True)
@commands.is_owner()
async def unload(ctx, extension=None):
    if extension == None:
        extensions = tuple(bot.extensions.keys())
        for extension in extensions:
            await bot.unload_extension(extension)
        await ctx.reply(f'`{", ".join(i[5:] for i in extensions)}` are unloaded.')
    else:
        await bot.unload_extension(f'cogs.{extension}')
        await ctx.reply(f'`{extension}` unloaded.')

@bot.command(hidden = True)
@commands.is_owner()
async def doc(ctx, *, query=None):
    if query == None:
        await ctx.reply('https://discordpy.readthedocs.io/en/latest/api.html')
    else:
        await ctx.reply(f'https://discordpy.readthedocs.io/en/latest/search.html?q={query.replace(" ", "+")}')

@bot.command(name = 'exec', hidden = True)
@commands.is_owner()
async def execute(ctx, *, content):
    if content.startswith('await '):
        output = await eval(content[6:])
        await ctx.reply(embed = discord.Embed(
            title = 'Await Evaluation',
            description = discord.utils.escape_markdown(output),
            color = 0xffe5ce
        ).set_footer(
            text = ctx.author.display_name,
            icon_url = ctx.author_display_avatar.url
        ))
    else:
        exec(content)
        await ctx.message.add_reaction('✅')

@bot.command(hidden = True)
@commands.is_owner()
async def leave(ctx, *, guild: discord.Guild):
    await guild.leave()

bot.run(os.environ["DISCORD_TOKEN"])
