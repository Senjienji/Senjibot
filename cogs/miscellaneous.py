import discord
from discord.ext import commands
from replit import db
import random
import time

if 'Snipe' not in db:
    db['Snipe'] = {} #{'channel.id': ['user.id', 'content', 'timestamp']}

class Miscellaneous(commands.Cog):
    @commands.command(name = 'eval')
    async def evaluate(self, ctx, *, content):
        await ctx.reply(embed = discord.Embed(
            title = 'Evaluation',
            description = str(eval(content, {
                'ctx': ctx,
                'discord': discord,
                'timestamp': time.time,
                'choose': random.choice,
                'math': __import__('math'),
                'shuffle': lambda x: random.sample(x, len(x)),
                'db': discord.utils.json.loads(db.dumps(dict(db))),
            }, {
                '__import__': None,
                'copyright': None,
                'credits': None,
                'license': None,
                'print': None,
                'eval': None,
                'exec': None,
                'help': None,
                'exit': None,
                'quit': None,
                'open': None
            })),
            color = 0xffe5ce
        ).set_footer(
            text = ctx.author.display_name,
            icon_url = ctx.author.display_avatar.url
        ))
    
    @commands.command()
    async def math(self, ctx):
        equation = f'{random.randint(1, 99)} {random.choice(("+", "-", "*", "%", "//"))} {random.randint(1, 99)}'
        reply = await ctx.reply(f'{equation} = ?')
        try:
            message = await ctx.bot.wait_for('message', check = lambda message: message.channel == ctx.channel and message.author == ctx.author, timeout = 60)
            embed = discord.Embed(
                description = f'{equation} = {eval(equation)}',
                color = 0xffe5ce
            ).set_footer(
                text = f'{int((message.created_at - reply.created_at).total_seconds())} seconds'
            )
            try:
                if int(message.content) == eval(equation):
                    embed.title = 'Correct!'
                else:
                    embed.title = 'Wrong!'
            except ValueError:
                embed.title = 'Invalid number passed.'
            await message.reply(embed = embed)
        except discord.utils.asyncio.TimeoutError:
            await reply.edit(content = f"{equation} = {eval(equation)}\nYou didn't reply in time.")
    
    @commands.command(description = 'Tic Tac Toe', hidden = True)
    async def ttt(self, ctx):
        board = (
            [None, None, None],
            [None, None, None],
            [None, None, None]
        )
        attempt = 1
        view = discord.ui.View(timeout = 60)
        for y in range(len(board)):
            for x in range(len(board[y])):
                view.add_item(discord.ui.Button(
                    label = ' ',
                    custom_id = str(x + y * len(board[y])),
                    row = y
                ))
        message = await ctx.reply('Select a box', view = view)
        while True:
            try:
                interaction = await ctx.bot.wait_for('interaction', check = lambda interaction: interaction.message == message and board[int(interaction.data['custom_id']) // len(board)][int(interaction.data['custom_id']) % len(board)] == None, timeout = 60)
                board[int(interaction.data['custom_id']) // len(board)][int(interaction.data['custom_id']) % len(board)] = '❌' if attempt % 2 else '⭕'
                view.clear_items()
                for y in range(len(board)):
                    for x in range(len(board[y])):
                        view.add_item(discord.ui.Button(
                            label = str() if board[y][x] else ' ',
                            emoji = board[y][x],
                            custom_id = str(x + y * len(board[y])),
                            row = y
                        ))
                await message.edit(view = view)
                attempt += 1
            except discord.utils.asyncio.TimeoutError:
                view.stop()
                break
    
    @commands.command()
    async def menu(self, ctx):
        view = discord.ui.View(timeout = 60)
        view.add_item(discord.ui.Select(options = [discord.SelectOption(
            label = 'Option 1',
            emoji = '1️⃣'
        ), discord.SelectOption(
            label = 'Option 2',
            emoji = '2️⃣'
        ), discord.SelectOption(
            label = 'Option 3',
            emoji = '3️⃣'
        )]))
        message = await ctx.reply('Menu', view = view)
        while True:
            try:
                interaction = await ctx.bot.wait_for('interaction', check = lambda interaction: interaction.message == message, timeout = 60)
                await interaction.followup.send(interaction.data, ephemeral = True)
            except discord.utils.asyncio.TimeoutError:
                await message.edit(view = None)
                view.stop()
                break
    
    @commands.command()
    async def rps(self, ctx, member: discord.Member = None):
        if member == None:
            member = ctx.me
        if member == ctx.author:
            return await ctx.reply('No')
        view = discord.ui.View(timeout = 60)
        view.add_item(discord.ui.Button(
            label = 'Rock',
            emoji = '🪨',
            custom_id = 'Rock'
        ))
        view.add_item(discord.ui.Button(
            label = 'Paper',
            emoji = '📄',
            custom_id = 'Paper'
        ))
        view.add_item(discord.ui.Button(
            label = 'Scissors',
            emoji = '✂️',
            custom_id = 'Scissors'
        ))
        message = await ctx.reply(f'`{ctx.author.display_name}` is choosing...\n`{member.display_name}` is choosing...', view = view)
        p1, p2 = (None, None)
        if member.bot:
            p2 = random.randint(0, 2)
            await message.edit(content = message.content.split('\n')[0] + f'\n`{member.display_name}` is ready!')
        while True:
            try:
                interaction = await ctx.bot.wait_for('interaction', check = lambda interaction: interaction.message == message and interaction.user in (ctx.author, member), timeout = 60)
                moves = ('Rock', 'Paper', 'Scissors')
                if interaction.user == ctx.author:
                    if p1 == None:
                        p1 = moves.index(interaction.data['custom_id'])
                        await message.edit(content = f'\n`{ctx.author.display_name}` is ready!\n' + message.content.split('\n')[1])
                    else:
                        await interaction.followup.send("You can't change your move.", ephemeral = True)
                elif interaction.user == member:
                    if p2 == None:
                        p2 = moves.index(interaction.data['custom_id'])
                        await message.edit(content = message.content.split('\n')[0] + f'\n`{member.display_name}` is ready!')
                    else:
                        await interaction.followup.send("You can't change your move.", ephemeral = True)
                if p1 != None and p2 != None:
                    if p1 - p2 in (-2, 1):
                        content = f'{ctx.author.display_name} won!'
                    elif p1 - p2 in (-1, 2):
                        content = f'{member.display_name} won!'
                    else:
                        content = "It's a tie!"
                    content += f'\n\n`{ctx.author.display_name}`: {moves[p1]}\n`{member.display_name}`: {moves[p2]}'
                    await message.edit(content = content, view = None)
                    break
                else:
                    continue
            except discord.utils.asyncio.TimeoutError:
                await message.edit(content = 'You took too long to respond.', view = None)
                view.stop()
                break
    
    @commands.command(aliases = ['cd'])
    async def cooldown(self, ctx):
        await ctx.reply(embed = discord.Embed(
            title = 'Cooldowns',
            description = '\n'.join(f'{index}. `{command.name}`: <t:{int(time.time() + command.get_cooldown_retry_after(ctx))}:F>' for index, command in enumerate(filter(lambda command: command.is_on_cooldown(ctx), ctx.bot.commands), start = 1)) or 'Nothing found.',
            color = 0xffe5ce
        ).set_footer(
            text = ctx.author.display_name,
            icon_url = ctx.author.display_avatar.url
        ))

    @commands.command()
    async def say(self, ctx, *, content):
        await ctx.send(content)
    
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
    
    @commands.command()
    async def invite(self, ctx):
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            label = 'Invite',
            url = 'https://Senjibot.senjienji.repl.co/invite',
            style = discord.ButtonStyle.link
        ))
        await ctx.reply('<https://Senjibot.senjienji.repl.co/invite>', view = view)
    
    @commands.command()
    async def bot(self, ctx):
        await ctx.bot.wait_until_ready()
        await ctx.reply(embed = discord.Embed(
            title = 'Bot Info',
            description = f'''
In: {len(ctx.bot.guilds)} guilds
Latency: {int(ctx.bot.latency * 1000)}ms
Uptime: {discord.utils.format_dt(ctx.bot.launch_time, "R")}
Version: {discord.__version__}
            ''',
            color = 0xffe5ce
        ).set_footer(
            text = ctx.author.display_name,
            icon_url = ctx.author.display_avatar.url
        ))
    
    @commands.command()
    async def emoji(self, ctx, *, emoji: discord.Emoji):
        view = discord.ui.View(timeout = None)
        view.add_item(discord.ui.Button(
            label = 'Link',
            url = emoji.url,
            style = discord.ButtonStyle.link
        ))
        await ctx.reply(embed = discord.Embed(
            title = f'{emoji.name}.{"gif" if emoji.animated else "png"}',
            description = f'[Link]({emoji.url})',
            color = 0xffe5ce
        ).set_image(
            url = emoji.url
        ).set_footer(
            text = ctx.author.display_name,
            icon_url = ctx.author.display_avatar.url
        ), view = view)
    
    @commands.command()
    async def poll(self, ctx, name, *options):
        message = await ctx.send(embed = discord.Embed(
            title = f'Poll: {name}',
            description = '\n'.join(f'{index}. {option}' for index, option in enumerate(options[:10], start = 1)),
            color = 0xffe5ce
        ).set_footer(
            text = f'By {ctx.author}',
            icon_url = ctx.author.display_avatar.url
        ))
        for i in range(len(options[:10])):
            await message.add_reaction('1️⃣ 2️⃣ 3️⃣ 4️⃣ 5️⃣ 6️⃣ 7️⃣ 8️⃣ 9️⃣ 🔟'.split()[i])
    
    @commands.command()
    async def avatar(self, ctx, *, user: discord.User = None):
        if user == None:
            user = ctx.author
        view = discord.ui.View(timeout = None)
        view.add_item(discord.ui.Button(
            label = 'Link',
            url = user.display_avatar.url,
            style = discord.ButtonStyle.link
        ))
        await ctx.reply(embed = discord.Embed(
            title = f'{user.display_name}.{"gif" if user.display_avatar.is_animated() else "png"}',
            description = f'[Link]({user.display_avatar.url})',
            color = 0xffe5ce
        ).set_image(
            url = user.display_avatar.url
        ).set_footer(
            text = ctx.author.display_name,
            icon_url = ctx.author.display_avatar.url
        ), view = view)

    @commands.Cog.listener() 
    async def on_message_delete(self, message):
        db['Snipe'][str(message.channel.id)] = [message.author.id, message.content, message.created_at.timestamp()]
    
    @commands.command()
    async def snipe(self, ctx):
        if str(ctx.channel.id) in db['Snipe']:
            await ctx.reply(embed = discord.Embed(
                title = f'By {ctx.guild.get_member(db["Snipe"][str(ctx.channel.id)][0])}',
                description = db['Snipe'][str(ctx.channel.id)][1],
                timestamp = __import__('datetime').datetime.fromtimestamp(db['Snipe'][str(ctx.channel.id)][2]),
                color = 0xffe5ce
            ))
        else:
            await ctx.reply('Nothing found.')

def setup(bot):
    bot.add_cog(Miscellaneous())
    bot.help_command.cog = Miscellaneous()