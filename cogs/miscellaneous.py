import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import os

class Miscellaneous(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self.bot.tree.add_command(app_commands.ContextMenu(
            name = 'Avatar',
            callback = self.avatar_callback,
        ))
    
    @app_commands.command(description = 'Sends your text')
    @app_commands.describe(
       content = 'The text to send',
       channel = 'Where to send the text'
    )
    async def say(self, inter, content, channel: Optional[discord.TextChannel]):
        if channel == None:
            channel = inter.channel
        if channel.permissions_for(inter.user).send_messages:
            await channel.send('> ' + '\n> '.join(content.split()) + f'\n-{inter.user.mention}')
            await inter.response.send_message('Message sent.', ephemeral = True)
        else:
            await inter.response.send_message('Missing `Send Messages` permission.', ephemeral = True)
    
    @app_commands.command(description = 'Shows the information of Senjibot')
    async def bot(self, inter):
        await inter.response.send_message(embed = discord.Embed(
            title = 'Bot Info',
            description = f'''
In: {len(self.bot.guilds)} servers
Latency: {int(self.bot.latency * 1000)}ms
Uptime: {discord.utils.format_dt(self.bot.launch_time, "R")}
Version: {discord.__version__}''',
            color = 0xffe5ce
        ).set_author(
            name = inter.user.display_name,
            url = f'https://discord.com/users/{inter.user.id}',
            icon_url = inter.user.display_avatar.url
        ))
    
    @app_commands.command(description = 'Shows the emoji image')
    @app_commands.describe(emoji = 'The emoji to show')
    async def emoji(self, ctx, emoji: discord.Emoji):
        await inter.response.send_message(embed = discord.Embed(
            title = f'{emoji.name}.{"gif" if emoji.animated else "png"}',
            description = f'[Link]({emoji.url})',
            color = 0xffe5ce
        ).set_image(
            url = emoji.url
        ).set_author(
            name = inter.user.display_name,
            url = f'https://discord.com/users/{inter.user.id}',
            icon_url = inter.user.display_avatar.url
        ), view = discord.ui.View().add_item(discord.ui.Button(
            label = 'Link',
            url = emoji.url,
            style = discord.ButtonStyle.link
        )))

    @app_commands.command(description = "Shows an user's avatar")
    @app_commands.describe(user = 'The user to show')
    async def avatar(self, inter, user: Optional[discord.User]):
        if user == None:
            user = inter.user
        await inter.response.send_message(embed = discord.Embed(
            title = f'{user.display_name}.{"gif" if user.display_avatar.is_animated() else "png"}',
            description = f'[Link]({user.display_avatar.url})',
            color = 0xffe5ce
        ).set_image(
            url = user.display_avatar.url
        ).set_author(
            name = inter.user.display_name,
            url = f'https://discord.com/users/{inter.user.id}',
            icon_url = inter.user.display_avatar.url
        ), view = discord.ui.View().add_item(discord.ui.Button(
            label = 'Link',
            url = user.display_avatar.url,
            style = discord.ButtonStyle.link
        )))
    
    async def avatar_callback(self, inter: discord.Interaction, member: discord.Member):
        await inter.response.send_message(embed = discord.Embed(
            title = f'{member.display_name}.{"gif" if member.display_avatar.is_animated() else "png"}',
            description = f'[Link]({member.display_avatar.url})',
            color = 0xffe5ce
        ).set_image(
            url = member.display_avatar.url
        ).set_author(
            name = inter.user.display_name,
            url = f'https://discord.com/users/{inter.user.id}',
            icon_url = inter.user.display_avatar.url
        ), view = discord.ui.View().add_item(discord.ui.Button(
            label = 'Link',
            url = member.display_avatar.url,
            style = discord.ButtonStyle.link
        )))
    
    @app_commands.command(description = 'Shows the icon of a server')
    @app_commands.describe(server = 'The server to show')
    async def icon(self, inter, server: Optional[discord.Guild]):
        if server == None:
            server = inter.guild
        await inter.response.send_message(embed = discord.Embed(
            title = f'{guild.name}.{"gif" if guild.icon.is_animated() else "png"}',
            description = f'[Link][{guild.icon.url}]',
            color = 0xffe5ce
        ).set_image(
            url = guild.icon.url
        ).set_author(
            name = inter.user.display_name,
            url = f'https://discord.com/users/{inter.user.id}',
            icon_url = inter.user.display_avatar.url
        ), view = discord.ui.View().add_item(discord.ui.Button(
            label = 'Link',
            url = guild.icon.url,
            style = discord.ButtonStyle.link
        )))
    
    @app_commands.command(description = 'Sends a poll for everyone to vote')
    @app_commands.describe(
        title = 'The title of the poll',
        channel = 'Where to post the poll',
        options = 'Separate options with a new line'
    )
    async def poll(self, inter, title, channel: Optional[discord.TextChannel], options):
        if channel == None:
            channel = inter.channel
        options = options.split()[:10]
        if channel.permissions_for(inter.user).send_messages:
            message = await channel.send(embed = discord.Embed(
                title = title,
                description = '\n'.join(f'{"1️⃣ 2️⃣ 3️⃣ 4️⃣ 5️⃣ 6️⃣ 7️⃣ 8️⃣ 9️⃣ 🔟".split()[i]} {option}' for i, option in enumerate(options)),
                color = 0xffe5ce
            ).set_author(
                name = str(inter.user),
                url = 'https://discord.com/users/{inter.user.id}',
                icon_url = inter.user.display_avatar.url
            ))
            for i in range(len(options)):
                await message.add_reaction('1️⃣ 2️⃣ 3️⃣ 4️⃣ 5️⃣ 6️⃣ 7️⃣ 8️⃣ 9️⃣ 🔟'.split()[i])
            await inter.response.send_message('Poll sent.', ephemeral = True)
        else:
            await inter.response.send_message('Missing `Send Messages` permission', ephemeral = True)

async def setup(bot):
    await bot.add_cog(Miscellaneous(bot))
    bot.help_command.cog = Miscellaneous(bot)
