import discord
from discord.ext import commands
from webserver import keep_alive
from inspect import Parameter
from replit import db
from time import time as timestamp
import random

newline = "\n"

if "Prefix" not in db:
    db["Prefix"] = {} #{"guild_id": "prefix"}
if "Balance" not in db:
    db["Balance"] = {} #{"user_id": amount}
if "Shop" not in db:
    db["Shop"] = {} #{"guild_id": {"name": price}}
if "Enabled" not in db:
    db["Enabled"] = {} #{"guild_id": {"command_name": enabled}}

class HelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        await self.context.message.reply(embed = discord.Embed(
            title = "Help",
            description = f"""
Use `{self.context.bot.command_prefix(self.context.bot, self.context.message)}{self.context.command.name} <command>` for more info on a command.

**__Commands__**
{' '.join(command.name for command in await self.filter_commands(mapping[None], sort = True))}
            """,
            color = 0xffe5ce
        ).set_footer(
            text = self.context.author.display_name,
            icon_url = self.context.author.avatar
        ))
    async def send_group_help(self, group):
        await self.context.message.reply(embed = discord.Embed(
            title = "Help",
            description = f"""
{self.context.bot.command_prefix(self.context.bot, self.context.message)}{group.name}

Use `{self.context.bot.command_prefix(self.context.bot, self.context.message)}{self.context.command.name} {group.name} [command]` for more info on a command.

**Commands**
{newline.join(f"{self.context.bot.command_prefix(self.context.bot, self.context.message)}{group.name} {command.name}" for command in group.commands)}
            """,
            color = 0xffe5ce
        ).set_footer(
            text = self.context.author.display_name,
            icon_url = self.context.author.avatar
        ))
    async def send_command_help(self, command):
        await self.context.message.reply(embed = discord.Embed(
            title = "Help",
            description = f"{self.context.bot.command_prefix(self.context.bot, self.context.message)}{command.name} {command.signature}" + (f"\n**Aliases:** {', '.join(command.aliases)}" if command.aliases != [] else str()),
            color = 0xffe5ce
        ).set_footer(
            text = self.context.author.display_name,
            icon_url = self.context.author.avatar
        ))

def get_prefix(client, message):
    if message.guild == None:
        return "s!"
    elif str(message.guild.id) not in db["Prefix"]:
        db["Prefix"][str(message.guild.id)] = "s!"
    return db["Prefix"][str(message.guild.id)]

client = commands.Bot(
    command_prefix = get_prefix,
    activity = discord.Game("Python"),
    help_command = HelpCommand(verify_checks = False),
    owner_id = 902371374033670224,
    allowed_mentions = discord.AllowedMentions(
        everyone = False,
        replied_user = False,
        roles = False
    ),
    intents = discord.Intents(
        emojis = True,
        guilds = True,
        members = True,
        messages = True,
        reactions = True
    )
)

@client.check
async def is_enabled(ctx):
    if ctx.guild == None:
        return True
    if str(ctx.guild.id) not in db["Enabled"]:
        db["Enabled"][str(ctx.guild.id)] = {command.name: True for command in client.commands}
    if ctx.command.name not in db["Enabled"][str(ctx.guild.id)]:
        db["Enabled"][str(ctx.guild.id)][ctx.command.name] = True
    return db["Enabled"][str(ctx.guild.id)][ctx.command.name]

@client.before_invoke
async def trigger_typing(ctx):
    await ctx.trigger_typing()

#Events
@client.event
async def on_connect():
    print("Connected")

@client.event
async def on_ready():
    print("Ready")
    client.launch_time = __import__("datetime").datetime.utcnow()
    await client.get_user(client.owner_id).send(f"Online since <t:{int(client.launch_time.timestamp())}:d> <t:{int(client.launch_time.timestamp())}:T>")

