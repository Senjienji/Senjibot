import discord
from discord.ext import commands
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
    @commands.command(aliases = ['bal'])
    async def balance(self, ctx, *, member: discord.Member = None):
        if member == None:
            member = ctx.author
        if member.bot:
            return await ctx.reply('No')
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
        ).set_footer(
            text = ctx.author.display_name,
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
        global page
        page = 0
        embed = discord.Embed(
            title = 'Leaderboard',
            description = '\n'.join(paginator[page:page + 10]),
            color = 0xffe5ce
        ).set_footer(
            text = ctx.author.display_name,
            icon_url = ctx.author.display_avatar.url
        )
        
        class Leaderboard(discord.ui.View):
            @discord.ui.button(label = '', emoji = '⬅️', disabled = page == 0)
            async def previous(self, inter, button):
                if inter.user == ctx.author:
                    global page
                    page -= 10
                    button.disabled = page == 0
                    embed.description = "\n".join(paginator[page:page + 10])
                    await inter.response.edit_message(embed = embed, view = self)
                else:
                    await inter.response.send_message('This button is not for you.', ephemeral = True)
            
            @discord.ui.button(label = '', emoji = '➡️', disabled = page == len(paginator) // 10 * 10)
            async def next(self, inter, button):
                if inter.user == ctx.author:
                    global page
                    page += 10
                    button.disabled = page == len(paginator) // 10 * 10
                    embed.description = "\n".join(paginator[page:page + 10])
                    await inter.response.edit_message(embed = embed, view = self)
                else:
                    await inter.response.send_message('This button is not for you.', ephemeral = True)
        
        await ctx.reply(embed = embed, view = Leaderboard())
    
    @commands.command(aliases = ['dep'])
    async def deposit(self, ctx, amount):
        doc = currency_col.find_one({'user': ctx.author.id})
        if doc == None:
            doc = {
                'user': ctx.author.id,
                'balance': [0, 0]
            }
            currency_col.insert_one(doc)
        bal = doc['balance']
        wallet, bank = bal
        if amount.lower() == 'all':
            amount = wallet
        else:
            amount = int(amount)
        amount = min(amount, 1000 - bank)
        if amount > 0:
            if wallet >= amount:
                bal[0] -= amount
                bal[1] += amount
                currency_col.update_one(
                    {'user': ctx.author.id},
                    {'$set': {'balance': bal}}
                )
                await ctx.reply(f'${amount} deposited.')
            else:
                await ctx.reply(f"You're ${amount - wallet} short.")
        else:
            await ctx.reply('amount must be greater than 0.')
    
    @commands.command(aliases = ['with'])
    async def withdraw(self, ctx, amount):
        doc = currency_col.find_one({'user': ctx.author.id})
        if doc == None:
            doc = {
                'user': ctx.author.id,
                'balance': [0, 0]
            }
            currency_col.insert_one(doc)
        bal = doc['balance']
        bank = bal[1]
        if amount.lower() == 'all':
            amount = bank
        else:
            amount = int(amount)
        if amount > 0:
            if bank >= amount:
                bal[0] += amount
                bal[1] -= amount
                currency_col.update_one(
                    {'user': ctx.author.id},
                    {'$set': {'balance': bal}}
                )
                await ctx.reply(f'${amount} withdrawn.')
            else:
                await ctx.reply(f"You're ${amount - bank} short.")
        else:
            await ctx.reply('amount must be greater than 0.')
    
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
        await ctx.reply(f'You got ${gain}.')
    
    @commands.command(cooldown_after_parsing = True)
    @commands.guild_only()
    @commands.cooldown(rate = 1, per = 1 * 60 * 60, type = commands.BucketType.user)
    async def give(self, ctx, member: discord.Member, amount: int):
        doc = currency_col.find_one({'user': ctx.author.id})
        if doc == None:
            doc = {
                'user': ctx.author.id,
                'balance': [0, 0]
            }
            currency_col.insert_one(doc)
        author_bal = doc['balance']
        if member == ctx.author or member.bot:
            await ctx.reply('No')
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
        if amount > 0:
            if wallet >= amount:
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
            else:
                await ctx.reply(f"You're ${amount - wallet} short.")
                ctx.command.reset_cooldown(ctx)
        else:
            await ctx.reply('amount must be greater than 0.')
            ctx.command.reset_cooldown(ctx)
    
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
        if member == ctx.author or member.bot:
            await ctx.reply('No')
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
        if wallet1 >= 20:
            if wallet2 >= 20:
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
            else:
                await ctx.reply('Your target has less than $20.')
                ctx.command.reset_cooldown(ctx)
        else:
            await ctx.reply('You need at least $20 to rob someone.')
            ctx.command.reset_cooldown(ctx)
    
    @commands.command(hidden = True)
    @commands.is_owner()
    async def set(self, ctx, member: discord.Member, type, amount: int):
        doc = currency_col.find_one({'user': member.id})
        if doc == None:
            doc = {
                'user': member.id,
                'balance': [0, 0]
            }
            currency_col.insert_one(doc)
        type = type.lower()
        bal = doc['balance']
        if type in ('wallet', 'bank'):
            bal[('wallet', 'bank').index(type)] = amount
            currency_col.update_one(
                {'user': member.id},
                {'$set': {'balance': bal}}
            )
            await ctx.reply(f"`{member}`'s {type} balance has been set to ${amount}.")
        else:
            await ctx.reply('invalid type')
    
    @commands.group()
    @commands.guild_only()
    async def shop(self, ctx):
        doc = shop_col.find_one({'guild': ctx.guild.id})
        if doc == None:
            doc = {
                'guild': ctx.guild.id,
                'items': {}
            }
            shop_col.insert_one(doc)
        items = doc['items']
        if ctx.invoked_subcommand == None:
            if items == {}:
                await ctx.reply('This shop is empty, check again later.')
            else:
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
                        if wallet >= price:
                            bal[0] -= price
                            currency_col.update_one(
                                {'user': inter.user.id},
                                {'$set': {'balance': bal}}
                            )
                            await inter.response.send_message(f'{inter.user.mention} item "{select.values[0]}" purchased.')
                        else:
                            await inter.response.send_message(f'You are ${price - wallet} short.', ephemeral = True)

                message = await ctx.reply('Shop', view = Shop())
    
    @shop.command()
    @commands.has_guild_permissions(manage_guild = True)
    async def add(self, ctx, name, price: int):
        doc = shop_col.find_one({'guild': ctx.guild.id})
        items = doc['items']
        if name not in items:
            if price >= 0:
                items[name] = price
                shop_col.update_one(
                    {'_id': doc['_id']},
                    {'$set': {'items': items}}
                )
                await ctx.reply(f'Item "{name}" added.')
            else:
                await ctx.reply('price must be greater than or equal to 0.')
        else:
            await ctx.reply(f'Item "{name}" is already added.')
    
    @shop.command()
    @commands.has_guild_permissions(manage_guild = True)
    async def edit(self, ctx, name, other):
        doc = shop_col.find_one({'guild': ctx.guild.id})
        items = doc['items']
        if name in items:
            if other.isnumeric():
                items[name] = int(other)
                shop_col.update_one(
                    {'_id': doc['_id']},
                    {'$set': {'items': items}}
                )
                await ctx.reply(f'Item "{name}" edited.')
            else:
                items[other] = items[name]
                del items[name]
                shop_col.update_one(
                    {'_id': doc['_id']},
                    {'$set': {'items': items}}
                )
                await ctx.reply(f'Item "{name}" edited to "{other}".')
        else:
            await ctx.reply(f'Item "{name}" not found.')
    
    @shop.command()
    @commands.has_guild_permissions(manage_guild = True)
    async def remove(self, ctx, *, name):
        doc = shop_col.find_one({'guild': ctx.guild.id})
        items = doc['items']
        if name in items:
            del items[name]
            shop_col.update_one(
                {'_id': doc['_id']},
                {'$set': {'items': items}}
            )
            await ctx.reply(f'Item "{name}" removed.')
        else:
            await ctx.reply(f'Item "{name}" not found.')

async def setup(bot):
    await bot.add_cog(Currency())
