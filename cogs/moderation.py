import discord
from discord.ext import commands
import datetime
import pymongo
import os

client = pymongo.MongoClient(
    f'mongodb+srv://Senjienji:{os.getenv("PASSWORD")}@senjienji.czypcav.mongodb.net/?retryWrites=true&w=majority',
    server_api = pymongo.server_api.ServerApi('1'),
)
db = client.senjibot
rr_col = db.reaction_roles
prefix_col = db.prefix

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
    
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
    
    @commands.command()
    async def prefix(self, ctx, prefix = None):
        if prefix == None:
            await ctx.reply(f'My current prefix is `{ctx.bot.command_prefix(ctx.bot, ctx.message)}`.')
        elif ctx.author.guild_permissions.manage_guild:
            prefix_col.find_one_and_update(
                {'guild': ctx.guild.id},
                {'$set': {'prefix': prefix}}
            )
            await ctx.reply(f'Prefix has been changed to `{ctx.bot.command_prefix(ctx.bot, ctx.message)}`.')
        else:
            raise commands.MissingPermissions(['manage_guild'])
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        print(f'{payload.emoji = }')
        guild = self.bot.get_guild(payload.guild_id)
        if guild == None: return
        
        doc = rr_col.find_one({'guild': guild.id})
        if doc == None: return
        
        member = payload.member
        rr = doc['reaction_roles']
        if str(payload.message_id) in rr:
            type = rr[str(payload.message_id)]['type']
            if str(payload.emoji) in rr[str(payload.message_id)]:
                role = guild.get_role(rr[str(payload.message_id)][str(payload.emoji)])
                if type == 0: #normal
                    await member.add_roles(role)
                elif type == 1: #unique
                    await member.add_roles(role)
                    message = await guild.get_channel(payload.channel_id).fetch_message(payload.message_id)
                    for reaction in message.reactions:
                        print(f'{reaction.emoji = }')
                        print(f'{reaction.emoji == payload.emoji}')
                        if reaction.emoji != payload.emoji and str(reaction.emoji) in rr[str(payload.message_id)]:
                            async for user in reaction.users():
                                if user == member:
                                    await message.remove_reaction(reaction.emoji, member)
                                    break
                elif type == 2: #reversed
                    await member.remove_roles(role)
                elif type == 3: #verify
                    await member.add_roles(role)
                elif type == 4: #drop
                    await member.remove_roles(role)
    
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        guild = self.bot.get_guild(payload.guild_id)
        if guild == None: return
        
        doc = rr_col.find_one({'guild': guild.id})
        if doc == None: return
        
        member = guild.get_member(payload.user_id)
        rr = doc['reaction_roles']
        if str(payload.message_id) in rr:
            type = rr[str(payload.message_id)]['type']
            if str(payload.emoji) in rr[str(payload.message_id)]:
                role = guild.get_role(rr[str(payload.message_id)][str(payload.emoji)])
                if type == 0: #normal
                    await member.remove_roles(role)
                elif type == 1: #unique
                    await member.remove_roles(role)
                elif type == 2: #reversed
                    await member.add_roles(role)
                elif type == 3: #verify
                    pass
                elif type == 4: #drop
                    pass
    
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.guild == None: return
        
        doc = rr_col.find_one({'guild': message.guild.id})
        if doc == None: return
        
        rr = doc['reaction_roles']
        if str(message.id) in rr:
            del rr[str(message.id)]
            rr_col.update_one(
                {'_id': doc['_id']},
                {'$set': {'reaction_roles': rr}}
            )
    
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        doc = rr_col.find_one({'guild': role.guild.id})
        if doc == None: return
        
        rr = doc['reaction_roles']
        if role.id in sum(list(list(sk.values()) for k, sk in rr.items()), []):
            message, emoji = sum(list(list([k, sk] for sk, v in sd.items() if v == role.id) for k, sd in rr.items()), [])[0]
            del rr[message][emoji]
            rr_col.update_one(
                {'_id': doc['_id']},
                {'$set': {'reaction_roles': rr}}
            )
    
    @commands.group(
        aliases = ['rr'],
        help = '''Type 0: Normal
Type 1: Unique
Type 2: Reversed
Type 3: Verify
Type 4: Drop'''
    )
    @commands.guild_only()
    async def reaction_role(self, ctx):
        doc = rr_col.find_one({'guild': ctx.guild.id})
        if doc == None:
            doc = {
                'guild': ctx.guild.id,
                'reaction_roles': {} #{message.id: {'type': 0, emoji: role.id}}
            }
            rr_col.insert_one(doc)
        if ctx.invoked_subcommand == None:
            embed = discord.Embed(
                title = 'Reaction Roles',
                description = 'None',
                color = 0xffe5ce
            )
            for msg_id, rr in doc['reaction_roles'].items():
                if len(rr) > 1:
                    embed.description = None
                    embed.add_field(
                        name = f'{msg_id} (Type {rr["type"]})',
                        value = '\n'.join(
                            f'{emoji} {ctx.guild.get_role(role).mention}' for emoji, role in rr.items() if emoji != 'type'
                        )
                    )
            await ctx.reply(embed = embed)
    
    @reaction_role.command()
    async def add(self, ctx, msg_id, emoji, role: discord.Role, channel: discord.TextChannel = None):
        if channel == None:
            channel = ctx.channel
        message = await channel.fetch_message(int(msg_id))
        await message.add_reaction(emoji)
        doc = rr_col.find_one({'guild': ctx.guild.id})
        rr = doc['reaction_roles']
        if msg_id not in rr:
            rr[msg_id] = {'type': 0} #{emoji: role.id}
        if emoji in rr[msg_id]:
            await ctx.reply('Emoji already added.')
        elif role.id in rr[msg_id].values():
            await ctx.reply('Role already added.')
        else:
            rr[msg_id][emoji] = role.id
            rr_col.update_one(
                {'_id': doc['_id']},
                {'$set': {'reaction_roles': rr}}
            )
            for reaction in message.reactions:
                if str(reaction.emoji) == emoji:
                    async for user in reaction.users():
                        if isinstance(user, discord.Member):
                            await user.add_roles(role)
            await ctx.reply(f'Reaction role added to **{msg_id}**')
    
    @reaction_role.command()
    async def edit(self, ctx, msg_id, emoji, role: discord.Role, channel: discord.TextChannel = None):
        if channel == None:
            channel = ctx.channel
        message = await channel.fetch_message(int(msg_id))
        await ctx.message.add_reaction(emoji)
        doc = rr_col.find_one({'guild': ctx.guild.id})
        rr = doc['reaction_roles']
        if msg_id not in rr:
            rr[msg_id] = {'type': 0} #{emoji: role.id}
        if emoji in rr[msg_id]:
            old_role = ctx.guild.get_role(rr[msg_id][emoji])
            rr[msg_id][emoji] = role.id
            rr_col.update_one(
                {'_id': doc['_id']},
                {'$set': {'reaction_roles': rr}}
            )
            for reaction in message.reactions:
                if str(reaction.emoji) == emoji:
                    async for user in reaction.users():
                        if isinstance(user, discord.Member):
                            await user.add_roles(role)
                            await user.remove_roles(old_role)
            await ctx.reply(f'Role changed.')
        else:
            await ctx.reply('Emoji not found.')
    
    @reaction_role.command()
    async def type(self, ctx, msg_id, type: int):
        doc = rr_col.find_one({'guild': ctx.guild.id})
        rr = doc['reaction_roles']
        if msg_id not in rr:
            rr[msg_id] = {'type': 0} #{emoji: role.id}
        if 0 <= type <= 4:
            rr[msg_id]['type'] = type
            await ctx.reply(f'**{msg_id}** type set to {type}.')
            rr_col.update_one(
                {'_id': doc['_id']},
                {'$set': {'reaction_roles': rr}}
            )
        else:
            await ctx.reply(f'Invalid type.')
    
    @reaction_role.command()
    async def remove(self, ctx, msg_id, emoji, channel: discord.TextChannel = None):
        if channel == None:
            channel = ctx.channel
        message = await channel.fetch_message(int(msg_id))
        await message.remove_reaction(emoji, ctx.me)
        doc = rr_col.find_one({'guild': ctx.guild.id})
        rr = doc['reaction_roles']
        if msg_id not in rr:
            rr[msg_id] = {'type': 0} #{emoji: role.id}
        if emoji in rr[msg_id]:
            role = ctx.guild.get_role(rr[msg_id][emoji])
            del rr[msg_id][emoji]
            rr_col.update_one(
                {'_id': doc['_id']},
                {'$set': {'reaction_roles': rr}}
            )
            for reaction in message.reactions:
                if str(reaction.emoji) == emoji:
                    async for user in reaction.users():
                        if isinstance(user, discord.Member):
                            await user.remove_roles(role)
                await message.remove_reaction(reaction.emoji, ctx.me)
            await ctx.reply('Emoji removed.')
        else:
            await ctx.reply('Emoji not found.')
    
    @reaction_role.command()
    async def purge(ctx, msg_id = None):
        doc = rr_col.find_one({'guild': ctx.guild.id})
        rr = doc['reaction_roles']
        if msg_id == None:
            rr = {}
            await ctx.reply('ALL reaction roles has been removed.')
        elif msg_id in rr:
            del rr[msg_id]
            await ctx.reply(f'Purged reaction roles for **{msg_id}**')
        else:
            return await ctx.reply('Message not found.')
        rr_col.update_one(
            {'_id': doc['_id']},
            {'$set': {'reaction_roles': rr}}
        )
    
    @reaction_role.command()
    async def move(self, ctx, old_msg, new_msg, channel: discord.TextChannel = None):
        if channel == None:
            channel = ctx.channel
        doc = rr_col.find_one({'guild': ctx.guild.id})
        rr = doc['reaction_roles']
        if old_msg in rr:
            if new_msg not in rr:
                rr[new_msg] = {'type': 0} #{emoji: role.id}
            rr[new_msg] = rr[old_msg]
            message = await channel.fetch_message(int(new_msg))
            for emoji in rr[old_msg].values():
                if emoji != 'type':
                    await message.add_reaction(emoji)
            del rr[old_msg]
            rr_col.update_one(
                {'_id': doc['_id']},
                {'$set': {'reaction_roles': rr}}
            )
            await ctx.reply(f'{len(rr[new_msg]) - 1} reaction roles from **{old_msg}** has been moved to **{new_msg}**')
        else:
            await ctx.reply('Message not found.')

async def setup(bot):
    await bot.add_cog(Moderation(bot))