@client.event
async def on_command_error(ctx, error):
    print(f"{str(type(error))[8:-2]}: {error}")
    content = str(error)
    if isinstance(error, commands.CommandOnCooldown):
        content = f"You are on cooldown. Try again <t:{int(timestamp() + error.retry_after)}:R>"
    elif isinstance(error, (commands.CommandNotFound, commands.NotOwner)) or str(error) == f"The global check functions for command {ctx.command.name} failed.":
        return
    try:
        message = await ctx.reply(content)
    except discord.HTTPException:
        message = await ctx.send(f"{ctx.author.mention} {content}")
    except discord.Forbidden:
        try:
            return await ctx.author.send(f"> {ctx.channel.mention}: {ctx.message.content}\n{content}")
        except discord.Forbidden:
            return

@client.event
async def on_guild_join(guild):
    await client.get_user(client.owner_id).send(f"Added to `{guild.name}`.")

@client.event
async def on_guild_remove(guild):
    await client.get_user(client.owner_id).send(f"Removed from `{guild.name}`.")

#Miscellaneous Commands
@client.command(name = "eval")
async def evaluate(ctx, *, content):
    await ctx.reply(embed = discord.Embed(
        title = "Evaluation",
        description = str(eval(content, {
            "ctx": ctx,
            "client": client,
            "discord": discord,
            "choose": random.choice,
            "timestamp": timestamp(),
            "token": "NeverGonna.Give.YouUp",
            "shuffle": lambda x: random.sample(x, len(x)),
            "db": __import__("json").loads(db.dumps(dict(db)))
        }, {
            "__import__": None,
            "copyright": None,
            "credits": None,
            "license": None,
            "eval": None,
            "exec": None,
            "help": None,
            "exit": None,
            "quit": None
        })),
        color = 0xffe5ce
    ).set_footer(
        text = ctx.author.display_name,
        icon_url = ctx.author.avatar
    ))

@client.command(aliases = ["cd"])
async def cooldown(ctx):
    await ctx.reply(embed = discord.Embed(
        title = "Cooldowns",
        description = "\n".join(f"{index}. `{command.name}`: <t:{int(timestamp() + command.get_cooldown_retry_after(ctx))}:F>" for index, command in enumerate(filter(lambda command: command.is_on_cooldown(ctx), client.commands), start = 1)) or "Nothing found.",
        color = 0xffe5ce
    ).set_footer(
        text = ctx.author.display_name,
        icon_url = ctx.author.avatar
    ))

@client.command(brief = "Rock Paper Scissors", help = """
 - Rock & Rock: Tie
 - Rock & Paper: Lose
 - Rock & Scissors: Win
 - Paper & Rock: Win
 - Paper & Paper: Tie
 - Paper & Scissors: Lose
 - Scissors & Rock: Lose
 - Scissors & Paper: Win
 - Scissors & Scissors: Tie""")
@commands.bot_has_permissions(add_reactions = True)
async def rps(ctx, member: discord.Member = None):
    if member == None:
        member = client.user
    if member == ctx.author:
        return await ctx.reply("You can't play against yourself.")
    moves = ("🪨", "📄", "✂️")
    try:
        message = await ctx.reply("Choose a move by reacting to one of the reactions down below:")
        for emoji in moves:
            await message.add_reaction(emoji)
        reaction, user = await client.wait_for("reaction_add", check = lambda reaction, user: str(reaction.emoji) in moves and reaction.message == message and user == ctx.author, timeout = 30)
        await message.delete()
        p1 = moves.index(str(reaction.emoji))
        if member.bot:
            p2 = random.randint(0, 2)
        else:
            message = await ctx.send(f"{member.mention} Choose a move by reacting to one of the reactions down below:")
            for emoji in moves:
                await message.add_reaction(emoji)
            reaction, user = await client.wait_for("reaction_add", check = lambda reaction, user: str(reaction.emoji) in moves and reaction.message == message and user == member, timeout = 30)
            await message.delete()
            p2 = moves.index(str(reaction.emoji))
        if p1 - p2 in (-2, 1):
            await ctx.reply(f"{ctx.author.display_name} wins!\n\n{ctx.author.display_name}: {moves[p1]} | {member.display_name}: {moves[p2]}")
        elif p1 - p2 in (-1, 2):
            await ctx.reply(f"{member.display_name} wins!\n\n{ctx.author.display_name}: {moves[p1]} | {member.display_name}: {moves[p2]}")
        else:
            await ctx.reply( f"It's a tie!\n\n{ctx.author.display_name}: {moves[p1]} | {member.display_name}: {moves[p2]}")
    except __import__("asyncio").TimeoutError:
        await message.edit(content = "You didn't reply in time.")

