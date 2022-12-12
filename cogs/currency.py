import discord
from discord.ext import commands
from typing import Optional, Union, Literal
import pymongo
import random
import os

client = pymongo.MongoClient(
    f'mongodb+srv://Senjienji:{os.environ["PASSWORD"]}@senjienji.czypcav.mongodb.net/?retryWrites=true&w=majority',
    server_api = pymongo.server_api.ServerApi('1'),
)
db = client.senjibot
currency_col = db.currency
shop_col = db.shop

class Currency(commands.Cog):
    @commands.command(aliases = ['bal'])
    async def balance(self, ctx, *, member: Optional[discord.Member]):
        if member == None:
            member = ctx.author
        if member.bot:
            return await ctx.reply('`member` must not be a bot.')
        
        doc = currency_col.find_one({'user': member.id})
        if doc == None:
            doc = {
                'user': member.id,
                'balance': [0, 0]
            }
            currency_col.insert_one(doc)
        wallet, bank = doc['balance']
        await ctx.reply(embed = discord.Embed(
            title = f"{member.display_name}'s Balance",
            description = f'Wallet: ${wallet}\nBank: ${bank} / $1000',
            color = 0xffe5ce
        ).set_author(
            name = ctx.author,
            url = f'https://discord.com/users/{ctx.author.id}',
            icon_url = ctx.author.display_avatar.url
        ))
    
    @commands.command(aliases = ['lb'])
    async def leaderboard(self, ctx):
        paginator = tuple(
            f'{index}. `{member}`: ${amount}' for index, (member, amount) in enumerate(
                sorted(
                    filter(
                        lambda i: i[0] != None and i[1] > 0,
                        (
                            (
                                ctx.guild.get_member(i['user']),
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
            name = ctx.author,
            url = f'https://discord.com/users/{ctx.author.id}',
            icon_url = ctx.author.display_avatar.url
        )
        
        class Leaderboard(discord.ui.View):
            page = 0
            embed.description = '\n'.join(paginator[page:page + 10])
            
            @discord.ui.button(label = '', emoji = '⬅️', disabled = page == 0)
            async def previous(self, inter, button):
                if inter.user != ctx.author:
                    return await inter.response.send_message('This button is not for you.', ephemeral = True)
                
                page -= 10
                button.disabled = page == 0
                embed.description = '\n'.join(paginator[page:page + 10])
                await inter.response.edit_message(embed = embed, view = self)
            
            @discord.ui.button(label = '', emoji = '➡️', disabled = page == len(paginator) // 10 * 10)
            async def next(self, inter, button):
                if inter.user != ctx.author:
                    return await inter.response.send_message('This button is not for you.', ephemeral = True)
                
                page += 10
                button.disabled = page == len(paginator) // 10 * 10
                embed.description = '\n'.join(paginator[page:page + 10])
                await inter.response.edit_message(embed = embed, view = self)
        
        await ctx.reply(embed = embed, view = Leaderboard())
    
    @commands.command(aliases = ['dep'])
    async def deposit(self, ctx, amount: Union[int, Literal['all']]):
        doc = currency_col.find_one({'user': ctx.author.id})
        if doc == None:
            doc = {
                'user': ctx.author.id,
                'balance': [0, 0]
            }
            currency_col.insert_one(doc)
        bal = doc['balance']
        wallet, bank = bal
        if amount == 'all':
            amount = wallet
        amount = min(amount, 1000 - bank)
        if amount <= 0:
            return await ctx.reply('`amount` must be greater than 0.')
        if wallet < amount:
            return await ctx.reply(f"You're ${amount - wallet} short.")
        
        bal[0] -= amount
        bal[1] += amount
        currency_col.update_one(
            {'user': ctx.author.id},
            {'$set': {'balance': bal}}
        )
        await ctx.reply(f'${amount} deposited.')
    
    @commands.command(aliases = ['with'])
    async def withdraw(self, ctx, amount: Union[int, Literal['all']]):
        doc = currency_col.find_one({'user': ctx.author.id})
        if doc == None:
            doc = {
                'user': ctx.author.id,
                'balance': [0, 0]
            }
            currency_col.insert_one(doc)
        bal = doc['balance']
        bank = bal[1]
        if amount == 'all':
            amount = bank
        if amount <= 0:
            return await ctx.reply('`amount` must be greater than 0.')
        if bank < amount:
            return await ctx.reply(f"You're ${amount - bank} short.")
        
        bal[0] += amount
        bal[1] -= amount
        currency_col.update_one(
            {'user': ctx.author.id},
            {'$set': {'balance': bal}}
        )
        await ctx.reply(f'${amount} withdrawn.')
    
    @commands.command(cooldown_after_parsing = True)
    @commands.cooldown(rate = 1, per = 30 * 60, type = commands.BucketType.user)
    async def work(self, ctx):
        doc = currency_col.find_one({'user': ctx.author.id})
        if doc == None:
            doc = {
                'user': ctx.author.id,
                'balance': [0, 0]
            }
            currency_col.insert_one(doc)
        bal = doc['balance']
        gain = random.randint(1, 10)
        bal[0] += gain
        currency_col.update_one(
            {'user': ctx.author.id},
            {'$set': {'balance': bal}}
        )
        await ctx.reply(f'You got ${gain}!')
    
    @commands.command(cooldown_after_parsing = True)
    @commands.cooldown(rate = 1, per = 24 * 60 * 60, type = commands.BucketType.user)
    async def daily(self, ctx):
        doc = currency_col.find_one({'user': ctx.author.id})
        if doc == None:
            doc = {
                'user': ctx.author.id,
                'balance': [0, 0]
            }
            currency_col.insert_one(doc)
        bal = doc['balance']
        bal[0] += 30
        currency_col.update_one(
            {'user': ctx.author.id},
            {'$set': {'balance': bal}}
        )
        await ctx.reply('You got $30!')
    
    @commands.command(cooldown_after_parsing = True)
    @commands.guild_only()
    @commands.cooldown(rate = 1, per = 1 * 60 * 60, type = commands.BucketType.user)
    async def give(self, ctx, member: discord.Member, amount: Union[int, Literal['all']]):
        doc = currency_col.find_one({'user': ctx.author.id})
        if doc == None:
            doc = {
                'user': ctx.author.id,
                'balance': [0, 0]
            }
            currency_col.insert_one(doc)
        author_bal = doc['balance']
        if member == ctx.author:
            await ctx.reply("You shouldn't give yourself money.")
            return ctx.command.reset_cooldown(ctx)
        if member.bot:
            await ctx.reply('`member` must not be a bot.')
            return ctx.command.reset_cooldown(ctx)
        
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
        if amount <= 0:
            await ctx.reply('`amount` must be greater than 0.')
            return ctx.command.reset_cooldown(ctx)
        if wallet < amount:
            await ctx.reply(f"You're ${amount - wallet} short.")
            return ctx.command.reset_cooldown(ctx)
        
        author_bal[0] -= amount
        member_bal[0] += amount
        currency_col.update_one(
            {'user': ctx.author.id},
            {'$set': {'balance': author_bal}}
        )
        currency_col.update_one(
            {'user': member.id},
            {'$set': {'balance': member_bal}}
        )
        await ctx.reply(f'You gave ${amount} to `{member}`.')
    
    @commands.command(cooldown_after_parsing = True)
    @commands.guild_only()
    @commands.cooldown(rate = 1, per = 2 * 60 * 60, type = commands.BucketType.user)
    async def rob(self, ctx, *, member: discord.Member):
        doc = currency_col.find_one({'user': ctx.author.id})
        if doc == None:
            doc = {
                'user': ctx.author.id,
                'balance': [0, 0]
            }
            currency_col.insert_one(doc)
        author_bal = doc['balance']
        if member == ctx.author:
            await ctx.reply("You shouldn't rob yourself.")
            return ctx.command.reset_cooldown(ctx)
        if member.bot:
            await ctx.reply('`member` must not be a bot.')
            return ctx.command.reset_cooldown(ctx)
        
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
        if wallet1 < 20:
            await ctx.reply('You need at least $20 to rob someone.')
            return ctx.command.reset_cooldown(ctx)
        if wallet2 < 20:
            await ctx.reply('Your target has less than $20.')
            return ctx.command.reset_cooldown(ctx)
        
        if random.randint(0, 100) < 50:
            amount = random.randint(20, max(wallet2 // 3, 20))
            author_bal[0] += amount
            member_bal[0] -= amount
            currency_col.update_one(
                {'user': ctx.author.id},
                {'$set': {'balance': author_bal}}
            )
            currency_col.update_one(
                {'user': member.id},
                {'$set': {'balance': member_bal}}
            )
            await ctx.reply(f'You stole ${amount} from `{member}`.')
        else:
            amount = random.randint(20, max(wallet1 // 3, 20))
            author_bal[0] -= amount
            currency_col.update_one(
                {'user': ctx.author.id},
                {'$set': {'balance': author_bal}}
            )
            await ctx.reply(f'You got caught and lost ${amount}.')
    
    @commands.command(hidden = True)
    @commands.is_owner()
    @commands.guild_only()
    async def set(self, ctx, member: discord.Member, type: Literal['wallet', 'bank'], amount: int):
        doc = currency_col.find_one({'user': member.id})
        if doc == None:
            doc = {
                'user': member.id,
                'balance': [0, 0]
            }
            currency_col.insert_one(doc)
        bal = doc['balance']
        bal[['wallet', 'bank'].index(type)] = amount
        currency_col.update_one(
            {'user': member.id},
            {'$set': {'balance': bal}}
        )
        await ctx.reply(f"`{member}`'s {type} balance has been set to ${amount}.")
    
    @commands.group()
    @commands.guild_only()
    async def shop(self, ctx):
        doc = shop_col.find_one({'guild': ctx.guild.id})
        if doc == None:
            doc = {
                'guild': ctx.guild.id,
                'items': {} #{name: price}
            }
            shop_col.insert_one(doc)
        if ctx.invoked_subcommand: return
        
        items = doc['items']
        if items == {}:
            return await ctx.reply('This shop is empty, check again later.')
        
        options = [
            discord.SelectOption(
                label = name,
                description = f'${price}'
            ) for name, price in items.items()
        ]
        
        class Shop(discord.ui.View):
            @discord.ui.select(placeholder = 'Select an item', options = options)
            async def menu(self, inter, select):
                doc = currency_col.find_one({'user': inter.user.id})
                if doc == None:
                    doc = {
                        'user': inter.user.id,
                        'balance': [0, 0]
                    }
                    currency_col.insert_one(doc)
                bal = doc['balance']
                wallet = bal[0]
                price = items[select.values[0]]
                if wallet < price:
                    return await inter.response.send_message(f"You're ${price - wallet} short.", ephemeral = True)
                
                bal[0] -= price
                currency_col.update_one(
                    {'user': inter.user.id},
                    {'$set': {'balance': bal}}
                )
                await inter.response.send_message(f'{inter.user.mention} item "{select.values[0]}" purchased.')
        
        message = await ctx.reply('Shop', view = Shop())
    
    @shop.command()
    @commands.has_guild_permissions(manage_guild = True)
    async def add(self, ctx, name, price: int):
        doc = shop_col.find_one({'guild': ctx.guild.id})
        items = doc['items']
        if name in items:
            return await ctx.reply(f'Item "{name}" already added.')
        if price < 0:
            return await ctx.reply('`price` must not be lower than 0.')
        
        items[name] = price
        shop_col.update_one(
            {'_id': doc['_id']},
            {'$set': {'items': items}}
        )
        await ctx.reply(f'Item "{name}" added.')
    
    @shop.command()
    @commands.has_guild_permissions(manage_guild = True)
    async def edit(self, ctx, name, change: Union[str, int]):
        doc = shop_col.find_one({'guild': ctx.guild.id})
        items = doc['items']
        if name not in items:
            return await ctx.reply(f'Item "{name}" not found.')
        
        if isinstance(change, str):
            items[change] = items[name]
            del items[name]
            await ctx.reply(f'Item "{name}" edited to "{change}".')
        elif isinstance(change, int):
            items[name] = change
            await ctx.reply(f'Item "{name}" edited to ${change}.')
        shop_col.update_one(
            {'_id': doc['_id']},
            {'$set': {'items': items}}
        )
    
    @shop.command()
    @commands.has_guild_permissions(manage_guild = True)
    async def remove(self, ctx, *, name):
        doc = shop_col.find_one({'guild': ctx.guild.id})
        items = doc['items']
        if name not in items:
            return await ctx.reply(f'Item "{name}" not found.')
        
        del items[name]
        shop_col.update_one(
            {'_id': doc['_id']},
            {'$set': {'items': items}}
        )
        await ctx.reply(f'Item "{name}" removed.')

async def setup(bot):
    await bot.add_cog(Currency())
