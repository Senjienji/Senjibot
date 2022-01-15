import discord
from discord.ext import commands
from webserver import keep_alive
from replit import db
import random
import time
import os 

if 'Prefix' not in db:
    db['Prefix'] = {} #{'guild.id': 'prefix'}

class MinimalHelpCommand(commands.MinimalHelpCommand):
    async def send_pages(self):
        await self.context.reply(embed = discord.Embed(
            title = 'Help',
            description = self.paginator.pages[0],
            color = 0xffe5ce
        ).set_footer(
            text = self.context.author.display_name,
            icon_url = self.context.author.display_avatar
        ))

def get_prefix(bot, message):
    if message.guild == None:
        return 's!'
    if str(message.guild.id) not in db['Prefix']:
        db['Prefix'][str(message.guild.id)] = 's!'
    return db['Prefix'][str(message.guild.id)]

bot = commands.Bot(
    command_prefix = get_prefix,
    activity = discord.Game('Python'),
    owner_id = 902371374033670224,
    help_command = MinimalHelpCommand(verify_checks = False),
    allowed_mentions = discord.AllowedMentions(
        everyone = False,
        roles = False,
        replied_user = False
    ),
    intents = discord.Intents(
        guilds = True,
        members = True,
        messages = True
    )
)

for extension in os.listdir('./cogs'):
    if extension.endswith('.py'):
        bot.load_extension(f'cogs.{extension[:-3]}')

@bot.check
async def is_enabled(ctx):
    if ctx.guild == None:
        return True
    if str(ctx.guild.id) not in db['Enabled']:
        db['Enabled'][str(ctx.guild.id)] = {command.name: True for command in bot.commands}
    if ctx.command.name not in db['Enabled'][str(ctx.guild.id)]:
        db['Enabled'][str(ctx.guild.id)][ctx.command.name] = True
    return db['Enabled'][str(ctx.guild.id)][ctx.command.name]

@bot.before_invoke
async def before_invoke(ctx):
    await bot.wait_until_ready()
    await ctx.trigger_typing()

@bot.event
async def on_connect():
    print('Connected')

@bot.event
async def on_ready():
    bot.launch_time = __import__('datetime').datetime.today()
    print('Ready')
    await bot.get_user(bot.owner_id).send(f'Online since {discord.utils.format_dt(bot.launch_time, "d")} {discord.utils.format_dt(bot.launch_time, "T")}')

@bot.event
async def on_command_error(ctx, error):
    print(f'{str(type(error))[8:-2]}: {error}')
    content = str(error)
    if isinstance(error, commands.CommandOnCooldown):
        content = f'You are on cooldown. Try again {discord.utils.format_dt(__import__("datetime").datetime.fromtimestamp(time.time() + error.retry_after), "R")}'
    elif isinstance(error, commands.MissingRequiredArgument):
        return await ctx.send_help(ctx.command)
    elif isinstance(error, (commands.CommandNotFound, commands.NotOwner)) or str(error) == f'The global check functions for command {ctx.command.name} failed.':
        return
    try:
        await ctx.reply(content)
    except discord.HTTPException:
        await ctx.send(f'{ctx.author.mention} {content}')
    except discord.Forbidden:
        try:
            await ctx.author.send(f'> {ctx.channel.mention}: {ctx.message.content}\n{content}')
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
            if extension.endwith('py'):
                bot.load_extension(f'cogs.{extension[:-3]}')
        await ctx.reply(f'`{" ".join(bot.extensions.keys())}` loaded')
    else:
        bot.load_extension(f'cogs.{extension}')
        await ctx.reply(f'`cogs.{extension}` loaded.')

@bot.command(hidden = True)
@commands.is_owner()
async def reload(ctx, extension = None):
    if extension == None:
        for extension in os.listdir('./cogs'):
            if extension.endswith('.py'):
                bot.reload_extension(f'cogs.{extension[:-3]}')
        await ctx.reply(f'`{" ".join(bot.extensions.keys())}` reloaded.')
    else:
        bot.reload_extension(f'cogs.{extension}')
        await ctx.reply(f'`{extension}` reloaded.')

@bot.command(hidden = True)
@commands.is_owner()
async def unload(ctx, extension = None):
    if extension == None:
        for extension in os.listdir('./cogs'):
            if extension.endswith('.py'):
                bot.unload_extension(f'cogs.{extension[:-3]}')
        await ctx.reply(f'`{" ".join(filter(lambda extension: extension.endswith("py"), os.listdir("./cogs")))}` unloaded.')
    else:
        bot.reload_untension(f'cogs.{extension}')
        await ctx.reply(f'`{extension}` unloaded.')


@bot.command(hidden = True)
@commands.is_owner()
async def doc(ctx, *, query = None):
    if query == None:
        await ctx.reply('https://discordpy.readthedocs.io/en/master/api.html')
    else:
        await ctx.reply(f'https://discordpy.readthedocs.io/en/master/search.html?q={query.replace(" ", "+")}')

@bot.command(name = 'exec', hidden = True)
@commands.is_owner()
async def execute(ctx, *, content):
    exec(content)
    await ctx.reply('done')

@bot.command(hidden = True)
@commands.is_owner()
async def leave(ctx, *, guild: discord.Guild):
	await guild.leave()

keep_alive()
bot.run(os.getenv('token'))