@client.command()
async def embed(ctx, title: str = "", description: str = "", url: str = ""):
    if title + description == "":
        raise commands.MissingRequiredArgument(Parameter("title" if title == "" else "description", Parameter.VAR_POSITIONAL))
    embed = discord.Embed(
        title = title,
        description = description,
        color = 0xffe5ce
    )
    if url != "":
        embed.set_image(
            url = url
        )
    elif ctx.message.attachments != []:
        embed.set_image(
            url = ctx.message.attachments[0].url
        )
    if ctx.message.reference != None and ctx.message.reference.resolved != None and ctx.message.reference.resolved.author in (client.user, ctx.author):
        await ctx.message.reference.resolved.edit(embed = embed)
    else:
        await ctx.send(embed = embed)

@client.command()
async def invite(ctx):
    await ctx.reply("<https://Senjibot.senjienji.repl.co/invite>")

#Informational Commands
@client.command()
@commands.bot_has_permissions(attach_files = True)
async def user(ctx, *, user: discord.User = None):
    if user == None:
        user = ctx.author
    await ctx.reply(embed = discord.Embed(
        title = "User Info",
        description = f"""
Name: {user.name}
Tag: #{user.discriminator}
ID: {user.id}
Bot? {'Yes' if user.bot else 'No'}
Created at: <t:{int(user.created_at.timestamp())}:F>
Avatar URL: [Link]({user.avatar_url})
        """,
        color = 0xffe5ce
    ).set_image(
        url = user.avatar_url
    ).set_footer(
        text = ctx.author.display_name,
        icon_url = ctx.author.avatar
    ))

@client.command()
@commands.guild_only()
@commands.bot_has_permissions(attach_files = True)
async def member(ctx, *, member: discord.Member = None):
    if member == None:
        member = ctx.author
    await ctx.reply(embed = discord.Embed(
        title = "Member Info",
        url = f"https://discord.com/users/{member.id}",
        description = f"""
Nick: {member.nick}
Name: {member.name}
Tag: #{member.discriminator}
ID: {member.id}
Bot? {'Yes' if member.bot else 'No'}
Roles: {len(member.roles) - 1}
Created at: <t:{int(member.created_at.timestamp())}:F>
Joined at: <t:{int(member.joined_at.timestamp())}:F>
Avatar URL: [Link]({member.avatar})
        """,
        color = 0xffe5ce
    ).set_image(
        url = member.avatar_url
    ).set_footer(
        text = ctx.author.display_name,
        icon_url = ctx.author.avatar
    ))

@client.command(aliases = ("server",))
@commands.bot_has_permissions(attach_files = True)
async def guild(ctx, *, guild: discord.Guild = None):
    if guild == None:
        guild = ctx.guild
    await ctx.reply(embed = discord.Embed(
        title = "Server Info",
        description = f"""
Name: {guild.name}
ID: {guild.id}
Members: {len(list(filter(lambda member: member.bot == False, guild.members)))} humans, {len(list(filter(lambda member: member.bot, guild.members)))} bots, {guild.member_count} total
Channels: {len(guild.text_channels)} text, {len(guild.voice_channels)} voice
Roles: {len(guild.roles) - 1}
Owner: {guild.owner.mention} ({guild.owner})
Created at: <t:{int(guild.created_at.timestamp())}:F>
Icon URL: [Link]({guild.icon_url})
        """,
        color = 0xffe5ce
    ).set_image(
        url = guild.icon_url
    ).set_footer(
        text = ctx.author.display_name,
        icon_url = ctx.author.avatar
    ))

