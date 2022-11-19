import discord
from discord.ext import commands
import datetime

class Moderation(commands.Cog):
    @commands.command()
    @commands.has_guild_permissions(kick_members = True)
    @commands.bot_has_guild_permissions(kick_members = True)
    async def kick(self, ctx, member: discord.Member, *, reason = 'no reason'):
        await ctx.guild.kick(member, reason = f'By {ctx.author} for {reason}.')
        await ctx.reply(f'`{member}` kicked for {reason}.')
    
    @commands.command()
    @commands.has_guild_permissions(ban_members = True)
    @commands.bot_has_guild_permissions(ban_members = True)
    async def ban(self, ctx, user: discord.User, *, reason = 'no reason'):
        await ctx.guild.ban(user, reason = f'By {ctx.author} for {reason}', delete_message_days = 0)
        await ctx.reply(f'`{user}` banned for {reason}.')
    
    @commands.command()
    @commands.has_guild_permissions(ban_members = True)
    @commands.bot_has_guild_permissions(ban_members = True)
    async def unban(self, ctx, *, user: discord.User):
        await ctx.guild.unban(user)
        await ctx.reply(f'`{user}` unbanned.')
    
    @commands.command()
    @commands.has_permissions(manage_messages = True)
    @commands.bot_has_permissions(manage_messages = True, read_message_history = True)
    async def purge(self, ctx, limit: int):
        await ctx.message.delete()
        purge = await ctx.channel.purge(limit = limit)
        await ctx.send(f'Purged {len(purge)} message{str() if len(purge) == 1 else "s"}.', delete_after = 3)
    
    @commands.command(aliases = ['mute'])
    @commands.has_permissions(moderate_members = True)
    @commands.bot_has_permissions(moderate_members = True)
    async def timeout(self, ctx, member: discord.Member, seconds: int = None):
        if seconds == None:
            await member.timeout(None, reason = f'By {ctx.author}')
            await ctx.reply(f"`{member}`'s timeout has been removed.")
        else:
            await member.timeout(datetime.timedelta(seconds = seconds), reason = f'By {ctx.author}')
            await ctx.reply(f'`{member}` is timed out until {discord.utils.format_dt(datetime.datetime.today() + datetime.timedelta(seconds = seconds), "D")}.')

async def setup(bot):
    await bot.add_cog(Moderation())
