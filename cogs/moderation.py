import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, Union
import pymongo
import os

client = pymongo.MongoClient(
    f'mongodb+srv://Senjienji:{os.getenv("PASSWORD")}@senjienji.czypcav.mongodb.net/?retryWrites=true&w=majority',
    server_api = pymongo.server_api.ServerApi('1'),
)
db = client.senjibot
rr_col = db.reaction_roles_test

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
    
    @app_commands.command(description = 'Purge messages')
    @app_commands.describe(limit = 'The amount of messages to delete')
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(manage_messages = True)
    @app_commands.checks.bot_has_permissions(manage_messages = True, read_message_history = True)
    async def purge(self, inter, limit: int):
        purge = await inter.channel.purge(limit = limit)
        await inter.response.send_message(f'Purged {len(purge)} message{"s" if len(purge) > 1 else None}.', ephemeral = True)
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        guild = self.bot.get_guild(payload.guild_id)
        if guild == None: return
        
        doc = rr_col.find_one({'guild': guild.id})
        if doc == None: return
        
        member = payload.member
        rr = doc['reaction_roles']
        if str(payload.message_id) in rr:
            type = rr[str(payload.message_id)]['type']
            if payload.emoji.name in rr[str(payload.message_id)]:
                role = guild.get_role(rr[str(payload.message_id)][payload.emoji.name])
                if type == 0: #normal
                    await member.add_roles(role)
                elif type == 1: #unique
                    await member.add_roles(role)
                    message = await guild.get_channel(payload.channel_id).fetch_message(payload.message_id)
                    for reaction in message.reactions:
                        if reaction.emoji != payload.emoji and reaction.emoji.name in rr[str(payload.message_id)]:
                            await message.remove_reaction(reaction.emoji, member)
                elif type == 2: #reversed
                    await member.remove_roles(role)
                elif type == 3: #verify
                    await member.add_roles(role)
                elif type == 4: #drop
                    await member.remove_roles(role)
                elif type == 5: #binding
                    if not any(j in [i.id for i in member.roles] for j in rr[str(payload.message_id)].values()):
                        await member.add_roles(role)
    
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
            if payload.emoji.name in rr[str(payload.message_id)]:
                role = guild.get_role(rr[str(payload.message_id)][payload.emoji.name])
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
                elif type == 5: #binding
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
    
    reaction_role = app_commands.Group(
        name = 'reaction_role',
        description = '''Type 0: Normal
Type 1: Unique
Type 2: Reversed
Type 3: Verify
Type 4: Drop
Type 5: Binding''',
        guild_only = True
    )
    
    @reaction_role.command(
        name = 'list',
        description = 'Shows the list of reaction roles'
    )
    async def rr_list(self, inter):
        doc = rr_col.find_one({'guild': inter.guild_id})
        if doc == None:
            doc = {
                'guild': inter.guild_id,
                'reaction_roles': {} #{message.id: {'type': 0, emoji.name: role.id}}
            }
            rr_col.insert_one(doc)
        embed = discord.Embed(
            title = 'Reaction Roles',
            description = 'None',
            color = 0xffe5ce
        ).set_author(
            name = inter.user,
            url = f'https://discord.com/users/{inter.user.id}',
            icon_url = inter.user.display_avatar.url
        )
        for msg_id, rr in doc['reaction_roles'].items():
            if len(rr) > 1:
                embed.description = None
                embed.add_field(
                    name = f'{msg_id} (Type {rr["type"]})',
                    value = '\n'.join(f'{emoji} {inter.guild.get_role(role).mention}' for emoji, role in rr.items() if emoji != 'type')
                )
        await inter.response.send_message(embed = embed)
    
    @reaction_role.command(description = 'Adds a reaction role\nRequires the `Manage Server` permission')
    @app_commands.describe(
        msg_id = "The message's ID to apply the reaction role",
        emoji = 'An unicode or a custom emoji',
        role = 'The role to set the reaction role',
        channel = 'The channel to fetch the message from'
    )
    @app_commands.checks.has_permissions(manage_guild = True)
    async def add(self, inter, msg_id, emoji: discord.PartialEmoji, role: discord.Role, channel: Optional[discord.TextChannel]):
        if channel == None:
            channel = inter.channel
        message = await channel.fetch_message(int(msg_id))
        await message.add_reaction(emoji)
        doc = rr_col.find_one({'guild': inter.guild_id})
        if doc == None:
            doc = {
                'guild': inter.guild_id,
                'reaction_roles': {} #{message.id: {'type': 0, emoji.name: role.id}}
            }
            rr_col.insert_one(doc)
        rr = doc['reaction_roles']
        if msg_id not in rr:
            rr[msg_id] = {'type': 0} #{emoji.name: role.id}
        if emoji.name in rr[msg_id]:
            raise commands.BadArgument('Emoji "{emoji}" already added.')
        if role.id in rr[msg_id].values():
            raise commands.BadArgument('Role "{role}" already added.')
        
        rr[msg_id][emoji.name] = role.id
        rr_col.update_one(
            {'guild': inter.guild_id},
            {'$set': {'reaction_roles': rr}}
        )
        reaction = discord.utils.get(message.reactions, emoji = emoji)
        if reaction != None:
            async for user in reaction.users():
                if isinstance(user, discord.Member):
                    await user.add_roles(role)
        await inter.response.send_message(f'Reaction role added to **{msg_id}**')
    
    @reaction_role.command(description = 'Edits a reaction role\nRequires the `Manage Server` permission')
    @app_commands.describe(
        msg_id = "The message's ID to edit the reaction role",
        emoji = "The reaction role's emoji",
        change = 'An emoji or a role',
        channel = 'The channel to fetch the message from'
    )
    @app_commands.checks.has_permissions(manage_guild = True)
    async def edit(self, inter, msg_id, emoji: discord.PartialEmoji, change: Union[discord.Role, discord.PartialEmoji], channel: Optional[discord.TextChannel]):
        if channel == None:
            channel = inter.channel
        message = await channel.fetch_message(int(msg_id))
        doc = rr_col.find_one({'guild': inter.guild_id})
        if doc == None:
            doc = {
                'guild': inter.guild_id,
                'reaction_roles': {} #{message.id: {'type': 0, emoji.name: role.id}}
            }
            rr_col.insert_one(doc)
        rr = doc['reaction_roles']
        if msg_id not in rr:
            rr[msg_id] = {'type': 0} #{emoji.name: role.id}
        if emoji.name not in rr[msg_id]:
            raise commands.BadArgument('Emoji "{emoji}" not found.')
        
        if isinstance(change, discord.Role):
            role = inter.guild.get_role(rr[msg_id][emoji.name])
            rr[msg_id][emoji.name] = change.id
            reaction = discord.utils.get(message.reactions, emoji = emoji)
            if reaction != None:
                async for user in reaction.users():
                    if isinstance(user, discord.Member):
                        await user.add_roles(change)
                        await user.remove_roles(role)
            await inter.response.send_message('Role changed.')
        elif isinstance(change, discord.PartialEmoji):
            rr[msg_id][change.name] = rr[msg_id][emoji.name]
            del rr[msg_id][emoji.name]
            for reaction in message.reactions:
                if reaction.emoji == emoji:
                    async for user in reaction.users():
                        if isinstance(user, discord.Member):
                            await user.remove_roles(role)
                elif reaction.emoji == change:
                    async for user in reaction.users():
                        if isinstance(user, discord.Member):
                            await user.add_roles(role)
            await inter.response.send_message(f'Emoji changed to {change}.')
        rr_col.update_one(
            {'guild': inter.guild_id},
            {'set': {'reaction_roles': rr}}
        )
    
    @reaction_role.command(
        name = 'type',
        description = 'Changes the type of a reaction role message\nRequires the `Manage Server` permission'
    )
    @app_commands.describe(
        msg_id = "The message's ID to edit the reaction role",
        type = '''Type 0: Normal
Type 1: Unique
Type 2: Reversed
Type 3: Verify
Type 4: Drop
Type 5: Binding'''
    )
    @app_commands.checks.has_permissions(manage_guild = True)
    async def rr_type(self, inter, msg_id, type: app_commands.Range[int, 0, 5]):
        doc = rr_col.find_one({'guild': inter.guild_id})
        if doc == None:
            doc = {
                'guild': inter.guild_id,
                'reaction_roles': {} #{message.id: {'type': 0, emoji.name: role.id}}
            }
            rr_col.insert_one(doc)
        rr = doc['reaction_roles']
        if msg_id not in rr:
            raise commands.MessageNotFound(msg_id)
        
        rr[msg_id]['type'] = type
        rr_col.update_one(
            {'guild': inter.guild_id},
            {'$set': {'reaction_roles': rr}}
        )
        await inter.response.send_message(f"**{msg_id}**'s type set to {type}.")
    
    @reaction_role.command(description = 'Removes a reaction role from a message\nRequires the `Manage Server` permission')
    @app_commands.describe(
        msg_id = "The message's ID to remove the reaction role",
        emoji = "The reaction role's emoji",
        channel = 'The channel to fetch the message from'
    )
    @app_commands.checks.has_permissions(manage_guild = True)
    async def remove(self, inter, msg_id, emoji: discord.PartialEmoji, channel: Optional[discord.TextChannel]):
        if channel == None:
            channel = inter.channel
        message = await channel.fetch_message(int(msg_id))
        doc = rr_col.find_one({'guild': inter.guild_id})
        if doc == None:
            doc = {
                'guild': inter.guild_id,
                'reaction_roles': {} #{message.id: {'type': 0, emoji.name: role.id}}
            }
            rr_col.insert_one(doc)
        rr = doc['reaction_roles']
        if msg_id not in rr:
            rr[msg_id] = {'type': 0} #{emoji.name: role.id}
        if emoji.name not in rr[msg_id]:
            raise commands.BadArgument(f'Emoji "{emoji}" not found.')
        
        role = inter.guild.get_role(rr[msg_id][emoji.name])
        del rr[msg_id][emoji.name]
        rr_col.update_one(
            {'guild': inter.guild_id},
            {'$set': {'reaction_roles': rr}}
        )
        reaction = discord.utils.get(message.reactions, emoji = emoji)
        if reaction != None:
            async for user in reaction.users():
                if isinstance(user, discord.Member):
                    await user.remove_roles(role)
        await message.remove_reaction(emoji, inter.guild.me)
        await inter.response.send_message('Emoji removed.')
    
    @reaction_role.command(
        name = 'purge',
        description = "Removes all or a message's reaction roles, this cannot be undone\nRequires the `Manage Server` permission"
    )
    @app_commands.describe(msg_id = "The message's ID to purge")
    @app_commands.checks.has_permissions(manage_guild = True)
    async def rr_purge(self, inter, msg_id: Optional[str]):
        doc = rr_col.find_one({'guild': inter.guild_id})
        if doc == None:
            doc = {
                'guild': inter.guild_id,
                'reaction_roles': {} #{message.id: {'type': 0, emoji.name: role.id}}
            }
            rr_col.insert_one(doc)
        rr = doc['reaction_roles']
        if msg_id == None:
            rr_col.update_one(
                {'guild': inter.guild_id},
                {'$set': {'reaction_roles': {}}}
            )
            await inter.response.send_message('ALL reaction roles has been removed.')
        elif msg_id in rr:
            del rr[msg_id]
            rr_col.update_one(
                {'guild': inter.guild_id},
                {'$set': {'reaction_roles': rr}}
            )
            await inter.response.send_message(f'Purged reaction roles for **{msg_id}**')
        else:
            raise commands.MessageNotFound(msg_id)
    
    @reaction_role.command(description = 'Moves all reaction roles from a message to another\nRequires the `Manage Server` permission')
    @app_commands.describe(
        old_msg = "The message's ID to move the reaction roles from",
        new_msg = "The message's ID to move the reaction roles to",
        channel = "The channel to fetch the new message from'
    )
    @app_commands.checks.has_permissions(manage_guild = True)
    async def move(self, inter, old_msg, new_msg, channel: Optional[discord.TextChannel]):
        if channel == None:
            channel = inter.channel
        message = await channel.fetch_message(int(new_msg))
        doc = rr_col.find_one({'guild': inter.guild_id})
        rr = doc['reaction_roles']
        if old_msg not in rr:
            raise commands.MessageNotFound(old_msg)
        
        rr[new_msg] = rr[old_msg]
        del rr[old_msg]
        rr_col.update_one(
            {'guild': inter.guild_id},
            {'$set': {'reaction_roles': rr}}
        )
        for emoji in rr[new_msg].values():
            if emoji != 'type':
                await message.add_reaction(emoji)
        await inter.response.send_messsage(f'{len(rr[new_msg]) - 1} reaction roles from **{old_msg}** has been moved to **{new_msg}**')

async def setup(bot):
    await bot.add_cog(Moderation(bot))