@client.command(aliases = ["emote"])
@commands.bot_has_permissions(attach_files = True)
async def emoji(ctx, *, emoji: discord.Emoji):
    await ctx.reply(embed = discord.Embed(
        title = "Emoji Info",
        description = f"""
Name: {emoji.name}
ID: {emoji.id}
Animated? {'Yes' if emoji.animated else 'No'}
Created at: <t:{int(emoji.created_at.timestamp())}:F>
URL: [Link]({emoji.url})
        """,
        color = 0xffe5ce
    ).set_image(
        url = emoji.url
    ).set_footer(
        text = ctx.author.display_name,
        icon_url = ctx.author.avatar
    ))

@client.command()
async def bot(ctx):
    await ctx.reply(embed = discord.Embed(
        title = "Bot Info",
        description = f"""
In: {len(client.guilds)} guilds
Latency: {int(client.latency * 1000)}ms
Uptime: <t:{int(client.launch_time.timestamp())}:R>
Version: {discord.__version__}
        """,
        color = 0xffe5ce
    ).set_footer(
        text = ctx.author.display_name,
        icon_url = ctx.author.avatar
    ))

#Moderation Commands
@client.command()
@commands.guild_only()
@commands.has_guild_permissions(kick_members = True)
@commands.bot_has_guild_permissions(kick_members = True)
async def kick(ctx, user: discord.User, *, reason: str = "no reason"):
    await ctx.guild.kick(user, reason = f"By {ctx.author.name} for {reason}.")
    await ctx.reply(f"{user.name} has been kicked for {reason}.")

@client.command()
@commands.guild_only()
@commands.has_guild_permissions(ban_members = True)
@commands.bot_has_guild_permissions(ban_members = True)
async def ban(ctx, user: discord.User, *, reason: str = "no reason"):
    await ctx.guild.ban(user, reason = f"By {ctx.author.name} for {reason}.", delete_message_days = 0)
    await ctx.reply(f"{user.name} has been banned for {reason}.")

@client.command()
@commands.guild_only()
@commands.has_guild_permissions(ban_members = True)
@commands.bot_has_guild_permissions(ban_members = True)
async def unban(ctx, user: discord.User, *, reason: str = "no reason"):
    await ctx.guild.unban(user, reason = f"By {ctx.author.name} for {reason}.")
    await ctx.reply(f"{user.name} has been unbanned for {reason}.")

@client.command()
async def prefix(ctx, prefix = None):
    if ctx.guild == None:
        await ctx.reply(f"My current prefix is `{client.command_prefix(client, ctx.message)}`.")
    elif prefix == None:
        await ctx.reply(f"My current prefix is `{db['Prefix'][str(ctx.guild.id)]}`.")
    elif ctx.author.guild_permissions.manage_guild:
        db["Prefix"][str(ctx.guild.id)] = prefix
        await ctx.reply(f"Prefix has been set to `{db['Prefix'][str(ctx.guild.id)]}`.")
    else:
        raise commands.MissingPermissions(["manage_guild"])

@client.command()
@commands.guild_only()
@commands.has_guild_permissions(manage_roles = True)
@commands.bot_has_guild_permissions(manage_roles = True)
async def role(ctx, role: discord.Role, *, member: discord.Member = None):
    if member == None:
        member = ctx.author
    if ctx.author.top_role.position < role.position and ctx.author != ctx.guild.owner:
        return await ctx.reply(f"Your highest role is not high enough.")
    if role in member.roles:
        await member.remove_roles(role, reason = f"By {ctx.author.name}")
        await ctx.reply(f"Removed {role.mention} from {member.mention}.")
    else:
        await member.add_roles(role, reason = f"By {ctx.author.name}")
        await ctx.reply(f"Added {role.mention} to {member.mention}.")

@client.command()
@commands.guild_only()
@commands.has_guild_permissions(manage_guild = True)
async def enable(ctx, command):
    found = False
    for cmd in client.commands:
        if command.lower() in (cmd.name, *cmd.aliases):
            command = cmd.name
            found = True
            break
    if not found:
        raise commands.BadArgument(f'Command "{command}" not found.')
    elif command in ("enable", "disable", "help"):
        raise commands.UserInputError("cannot enable this command.")
    db["Enabled"][str(ctx.guild.id)][command] = True
    await ctx.reply(f'"{command}" enabled.')

