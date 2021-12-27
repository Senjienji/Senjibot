import discord
from discord.ext import commands
from replit import db

if "Prefix" not in db:
    db["Prefix"] = {}
if "Enabled" not in db:
    db["Enabled"] = {}

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    @commands.has_guild_permissions(kick_members = True)
    @commands.bot_has_guild_permissions(kick_members = True)
    async def kick(self, ctx, member: discord.Member, *, reason = "no reason"):
        await ctx.guild.kick(member, reason = f"By {ctx.author} for {reason}.")
        await ctx.reply(f"`{member}` kicked for {reason}.")
    
    @commands.command()
    @commands.has_guild_permissions(ban_members = True)
    @commands.bot_has_guild_permissions(ban_members = True)
    async def ban(self, ctx, user: discord.User, *, reason = "no reason"):
        await ctx.guild.ban(user, reason = f"By {ctx.author} for {reason}", delete_message_days = 0)
        await ctx.reply(f"`{user}` banned for {reason}.")

    @commands.command()
    @commands.has_guild_permissions(ban_members = True)
    @commands.bot_has_guild_permissions(ban_members = True)
    async def unban(self, ctx, *, user: discord.User):
        await ctx.guild.unban(user)
        await reply(f"`{user}` unbanned.")
    
    @commands.command()
    async def prefix(self, ctx, prefix = None):
        if prefix == None:
            await ctx.reply(f"My current prefix is `{self.client.command_prefix(self.client, ctx.message)}`.")
        elif ctx.author.guild_permissions.manage_guild:
            db["Prefix"][str(ctx.guild.id)] = prefix
            await ctx.reply(f"Prefix has been changed to `{self.client.command_prefix(self.client, ctx.message)}`.")
        else:
            raise commands.MissingPermissions(["manage_guild"])
    
    @commands.command()
    @commands.has_guild_permissions(manage_guild = True)
    async def enable(self, ctx, command):
        if command.lower() in (command.name for command in self.bot.commands):
            if command.lower() in ("enable", "disable", "help"):
                await ctx.reply("Cannot enable this command.")
            else:
                db["Enabled"][str(ctx.guild.id)][command.lower()] = True
                await ctx.reply(f'Command "{command.lower()}" enabled.')
        else:
            await ctx.reply(f'Command "{command.lower()}" not found.')
    
    @commands.command()
    @commands.has_guild_permissions(manage_guild = True)
    async def disable(self, ctx, command):
        if command.lower() in (command.name for command in self.bot.commands):
            if command.lower() not in ("enable", "disable", "help"):
                db["Enabled"][str(ctx.guild.id)][command.lower()] = False
                await ctx.reply(f'Command "{command.lower()}" disabled.')
            else:
                await ctx.reply(f"Cannot disable this command.")
        else:
            await ctx.reply(f'Command "{command.lower()}" not found.')
    
    @commands.command()
    @commands.has_permissions(manage_messages = True)
    @commands.bot_has_permissions(manage_messages = True, read_message_history = True)
    async def purge(self, ctx, limit: int):
        await ctx.message.delete()
        purge = await ctx.channel.purge(limit = limit)
        await ctx.send(f"Purged {len(purge)} message{'s' if len(purge) != 1 else str()}.", delete_after = 3)

def setup(bot):
    bot.add_cog(Moderation(bot))