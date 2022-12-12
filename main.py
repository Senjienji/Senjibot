import discord
from discord.ext import commands
from typing import Optional
import datetime
import pymongo
import time
import os

client = pymongo.MongoClient(
    f'mongodb+srv://Senjienji:{os.environ["PASSWORD"]}@senjienji.czypcav.mongodb.net/?retryWrites=true&w=majority',
    server_api = pymongo.server_api.ServerApi('1'),
)
db = client.senjibot
prefix_col = db.prefix

class MinimalHelpCommand(commands.MinimalHelpCommand):
    async def send_pages(self):
        await self.context.reply(embed = discord.Embed(
            title = 'Help',
            description = self.paginator.pages[0],
            color = 0xffe5ce
        ).set_author(
            name = self.context.author,
            url = f'https://discord.com/users/{self.context.author.id}',
            icon_url = self.context.author.display_avatar.url
        ))

def get_prefix(bot, message):
    if message.guild == None:
        return 's!'
    doc = prefix_col.find_one({'guild': message.guild.id})
    if doc == None:
        doc = {
            'guild': message.guild.id,
            'prefix': 's!'
        }
        prefix_col.insert_one(doc)
    return doc['prefix']

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
        message_content = True,
        reactions = True,
        emojis = True
    )
)

@bot.before_invoke
async def before_invoke(ctx):
    await bot.wait_until_ready()
    await ctx.channel.typing()

@bot.event
async def on_connect():
    for extension in os.listdir('./cogs'):
        if extension.endswith('.py'):
            await bot.load_extension(f'cogs.{extension[:-3]}')
    print('Connected')

@bot.event
async def on_ready():
    bot.launch_time = datetime.datetime.today()
    print('Ready')

@bot.event
async def on_command_error(ctx, error):
    ctx.command.reset_cooldown(ctx)
    content = str(error)
    if isinstance(error, commands.CommandOnCooldown):
        content = f'You are on cooldown. Try again {discord.utils.format_dt(datetime.datetime.fromtimestamp(time.time() + error.retry_after), "R")}'
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
    raise error

@bot.event
async def on_guild_join(guild):
    await bot.get_user(bot.owner_id).send(f'Added to `{guild.name}`.')

@bot.event
async def on_guild_remove(guild):
    await bot.get_user(bot.owner_id).send(f'Removed from `{guild.name}`.')

@bot.command(hidden = True)
@commands.is_owner()
async def doc(ctx, *, query: Optional[str]):
    if query == None:
        await ctx.reply('https://discordpy.readthedocs.io/en/latest/api.html')
    else:
        await ctx.reply(f'https://discordpy.readthedocs.io/en/latest/search.html?q={query.replace(" ", "+")}')

@bot.command(name = 'exec', hidden = True)
@commands.is_owner()
async def execute(ctx, *, content):
    exec(content)
    await ctx.message.add_reaction('\U00002705')

@bot.command(name = 'eval', hidden = True)
@commands.is_owner()
async def evaluate(ctx, *, content):
    embed = discord.Embed(
        title = 'Evaluation',
        color = 0xffe5ce
    ).set_author(
        name = ctx.author,
        url = f'https://discord.com/users/{ctx.author.id}',
        icon_url = ctx.author.display_avatar.url
    )
    if content.startswith('await '):
        embed.title = 'Async ' + embed.title
        embed.description = await eval(content[6:], {**globals(), **locals()}, {})
    else:
        embed.description = eval(content, {**globals(), **locals()}, {})
    embed.description = discord.utils.escape_markdown(str(embed.description))
    await ctx.reply(embed = embed)

@bot.command(hidden = True)
@commands.is_owner()
async def leave(ctx, *, guild: discord.Guild):
    await guild.leave()

bot.run(os.environ["DISCORD_TOKEN"])