@client.command()
@commands.guild_only()
@commands.has_guild_permissions(manage_guild = True)
async def disable(ctx, command):
    found = False
    for cmd in client.commands:
        if command.lower() in (cmd.name, *cmd.aliases):
            command = cmd.name
            found = True
            break
    if not found:
        raise commands.BadArgument(f'Command "{command}" not found')
    elif command in ("enable", "disable", "help"):
        raise commands.UserInputError("cannot disable this command.")
    db["Enabled"][str(ctx.guild.id)][command] = False
    await ctx.reply(f'"{command}" disabled.')

@client.command()
@commands.guild_only()
@commands.has_permissions(manage_messages = True)
@commands.bot_has_permissions(manage_messages = True, read_message_history = True)
async def purge(ctx, limit: str):
    if limit.lower() in ("all", "max", "maximum"):
        limit = len(await ctx.channel.history(limit = None).flatten())
    else:
        limit = int(limit)
    purge = await ctx.channel.purge(limit = limit + 1)
    await ctx.send(f"Purged {len(purge) - 1} messages.", delete_after = 5)

#Currency Commands
@client.command(aliases = ["bal"])
async def balance(ctx, *, member: discord.Member = None):
    if member == None:
        member = ctx.author
    if member.bot:
        raise commands.BadArgument("member must not be a bot")
    if str(member.id) not in db["Balance"]:
        db["Balance"][str(member.id)] = 0
    await ctx.reply(f"`{member}` have ${db['Balance'][str(member.id)]}.")

@client.command(aliases = ["lb"])
@commands.guild_only()
async def leaderboard(ctx):
    await ctx.reply(embed = discord.Embed(
        title = "Leaderboard",
        description = "\n".join(f"{index}. `{member}`: ${amount}" for index, (member, amount) in enumerate(sorted(filter(lambda i: i[0] != None and i[1] > 0, [(ctx.guild.get_member(int(i[0])), i[1]) for i in db["Balance"].items()]), key = lambda i: i[1], reverse = True), start = 1)),
        color = 0xffe5ce
    ).set_footer(
        text = ctx.author.display_name,
        icon_url = ctx.author.avatar
    ))

@client.command()
@commands.cooldown(rate = 1, per = 1 * 60 * 60, type = commands.BucketType.user)
async def work(ctx):
    if str(ctx.author.id) not in db["Balance"]:
        db["Balance"][str(ctx.author.id)] = 0 
    gain = random.randint(500, 1000)
    db["Balance"][str(ctx.author.id)] += gain
    await ctx.reply(f"You got ${gain}.")

@client.command()
async def gamble(ctx, amount: int):
    if str(ctx.author.id) not in db["Balance"]:
        db["Balance"][str(ctx.author.id)] = 0
    if amount < 1:
        await ctx.reply("amount must be higher than 0.")
    elif db["Balance"][str(ctx.author.id)] >= amount:
        p1, p2 = (random.randint(2, 12), random.randint(2, 12))
        if p1 > p2:
            db["Balance"][str(ctx.author.id)] += amount
            await ctx.reply(f"You won ${amount}!\n\n{ctx.author.name}: {p1}\n{client.user.name}: {p2}")
        elif p1 < p2:
            db["Balance"][str(ctx.author.id)] -= amount
            await ctx.reply(f"You lost ${amount}.\n\n{ctx.author.name}: {p1}\n{client.user.name}: {p2}")
        else:
            await ctx.reply(f"It's a tie?\n\n{ctx.author.name}: {p1}\n{client.user.name}: {p2}")
    else:
        await ctx.reply(f"You are ${amount - db['Balance'][str(ctx.author.id)]} short.")

