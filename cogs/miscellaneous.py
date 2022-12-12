import discord
from discord.ext import commands
from typing import Optional
import time
import os

class Miscellaneous(commands.Cog):
    @commands.command(aliases = ['cd'])
    async def cooldown(self, ctx):
        await ctx.reply(embed = discord.Embed(
            title = 'Cooldowns',
            description = '\n'.join(
                f'{index}. `{command.name}`: <t:{int(time.time() + command.get_cooldown_retry_after(ctx))}:F>' for index, command in enumerate(
                    filter(
                        lambda command: command.is_on_cooldown(ctx),
                        ctx.bot.commands
                    ),
                    start = 1
                )
            ) or 'Nothing found.',
            color = 0xffe5ce
        ).set_author(
            name = ctx.author,
            url = f'https://discord.com/users/{ctx.author.id}',
            icon_url = ctx.author.display_avatar.url
        ))

    @commands.command()
    async def say(self, ctx, channel: Optional[discord.TextChannel], *, content):
        if channel == None:
            channel = ctx.channel
        if not channel.permissions_for(ctx.author).send_messages:
            raise commands.MissingPermissions(['send_messages'])
        
        await channel.send('> ' + '\n> '.join(content.split()) + f'\n- {ctx.author.mention}')
        await ctx.reply('Message sent.')
    
    @commands.command(enabled = False)
    async def invite(self, ctx):
        await ctx.reply(
            '<https://Senjibot.up.railway.app/invite>',
            view = discord.ui.View().add_item(discord.ui.Button(
                label = 'Link',
                url = 'https://Senjibot.up.railway.app/invite',
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
        ).set_author(
            name = ctx.author,
            url = f'https://discord.com/users/{ctx.author.id}',
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
        ).set_author(
            name = ctx.author,
            url = f'https://discord.com/users/{ctx.author.id}',
            icon_url = ctx.author.display_avatar.url
        ), view = discord.ui.View().add_item(discord.ui.Button(
            label = 'Link',
            url = emoji.url,
            style = discord.ButtonStyle.link
        )))

    @commands.command()
    async def avatar(self, ctx, *, user: Optional[discord.User]):
        if user == None:
            user = ctx.author
        await ctx.reply(embed = discord.Embed(
            title = f'{user.display_name}.{"gif" if user.display_avatar.is_animated() else "png"}',
            description = f'[Link]({user.display_avatar.url})',
            color = 0xffe5ce
        ).set_image(
            url = user.display_avatar.url
        ).set_author(
            name = ctx.author,
            url = f'https://discord.com/users/{ctx.author.id}',
            icon_url = ctx.author.display_avatar.url
        ), view = discord.ui.View().add_item(discord.ui.Button(
            label = 'Link',
            url = user.display_avatar.url,
            style = discord.ButtonStyle.link
        )))
    
    @commands.command()
    async def icon(self, ctx, *, server: Optional[discord.Guild]):
        if server == None:
            server = ctx.guild
        await ctx.reply(embed = discord.Embed(
            title = f'{server.name}.{"gif" if server.icon.is_animated() else "png"}',
            description = f'[Link]({server.icon.url})',
            color = 0xffe5ce
        ).set_image(
            url = server.icon.url
        ).set_author(
            name = ctx.author,
            url = f'https://discord.com/users/{ctx.author.id}',
            icon_url = ctx.author.display_avatar.url
        ), view = discord.ui.View().add_item(discord.ui.Button(
            label = 'Link',
            url = server.icon.url,
            style = discord.ButtonStyle.link
        )))
    
    @commands.command(brief = 'Separate options with a new line')
    async def poll(self, ctx, channel: Optional[discord.TextChannel], title, *, options):
        if channel == None:
            channel = ctx.channel
        if not channel.permissions_for(ctx.author).send_messages:
            raise commands.MissingPermissions(['send_messages'])
        options = options.split('\n')[:10]
        if len(options) < 2:
            return await ctx.reply('`options` must be at least 2.')
        
        message = await channel.send(embed = discord.Embed(
            title = title,
            description = '\n'.join(f'{"1️⃣ 2️⃣ 3️⃣ 4️⃣ 5️⃣ 6️⃣ 7️⃣ 8️⃣ 9️⃣ 🔟".split()[i]} {option}' for i, option in enumerate(options)),
            color = 0xffe5ce
        ).set_author(
            name = ctx.author,
            url = f'https://discord.com/users/{ctx.author.id}',
            icon_url = ctx.author.display_avatar.url
        ))
        for i in range(len(options)):
            await message.add_reaction('1️⃣ 2️⃣ 3️⃣ 4️⃣ 5️⃣ 6️⃣ 7️⃣ 8️⃣ 9️⃣ 🔟'.split()[i])
        if channel != ctx.channel:
            await ctx.reply('Poll sent.')

async def setup(bot):
    await bot.add_cog(Miscellaneous())
    bot.help_command.cog = Miscellaneous()
