import discord
from discord import app_commands
from discord.ext import commands
from typing import Union, Literal, Optional
import pymongo
import random
import os

client = pymongo.MongoClient(
    f'mongodb+srv://Senjienji:{os.getenv("PASSWORD")}@senjienji.czypcav.mongodb.net/?retryWrites=true&w=majority',
    server_api = pymongo.server_api.ServerApi('1'),
)
db = client.senjibot
currency_col = db.currency
shop_col = db.shop

class Currency(commands.Cog):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
    
    @app_commands.command(description = "Shows your (or someone else's) balance")
    @app_commands.describe(member = 'The member to choose (must not be a bot)')
    async def balance(self, inter, member: Optional[discord.Member]):
        if member == None:
            member = inter.user
        if member.bot:
            return await inter.response.send_message('No', ephemeral = True)
        doc = currency_col.find_one({'user': member.id})
        if doc == None:
            doc = {
                'user': member.id,
                'balance': [0, 0]
            }
            currency_col.insert_one(doc)
        wallet, bank = doc['balance']
        await inter.response.send_message(embed = discord.Embed(
            title = f"{member.display_name}'s Balance",
            description = f'Wallet: ${wallet}\nBank: ${bank} / $1000',
            color = 0xffe5ce
        ).set_author(
            name = inter.user.display_name,
            url = f'https://discord.com/users/{inter.user.id}',
            icon_url = inter.user.display_avatar.url
        ))
    
    @app_commands.command(description = "Shows this server's leaderboard")
    @app_commands.guild_only()
    async def leaderboard(self, inter):
        paginator = tuple(
            f'{index}. `{member}`: ${amount}' for index, (member, amount) in enumerate(
                sorted(
                    filter(
                        lambda i: i[0] != None and i[1] > 0,
                        (
                            (
                                inter.guild.get_member(i['user']),
                                sum(i['balance'])
                            ) for i in currency_col.find()
                        )
                    ),
                    key = lambda i: i[1],
                    reverse = True
                ),
                start = 1
            )
        )
        embed = discord.Embed(
            title = 'Leaderboard',
            color = 0xffe5ce
        ).set_author(
            name = inter.user.display_name,
            url = f'https://discord.com/users/{inter.user.id}',
            icon_url = inter.user.display_avatar.url
        )
        
        class Leaderboard(discord.ui.View):
            page = 0
            embed.description = '\n'.join(paginator[page:page + 10])
            
            @discord.ui.button(label = '', emoji = '⬅️', disabled = page == 0)
            async def previous(self, view_inter, button):
                if view_inter.user == inter.user:
                    page -= 10
                    button.disabled = page == 0
                    embed.description = '\n'.join(paginator[page:page + 10])
                    await view_inter.response.edit_message(embed = embed, view = self)
                else:
                    await view_inter.response.send_message('This button is not for you.', ephemeral = True)
            
            @discord.ui.button(label = '', emoji = '➡️', disabled = page == len(paginator) // 10 * 10)
            async def next(self, view_inter, button):
                if view_inter.user == inter.user:
                    page += 10
                    button.disabled = page == len(paginator) // 10 * 10
                    embed.description = '\n'.join(paginator[page:page + 10])
                    await view_inter.response.edit_message(embed = embed, view = self)
                else:
                    await view_inter.response.send_message('This button is not for you.', ephemeral = True)
        
        await inter.response.send_message(embed = embed, view = Leaderboard())
    
    @app_commands.command(description = 'Deposit your money into the bank\nLimit is $1000 per bank account')
    @app_commands.describe(amount = 'The amount of money to deposit')
    async def deposit(self, inter, amount: Literal[int, 'all']):
        doc = currency_col.find_one({'user': inter.user.id})
        if doc == None:
            doc = {
                'user': inter.user.id,
                'balance': [0, 0]
            }
            currency_col.insert_one(doc)
        bal = doc['balance']
        wallet, bank = bal
        if amount == 'all':
            amount = wallet
        amount = min(amount, 1000 - bank)
        if amount > 0:
            if wallet >= amount:
                bal[0] -= amount
                bal[1] += amount
                currency_col.update_one(
                    {'user': inter.user.id},
                    {'$set': {'balance': bal}}
                )
                await inter.response.send_message(f'${amount} deposited.')
            else:
                await inter.response.send_message(f"You're ${amount - wallet} short.", ephemeral = True)
        else:
            await inter.response.send_message('amount must be greater than 0.', ephemeral = True)
    
    @app_commands.command(description = 'Withdraw money from the bank')
    @app_commands.describe(amount = 'The amount of money to withdraw')
    async def withdraw(self, inter, amount: Literal[int, 'all']):
        doc = currency_col.find_one({'user': inter.user.id})
        if doc == None:
            doc = {
                'user': inter.user.id,
                'balance': [0, 0]
            }
            currency_col.insert_one(doc)
        bal = doc['balance']
        bank = bal[1]
        if amount == 'all':
            amount = bank
        if amount > 0:
            if bank >= amount:
                bal[0] += amount
                bal[1] -= amount
                currency_col.update_one(
                    {'user': inter.user.id},
                    {'$set': {'balance': bal}}
                )
                await inter.response.send_message(f'${amount} withdrawn.')
            else:
                await inter.response.send_message(f"You're ${amount - bank} short.", ephemeral = True)
        else:
            await inter.response.send_message('amount must be greater than 0.', ephemeral = True)
    
    @app_commands.command(description = 'Work every 30 minutes to get money!')
    @app_commands.checks.cooldown(1, 30 * 60, key = lambda i: i.user.id)
    async def work(self, inter):
        doc = currency_col.find_one({'user': inter.user.id})
        if doc == None:
            doc = {
                'user': inter.user.id,
                'balance': [0, 0]
            }
            currency_col.insert_one(doc)
        bal = doc['balance']
        gain = random.randint(1, 10)
        bal[0] += gain
        currency_col.update_one(
            {'user': inter.user.id},
            {'$set': {'balance': bal}}
        )
        await inter.response.send_message(f'You got ${gain}.')
    
    @app_commands.command(description = 'Give money to someone (cooldown is 1 hour)')
    @app_commands.describe(
        member = 'Who you want to give your money to (must not be a bot)',
        amount = 'The amount of money to give'
    )
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 1 * 60 * 60, key = lambda i: i.user.id)
    async def give(self, ctx, member: discord.Member, amount: Literal[int, 'all']):
        doc = currency_col.find_one({'user': inter.user.id})
        if doc == None:
            doc = {
                'user': inter.user.id,
                'balance': [0, 0]
            }
            currency_col.insert_one(doc)
        author_bal = doc['balance']
        if member == inter.user or member.bot:
            return await inter.response.send_message('No', ephemeral = True)
        doc = currency_col.find_one({'user': member.id})
        if doc == None:
            doc = {
                'user': member.id,
                'balance': [0, 0]
            }
            currency_col.insert_one(doc)
        member_bal = doc['balance']
        
        wallet = author_bal[0]
        if amount == 'all':
            amount = wallet
        if amount > 0:
            if wallet >= amount:
                author_bal[0] -= amount
                member_bal[0] += amount
                currency_col.update_one(
                    {'user': inter.user.id},
                    {'$set': {'balance': author_bal}}
                )
                currency_col.update_one(
                    {'user': member.id},
                    {'$set': {'balance': member_bal}}
                )
                await inter.response.send_message(f'You gave ${amount} to `{member}`.')
            else:
                await inter.response.send_message(f"You're ${amount - wallet} short.", ephemeral = True)
                ctx.command.reset_cooldown(ctx)
        else:
            await inter.response.send_message('amount must be greater than 0.', ephemeral = True)
            ctx.command.reset_cooldown(ctx)
    
    @app_commands.command(description = 'Rob someone (cooldown is 2 hours) (50% chance of success)')
    @app_commands.describe(member = 'The member you want to rob (must not be a bot)')
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 2 * 60 * 60, key = lambda i: i.user.id)
    async def rob(self, inter, member: discord.Member):
        doc = currency_col.find_one({'user': inter.user.id})
        if doc == None:
            doc = {
                'user': inter.user.id,
                'balance': [0, 0]
            }
            currency_col.insert_one(doc)
        author_bal = doc['balance']
        if member == inter.user or member.bot:
            return await inter.response.send_message('No', ephemeral = True)
        doc = currency_col.find_one({'user': member.id})
        if doc == None:
            doc = {
                'user': member.id,
                'balance': [0, 0]
            }
            currency_col.insert_one(doc)
        member_bal = doc['balance']
        
        wallet1 = author_bal[0]
        wallet2 = member_bal[0]
        if wallet1 >= 20:
            if wallet2 >= 20:
                if random.randint(0, 100) < 50:
                    amount = random.randint(20, max(wallet2 // 3, 20))
                    author_bal[0] += amount
                    member_bal[0] -= amount
                    currency_col.update_one(
                        {'user': inter.user.id},
                        {'$set': {'balance': author_bal}}
                    )
                    currency_col.update_one(
                        {'user': member.id},
                        {'$set': {'balance': member_bal}}
                    )
                    await inter.response.send_message(f'You stole ${amount} from `{member}`.')
                else:
                    amount = random.randint(20, max(wallet1 // 3, 20))
                    author_bal[0] -= amount
                    currency_col.update_one(
                        {'user': inter.user.id},
                        {'$set': {'balance': author_bal}}
                    )
                    await inter.response.send_message(f'You got caught and lost ${amount}.')
            else:
                await inter.response.send_message('Your target has less than $20.', ephemeral = True)
        else:
            await inter.response.send_message('You need at least $20 to rob someone.', ephemeral = True)
    
    def check(self, inter: discord.Interaction):
        return inter.user.id == self.bot.owner_id
    
    @commands.command(hidden = True)
    @commands.is_owner()
    async def set(self, ctx, member: discord.Member, type: Literal['wallet', 'bank'], amount: int):
        doc = currency_col.find_one({'user': member.id})
        if doc == None:
            doc = {
                'user': member.id,
                'balance': [0, 0]
            }
            currency_col.insert_one(doc)
        bal = doc['balance']
        bal[('wallet', 'bank').index(type)] = amount
        currency_col.update_one(
            {'user': member.id},
            {'$set': {'balance': bal}}
        )
        await ctx.reply(f"`{member}`'s {type} balance has been set to ${amount}.")
    
    shop = app_commands.Group(
        name = 'shop',
        description = 'shop for this server',
        guild_only = True
    )
    
    @shop.command(description = 'Shows all of the items in the shop')
    async def items(self, inter):
        doc = shop_col.find_one({'guild': inter.guild_id})
        if doc == None:
            doc = {
                'guild': inter.guild_id,
                'items': {}
            }
            shop_col.insert_one(doc)
        items = doc['items']
        
        if items == {}:
            return await inter.response.send_message('This shop is empty, check again later.', ephemeral = True)
        
        options = [
            discord.SelectOption(
                label = name,
                description = f'${price}'
            ) for name, price in items.items()
        ]
        
        class Shop(discord.ui.View):
            @discord.ui.select(placeholder = 'Select an item', options = options)
            async def menu(self, view_inter, select):
                doc = currency_col.find_one({'user': view_inter.user.id})
                if doc == None:
                    doc = {
                        'user': view_inter.user.id,
                        'balance': [0, 0]
                    }
                    currency_col.insert_one(doc)
                bal = doc['balance']
                wallet = bal[0]
                price = items[select.values[0]]
                if wallet >= price:
                    bal[0] -= price
                    currency_col.update_one(
                        {'user': view_inter.user.id},
                        {'$set': {'balance': bal}}
                    )
                    await view_inter.response.send_message(f'{view_inter.user.mention} item "{select.values[0]}" purchased.')
                else:
                    await view_inter.response.send_message(f'You are ${price - wallet} short.', ephemeral = True)
            
        message = await inter.response.send_message('Shop', view = Shop())
    
    @shop.command(description = 'Adds an item into the shop\nRequires the `Manage Server` permission')
    @app_commands.describe(
        name = 'The name of the item',
        price = 'How much it costs (must not be below 0)'
    )
    @app_commands.checks.has_permissions(manage_guild = True)
    async def add(self, inter, name, price: int):
        doc = shop_col.find_one({'guild': inter.guild_id})
        if doc == None:
            doc = {
                'guild': inter.guild_id,
                'items': {}
            }
            shop_col.insert_one(doc)
        items = doc['items']
        if name not in items:
            if price >= 0:
                items[name] = price
                shop_col.update_one(
                    {'guild': inter.guild_id},
                    {'$set': {'items': items}}
                )
                await inter.response.send_message(f'Item "{name}" added.')
            else:
                await inter.response.send_message('price must be greater than or equal to 0.', ephemeral = True)
        else:
            await inter.response.send_message(f'Item "{name}" is already added.', ephemeral = True)
    
    @shop.command(description = "Edits the price of an item or changes it's name\nRequires the `Manage Server` permission")
    @app_commands.describe(
        name = 'The name of the item',
        change = 'The new name **OR** the modified price'
    )
    @app_commands.checks.has_permissions(manage_guild = True)
    async def edit(self, inter, name, change: Union[str, int]):
        doc = shop_col.find_one({'guild': inter.guild_id})
        if doc == None:
            doc = {
                'guild': inter.guild_id,
                'items': {}
            }
            shop_col.insert_one(doc)
        items = doc['items']
        if name in items:
            if isinstance(change, str):
                items[change] = items[name]
                del items[name]
                shop_col.update_one(
                    {'guild': inter.guild_id},
                    {'$set': {'items': items}}
                )
                await inter.response.send_message(f'Item "{name}" edited to "{change}".')
            elif isinstance(change, int):
                items[name] = change
                shop_col.update_one(
                    {'guild': inter.guild_id},
                    {'$set': {'items': items}}
                )
                await inter.response.send_message(f'Item "{name}" edited to ${change}.')
        else:
            await inter.response.send_message(f'Item "{name}" not found.', ephemeral = True)
    
    @shop.command(description = 'Removes an item from the shop')
    @app_commands.describe(name = 'The name of the item')
    @app_commands.checks.has_permissions(manage_guild = True)
    async def remove(self, inter, name):
        doc = shop_col.find_one({'guild': inter.guild_id})
        if doc == None:
            doc = {
                'guild': inter.guild_id,
                'items': {}
            } 
            shop_col.insert_one(doc)
        items = doc['items']
        if name in items:
            del items[name]
            shop_col.update_one(
                {'guild': inter.guild_id},
                {'$set': {'items': items}}
            )
            await inter.response.send_message(f'Item "{name}" removed.')
        else:
            await inter.response.send_message(f'Item "{name}" not found.', ephemeral = True)

async def setup(bot):
    await bot.add_cog(Currency(bot))