#Shop Commands
@client.group()
@commands.guild_only()
async def shop(ctx):
    if str(ctx.guild.id) not in db["Shop"]:
        db["Shop"][str(ctx.guild.id)] = {"nothing": 0} #{"name": price}
    if ctx.invoked_subcommand == None:
        await ctx.reply(embed = discord.Embed(
            title = "Shop",
            description = "\n".join(f"{index}. `{name}`: ${price}" for index, (name, price) in enumerate(sorted(db["Shop"][str(ctx.guild.id)].items(), key = lambda i: i[1]), start = 1)),
            color = 0xffe5ce
        ).set_footer(
            text = ctx.author.display_name,
            icon_url = ctx.author.avatar
        ))

@shop.command()
@commands.has_guild_permissions(manage_guild = True)
async def add(ctx, name, price: int):
    if name in db["Shop"][str(ctx.guild.id)]:
        await ctx.reply(f'Item "{name}" is already added.')
    elif price >= 0:
        db["Shop"][str(ctx.guild.id)][name] = price
        await ctx.reply(f'Item "{name}" added.')
    else:
        await ctx.reply("price must be greater than -1.")

@shop.command()
@commands.has_guild_permissions(manage_guild = True)
async def edit(ctx, name, other):
    if name not in db["Shop"][str(ctx.guild.id)]:
        await ctx.reply(f'Item "{name}" not found.')
    elif other.isnumeric():
        db["Shop"][str(ctx.guild.id)][name] = int(other)
        await ctx.reply(f'Item "{name}" edited.')
    else:
        db["Shop"][str(ctx.guild.id)][other] = db["Shop"][str(ctx.guild.id)][name]
        del db["Shop"][str(ctx.guild.id)][name]
        await ctx.reply(f'Item "{name}" edited to "{other}".')

@shop.command()
@commands.has_guild_permissions(manage_guild = True)
async def remove(ctx, *, name):
    if name in db["Shop"][str(ctx.guild.id)]:
        del db["Shop"][str(ctx.guild.id)][name]
        await ctx.reply(f'Item "{name}" removed.')
    else:
        await ctx.reply(f'Item "{name}" not found.')

@client.command()
@commands.guild_only()
async def buy(ctx, *, name):
    if str(ctx.author.id) not in db["Balance"]:
        db["Balance"][str(ctx.author.id)] = 0
    if str(ctx.guild.id) not in db["Shop"]:
        db["Shop"][str(ctx.guild.id)] = {"nothing": 0} #{"name": price}
    if name not in db["Shop"][str(ctx.guild.id)]:
        await ctx.reply(f'Item "{name}" not found.')
    elif db["Balance"][str(ctx.author.id)] >= db["Shop"][str(ctx.guild.id)][name]:
        db["Balance"][str(ctx.author.id)] -= db["Shop"][str(ctx.guild.id)][name]
        await ctx.reply(f'Item "{name}" purchased.')
    else:
        await ctx.reply(f"You are ${db['Shop'][str(ctx.guild.id)][name] - db['Balance'][str(ctx.author.id)]} short.")

#Private Commands
@client.command(hidden = True)
@commands.is_owner()
async def doc(ctx, *, search = ""):
    if search == "":
        await ctx.reply("https://discordpy.readthedocs.io/en/stable/")
    else:
        await ctx.reply(f"https://discordpy.readthedocs.io/en/stable/search.html?q={search.replace(' ', '+')}")

@client.command(hidden = True)
@commands.is_owner()
async def set(ctx, member: discord.Member, amount: int):
    db["Balance"][str(member.id)] = amount
    await ctx.reply(f"`{member}`'s balance has been set to ${amount}.")

@client.command(name = "exec", hidden = True)
@commands.is_owner()
async def execute(ctx, *, content):
    exec(content)
    await ctx.reply("done")

@client.command(hidden = True)
@commands.is_owner()
async def invites(ctx, *, guild: discord.Guild):
    try:
        invites = await guild.invites()
    except discord.Forbidden:
        await ctx.reply(f"Not enough permission.")
    else:
        await ctx.author.send("\n".join(invite.url for invite in invites) or "No invites.")

@client.command(hidden = True)
@commands.is_owner()
async def leave(ctx, *, guild: discord.Guild):
	await guild.leave()

keep_alive()
client.run(__import__("os").environ["token"])