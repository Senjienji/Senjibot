import discord
from discord.ext import commands
#from replit import db
import random
import time

'''
if 'Snipe' not in db:
    db['Snipe'] = {} #{'channel.id': [user.id, 'content', 'timestamp']}f
'''

class Miscellaneous(commands.Cog):
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
    
    '''
    @commands.command()
    async def prefix(self, ctx, prefix = None):
        if prefix == None:
            await ctx.reply(f'My current prefix is `{ctx.bot.command_prefix(ctx.bot, ctx.message)}`.')
        elif ctx.author.guild_permissions.manage_guild:
            db['Prefix'][str(ctx.guild.id)] = prefix
            await ctx.reply(f'Prefix has been changed to `{ctx.bot.command_prefix(ctx.bot, ctx.message)}`.')
        else:
            raise commands.MissingPermissions(['manage_guild'])
    '''
    
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
    async def invite(self, ctx):
        await ctx.reply(
            '<https://Senjibot.senjienji.repl.co/invite>',
            view = discord.ui.View().add_item(discord.ui.Button(
                label = 'Link',
                url = 'https://Senjibot.senjienji.repl.co/invite',
                style = discord.ButtonStyle.link
            ))
        )
    
    @commands.command()
    async def bot(self, ctx):
        await ctx.reply(embed = discord.Embed(
            title = 'Bot Info',
            description = f'''
In: {len(ctx.bot.guilds)} guilds
Latency: {int(ctx.bot.latency * 1000)}ms
Uptime: {discord.utils.format_dt(ctx.bot.launch_time, "R")}
Version: {discord.__version__}''',
            color = 0xffe5ce
        ).set_footer(
            text = ctx.author.display_name,
            icon_url = ctx.author.display_avatar.url
        ))
    
    @commands.command()
    async def emoji(self, ctx, *, emoji: discord.Emoji):
        await ctx.reply(embed = discord.Embed(
            title = f'{emoji.name}.{"gif" if emoji.animated else "png"}',
            description = f'[Link]({emoji.url})',
            color = 0xffe5ce
        ).set_image(
            url = emoji.url
        ).set_footer(
            text = ctx.author.display_name,
            icon_url = ctx.author.display_avatar.url
        ), view = discord.ui.View().add_item(discord.ui.Button(
            label = 'Link',
            url = emoji.url,
            style = discord.ButtonStyle.link
        )))

    @commands.command()
    async def avatar(self, ctx, *, user: discord.User = None):
        if user == None:
            user = ctx.author
        await ctx.reply(embed = discord.Embed(
            title = f'{user.display_name.replace(" ", "+")}.{"gif" if user.display_avatar.is_animated() else "png"}',
            description = f'[Link]({user.display_avatar.url})',
            color = 0xffe5ce
        ).set_image(
            url = user.display_avatar.url
        ).set_footer(
            text = ctx.author.display_name,
            icon_url = ctx.author.display_avatar.url
        ), view = discord.ui.View().add_item(discord.ui.button(
            label = 'Link',
            url = user.display_avatar.url,
            style = discord.ButtonStyle.link
        )))
    
    @commands.command()
    async def poll(self, ctx, name, *options):
        if options == ():
            param = __import__('inspect').Parameter
            raise commands.MissingRequiredArgument(param('options', param.VAR_POSITIONAL))
        message = await ctx.send(embed = discord.Embed(
            title = f'Poll: {name}',
            description = '\n'.join(f'{"1️⃣ 2️⃣ 3️⃣ 4️⃣ 5️⃣ 6️⃣ 7️⃣ 8️⃣ 9️⃣ 🔟".split()[i]} {option}' for i, option in enumerate(options[:10])),
            color = 0xffe5ce
        ).set_footer(
            text = f'By {ctx.author}',
            icon_url = ctx.author.display_avatar.url
        ))
        for i in range(len(options[:10])):
            await message.add_reaction('1️⃣ 2️⃣ 3️⃣ 4️⃣ 5️⃣ 6️⃣ 7️⃣ 8️⃣ 9️⃣ 🔟'.split()[i])

'''
    @commands.Cog.listener() 
    async def on_message_delete(self, message):
        db['Snipe'][str(message.channel.id)] = [message.author.id, message.content, message.created_at.timestamp(), message.attachments[0].url if len(message.attachments) > 0 else None]
    
    @commands.command()
    async def snipe(self, ctx, channel: discord.TextChannel = None):
        if channel == None:
            channel = ctx.channel
        if str(channel.id) in db['Snipe']:
            embed = discord.Embed(
                title = f'By {ctx.guild.get_member(db["Snipe"][str(channel.id)][0])}',
                description = db['Snipe'][str(channel.id)][1],
                timestamp = __import__('datetime').datetime.fromtimestamp(db['Snipe'][str(channel.id)][2]),
                color = 0xffe5ce
            )
            if db['Snipe'][str(channel.id)][3]:
                embed.set_image(url = db['Snipe'][str(channel.id)][3])
            await ctx.reply(embed = embed)
        else:
            await ctx.reply('Nothing found.')
'''

async def setup(bot):
    await bot.add_cog(Miscellaneous())
    bot.help_command.cog = Miscellaneous()
