import discord
from discord.ext import commands
from webserver import keep_alive
from replit import db
from time import time as timestamp
import random

if "Prefix" not in db:
    db["Prefix"] = {} #{"guild.id": "prefix"}
if "Balance" not in db:
    db["Balance"] = {} #{"user.id": amount}
if "Enabled" not in db:
    db["Enabled"] = {} #{"guild.id": {"command": enabled}}
if "Shop" not in db:
    db["Shop"] = {} #{"guild.id": {"name": price}}

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
""" + "\n".join(f"{self.context.bot.command_prefix(self.context.bot, self.context.message)}{group.name} {command.name}" for command in group.commands),
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
async def before_invoke(ctx):
    if random.randint(0, 100) < 20 and ctx.command.name != "purge":
        await ctx.reply("""
**WARNING**
This bot will be scheduled for deletion in <t:1640995200:D>,
Please re-invite me: <https://Senjibot.senjienji.repl.co/invite>
                        """)
    await ctx.trigger_typing()

#Events
@client.event
async def on_connect():
    print("Connected")

@client.event
async def on_ready():
    print("Ready")
    client.launch_time = timestamp()
    await client.get_user(client.owner_id).send(f"Online since <t:{int(client.launch_time)}:d> <t:{int(client.launch_time)}:T>")

@client.event
async def on_command_error(ctx, error):
    print(f"{str(type(error))[8:-2]}: {error}")
    content = str(error)
    if isinstance(error, commands.CommandOnCooldown):
        content = f"You are on cooldown. Try again <t:{int(timestamp() + error.retry_after)}:R>"
    elif isinstance(error, (commands.CommandNotFound, commands.NotOwner)) or str(error) == f"The global check functions for command {ctx.command.name} failed.":
        return
    try:
        await ctx.reply(content)
    except discord.HTTPException:
        await ctx.send(f"{ctx.author.mention} {content}")
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
            "timestamp": timestamp,
            "shuffle": lambda x: random.sample(x, len(x)),
            "db": __import__("json").loads(db.dumps(dict(db)))
        }, {
            "print": (print if await client.is_owner(ctx.author) else None),
            "__import__": None,
            "copyright": None,
            "credits": None,
            "license": None,
            "eval": None,
            "exec": None,
            "help": None,
            "exit": None,
            "quit": None,
            "open": None
        })),
        color = 0xffe5ce
    ).set_footer(
        text = ctx.author.display_name,
        icon_url = ctx.author.avatar
    ))

@client.command()
async def math(ctx):
    equation = f"{random.randint(1, 99)} {random.choice(('+', '-', '*', '%', '//'))} {random.randint(1, 99)}"
    reply = await ctx.reply(f"{equation} = ?")
    try:
        message = await client.wait_for("message", check = lambda message: message.channel == ctx.channel and message.author == ctx.author, timeout = 60)
        embed = discord.Embed(
            description = f"{equation} = {eval(equation)}",
            color = 0xffe5ce
        ).set_footer(
            text = f"{int((message.created_at - reply.created_at).total_seconds())} seconds"
        )
        try:
            if int(message.content) == eval(equation):
                embed.title = "Correct!"
            else:
                embed.title = "Wrong!"
        except ValueError:
            embed.title = "Invalid number passed."
        await message.reply(embed = embed)
    except __import__("asyncio").TimeoutError:
        await reply.edit(content = f"{equation} = {eval(equation)}\nYou didn't reply in time.")

@client.command()
async def rps(ctx, member: discord.Member = None):
    if member == None:
        member = client.user
    if member == ctx.author:
        return await ctx.reply("no")
    view = discord.ui.View(timeout = 60)
    view.add_item(discord.ui.Select(placeholder = "Select a move", options = [discord.SelectOption(
        label = "Rock",
        emoji = "🪨"
    ), discord.SelectOption(
        label = "Paper",
        emoji = "📄"
    ), discord.SelectOption(
        label = "Scissors",
        emoji = "✂️"
    )]))
    message = await ctx.reply(f"{ctx.author.mention} Select a move:", view = view)
    try:
        interaction = await client.wait_for("interaction", check = lambda interaction: interaction.message == message and interaction.user == ctx.author, timeout = 60)
        moves = ("Rock", "Paper", "Scissors")
        p1 = moves.index(view.children[0].values[0])
        if member.bot:
            p2 = random.randint(0, 2)
        else:
            await message.edit(content = f"{member.mention} Select a move:")
            try:
                interaction = await client.wait_for("interaction", check = lambda interaction: interaction.message == message and interaction.user == member, timeout = 60)
                p2 = moves.index(view.children[0].values[0])
            except __import__("asyncio").TimeoutError:
                return await message.edit(content = f"{member.mention} You didn't select in time.", view = None)
        if p1 - p2 in (-2, 1):
            content = f"{ctx.author.display_name} won!"
        elif p1 - p2 in (-1, 2):
            content = f"{member.display_name} won!"
        else:
            content = "It's a tie!"
        content += f"\n\n`{ctx.author.display_name}`: {moves[p1]}\n`{member.display_name}`: {moves[p2]}"
        await message.edit(content = content, view = None)
    except __import__("asyncio").TimeoutError:
        await message.edit(content = f"{ctx.author.mention} You didn't select in time.", view = None)

@client.command(hidden = True)
async def select(ctx):
    menu = discord.ui.Select(placeholder = "Select an option", max_values = 25)
    for i in range(25):
        menu.add_option(label = f"Option {i + 1}")
    view = discord.ui.View(timeout = 60)
    view.add_item(menu)
    message = await ctx.reply("Select Menu", view = view)
    while True:
        try:
            interaction = await client.wait_for("interaction", check = lambda interaction: interaction.message == message, timeout = 1 * 60 * 60)
            await interaction.followup.send(f"You selected {', '.join(view.children[0].values)}!", ephemeral = True)
        except __import__("asyncio").TimeoutError:
            view.children[0].disable = True
            view.stop()
            break

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

@client.command()
async def embed(ctx, title, description, footer):
    embed = discord.Embed(
        title = title,
        description = description,
        color = 0xffe5ce
    )
    embed.set_footer(text = footer)
    if ctx.message.attachments != []:
        embed.set_image(url = ctx.message.attachments[0].url)
    await ctx.send(embed = embed)

@client.command()
async def invite(ctx):
    view = discord.ui.View()
    view.add_item(discord.ui.Button(
        label = "Invite",
        url = "https://Senjibot.senjienji.repl.co/invite",
        style = discord.ButtonStyle.link
    ))
    await ctx.reply("<https://Senjibot.senjienji.repl.co/invite>", view = view)

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
Avatar URL: [Link]({user.avatar})
        """,
        color = 0xffe5ce
    ).set_image(
        url = user.avatar
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
        url = member.avatar
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
Icon URL: [Link]({guild.icon})
        """,
        color = 0xffe5ce
    ).set_image(
        url = guild.icon
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
Uptime: <t:{int(client.launch_time)}:R>
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
    if command.lower() in (command.name for command in client.commands):
        if command.lower() in ("enable", "disable", "help"):
            await ctx.reply("Cannot enable this command.")
        else:
            db["Enabled"][str(ctx.guild.id)][command.lower()] = True
            await ctx.reply(f'Command "{command.lower()}" enabled.')
    else:
        await ctx.reply(f'Command "{command.lower()}" not found.')

@client.command()
@commands.guild_only()
@commands.has_guild_permissions(manage_guild = True)
async def disable(ctx, command):
    if command.lower() in (command.name for command in client.commands):
        if command.lower() in ("enable", "disable", "help"):
            await ctx.reply("Cannot disable this command.")
        else:
            db["Enabled"][str(ctx.guild.id)][command.lower()] = False
            await ctx.reply(f'Command "{command.lower()}" disabled.')
    else:
        await ctx.reply(f'Command "{command.lower()}" not found.')

@client.command()
@commands.guild_only()
@commands.has_permissions(manage_messages = True)
@commands.bot_has_permissions(manage_messages = True, read_message_history = True)
async def purge(ctx, limit):
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
        db["Balance"][str(member.id)] = {"wallet": 0, "bank": 0}
    await ctx.reply(embed = discord.Embed(
        title = f"{member.display_name}'s Balance",
        description = f"""
Wallet: ${db['Balance'][str(member.id)]['wallet']}
Bank: ${db['Balance'][str(member.id)]['bank']}
        """,
        color = 0xffe5ce
    ).set_footer(
        text = ctx.author.display_name,
        icon_url = ctx.author.avatar
    ))

@client.command(aliases = ["dep"])
async def deposit(ctx, amount: int):
    if str(ctx.author.id) not in db["Balance"]:
        db["Balance"][str(ctx.author.id)] = {"wallet": 0, "bank": 0}
    if db["Balance"][str(ctx.author.id)]["wallet"] >= amount:
        db["Balance"][str(ctx.author.id)]["bank"] += amount
        db["Balance"][str(ctx.author.id)]["wallet"] -= amount
        await ctx.reply(f"Deposited ${amount}.")
    else:
        await ctx.reply("Not enough wallet money")

@client.command(aliases = ["with"])
async def withdraw(ctx, amount: int):
    if str(ctx.author.id) not in db["Balance"]:
        db["Balance"][str(ctx.author.id)] = {"wallet": 0, "bank": 0}
    if db["Balance"][str(ctx.author.id)]["bank"] >= amount:
        db["Balance"][str(ctx.author.id)]["wallet"] += amount
        db["Balance"][str(ctx.author.id)]["bank"] -= amount
        await ctx.reply(f"Withdrawn ${amount}.")
    else:
        await ctx.reply("Not enough bank balance")

@client.command(aliases = ["lb"])
@commands.guild_only()
async def leaderboard(ctx):
    await ctx.reply(embed = discord.Embed(
        title = "Leaderboard",
        description = "\n".join(f"{index}. `{member}`: ${amount}" for index, (member, amount) in enumerate(sorted(filter(lambda i: i[0] != None and i[1] > 0, ((ctx.guild.get_member(int(i[0])), i[1]["wallet"]) for i in db["Balance"].items())), key = lambda i: i[1], reverse = True), start = 1)),
        color = 0xffe5ce
    ).set_footer(
        text = ctx.author.display_name,
        icon_url = ctx.author.avatar
    ))

@client.command()
@commands.cooldown(rate = 1, per = 1 * 60 * 60, type = commands.BucketType.user)
async def work(ctx):
    if str(ctx.author.id) not in db["Balance"]:
        db["Balance"][str(ctx.author.id)] = {"wallet": 0, "bank": 0}
    gain = random.randint(500, 1000)
    db["Balance"][str(ctx.author.id)]["wallet"] += gain
    await ctx.reply(f"You got ${gain}.")

@client.command()
async def gamble(ctx, amount: int):
    if str(ctx.author.id) not in db["Balance"]:
        db["Balance"][str(ctx.author.id)] = {"wallet": 0, "bank": 0}
    if amount < 1:
        await ctx.reply("amount must be higher than 0.")
    elif db["Balance"][str(ctx.author.id)]["wallet"] >= amount:
        p1, p2 = (random.randint(2, 12), random.randint(2, 12))
        if p1 > p2:
            db["Balance"][str(ctx.author.id)]["wallet"] += amount
            content = f"You won ${amount}!"
        elif p1 < p2:
            db["Balance"][str(ctx.author.id)]["wallet"] -= amount
            content = f"You lost ${amount}."
        else:
            content = "It's a tie?"
        content += f"\n\n`{ctx.author.display_name}`: {p1}\n`{client.user.name}`: {p2}"
        await ctx.reply(content)
    else:
        await ctx.reply(f"You are ${amount - db['Balance'][str(ctx.author.id)]['wallet']} short.")

@client.command()
@commands.guild_only()
@commands.cooldown(rate = 1, per = 1 * 60 * 60, type = commands.BucketType.user)
async def rob(ctx, member: discord.Member):
    if str(ctx.author.id) not in db["Balance"]:
        db["Balance"][str(ctx.author.id)] = {"wallet": 0, "bank": 0}
    if str(member.id) not in db["Balance"]:
        db["Balance"][str(member.id)] = {"wallet": 0, "bank": 0}
    if db["Balance"][str(ctx.author.id)]["wallet"] >= 500:
        if db["Balance"][str(member.id)]["wallet"] >= 1000:
            if random.randint(1, 100) >= 50:
                gain = random.randint(1000, db["Balance"][str(member.id)]["wallet"])
                db["Balance"][str(ctx.author.id)]["wallet"] += gain
                db["Balance"][str(member.id)]["wallet"] -= gain
                await ctx.reply(f"Successfully robbed ${gain}.")
            else:
                db["Balance"][str(ctx.author.id)]["wallet"] -= 500
                await ctx.reply("You got caught and lost $500.")
        else:
            await ctx.reply("Your target has less than $1000.")
    else:
        await ctx.reply("You need at least $500 to rob someone.")

#Shop Commands
@client.group()
@commands.guild_only()
async def shop(ctx):
    if str(ctx.guild.id) not in db["Shop"]:
        db["Shop"][str(ctx.guild.id)] = {"nothing": 0} #{"name": price}
    if db["Shop"][str(ctx.guild.id)] == {}:
        db["Shop"][str(ctx.guild.id)] = {"nothing": 0}
    if ctx.invoked_subcommand == None:
        menu = discord.ui.Select(placeholder = "Select an item")
        for name, price in db["Shop"][str(ctx.guild.id)].items():
            menu.add_option(
                label = f"{name}: ${price}",
                value = name
            )
        view = discord.ui.View(timeout = 1 * 60 * 60)
        view.add_item(menu)
        message = await ctx.reply("Shop", view = view)
        while True:
            try:
                interaction = await client.wait_for("interaction", check = lambda interaction: interaction.message == message, timeout = 1 * 60 * 60)
                if str(interaction.user.id) not in db["Balance"]:
                    db["Balance"][str(interaction.user.id)] = {"wallet": 0, "bank": 0}
                if db["Balance"][str(interaction.user.id)]["wallet"] >= db["Shop"][str(ctx.guild.id)][view.children[0].values[0]]:
                    db["Balance"][str(interaction.user.id)]["wallet"] -= db["Shop"][str(ctx.guild.id)][view.children[0].values[0]]
                    await interaction.followup.send(f'{interaction.user.mention} item "{view.children[0].values[0]}" purchased.')
                else:
                    await interaction.followup.send(f"You are ${db['Shop'][str(ctx.guild.id)][view.children[0].values[0]] - db['Balance'][str(interaction.user.id)]['wallet']} short.", ephemeral = True)
            except __import__("asyncio").TimeoutError:
                view.children[0].disable = True
                view.stop()
                break

@shop.command()
@commands.has_guild_permissions(manage_guild = True)
async def add(ctx, name, price: int):
    if name not in db["Shop"][str(ctx.guild.id)]:
        if price >= 0:
            db["Shop"][str(ctx.guild.id)][name] = price
            await ctx.reply(f'Item "{name}" added.')
        else:
            await ctx.reply("price must be greater than or equal to 0.")
    else:
        await ctx.reply(f'Item "{name}" is already added.')

@shop.command()
@commands.has_guild_permissions(manage_guild = True)
async def edit(ctx, name, other):
    if name in db["Shop"][str(ctx.guild.id)]:
        if other.isnumeric():
            db["Shop"][str(ctx.guild.id)][name] = int(other)
            await ctx.reply(f'Item "{name}" edited.')
        else:
            db["Shop"][str(ctx.guild.id)][other] = db["Shop"][str(ctx.guild.id)][name]
            del db["Shop"][str(ctx.guild.id)][name]
            await ctx.reply(f'Item "{name}" edited to "{other}".')
    else:
        await ctx.reply(f'Item "{name}" not found.')

@shop.command()
@commands.has_guild_permissions(manage_guild = True)
async def remove(ctx, *, name):
    if name in db["Shop"][str(ctx.guild.id)]:
        del db["Shop"][str(ctx.guild.id)][name]
        await ctx.reply(f'Item "{name}" removed.')
    else:
        await ctx.reply(f'Item "{name}" not found.')
#Private Commands
@client.command(hidden = True)
@commands.is_owner()
async def doc(ctx, *, search = ""):
    if search == "":
        await ctx.reply("https://discordpy.readthedocs.io/en/master/api.html")
    else:
        await ctx.reply(f"https://discordpy.readthedocs.io/en/master/search.html?q={search.replace(' ', '+')}")

@client.command(hidden = True)
@commands.is_owner()
async def set(ctx, member: discord.Member, type, amount: int):
    try:
        db["Balance"][str(member.id)][type] = amount
        await ctx.reply(f"`{member}`'s {type} balance has been set to ${amount}.")
    except KeyError:
        await ctx.reply("invalid type")

@client.command(name = "exec", hidden = True)
@commands.is_owner()
async def execute(ctx, *, content):
    exec(content)
    await ctx.reply("done")

@client.command(hidden = True)
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