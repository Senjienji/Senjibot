import discord
from discord.ext import commands
import pymongo
import random
import os

client = pymongo.MongoClient(
    f'mongodb+srv://Senjienji:{os.getenv("PASSWORD")}@senjienji.czypcav.mongodb.net/?retryWrites=true&w=majority',
    server_api = pymongo.server_api.ServerApi('1'),
)
db = client.db
currency_cl = db.currency
shop_cl = db.shop

class Currency(commands.Cog):
    @commands.command(aliases = ['bal'])
    async def balance(self, ctx, *, member: discord.Member = None):
        if member == None:
            member = ctx.author
        if member.bot:
            return await ctx.reply('No')
        if currency_cl.find_one({'user': member.id}) == None:
            currency_cl.insert_one({
                'user': member.id,
                'wallet': 0,
                'bank': 0
            })
        i = currency_cl.find_one({'user': member.id})
        wallet = i['wallet']
        bank = i['bank']
        await ctx.reply(embed = discord.Embed(
            title = f"{member.display_name}'s Balance",
            description = f'Wallet: ${wallet}\nBank: ${bank}',
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
                                i['wallet'] + i['bank']
                            ) for i in currency_cl.find()
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
        if currency_cl.find_one({'user': ctx.author.id}) == None:
            currency_cl.insert_one({
                'user': ctx.author.id,
                'wallet': 0,
                'bank': 0
            })
        wallet = currency_cl.find_one({'user': ctx.author.id})['wallet']
        if amount.lower() == 'all':
            amount = wallet
        else:
            amount = int(amount)
        if amount > 0:
            if wallet >= amount:
                currency_cl.find_one_and_update(
                    {'user': ctx.author.id},
                    {'$inc': {
                        'wallet': -amount,
                        'bank': amount
                    }}
                )
                await ctx.reply(f'${amount} deposited.')
            else:
                await ctx.reply(f"You're ${amount - wallet} short.")
        else:
            await ctx.reply('amount must be greater than 0.')
    
    @commands.command(aliases = ['with'])
    async def withdraw(self, ctx, amount):
        if currency_cl.find_one({'user': ctx.author.id}) == None:
            currency_cl.insert_one({
                'user': ctx.author.id,
                'wallet': 0,
                'bank': 0
            })
        bank = currency_cl.find_one({'user': ctx.author.id})['bank']
        if amount.lower() == 'all':
            amount = bank
        else:
            amount = int(amount)
        if amount > 0:
            if bank >= amount:
                currency_cl.find_one_and_update(
                    {'user': ctx.author.id},
                    {'$inc': {
                        'wallet': amount,
                        'bank': -amount
                    }}
                )
                await ctx.reply(f'${amount} withdrawn.')
            else:
                await ctx.reply(f"You're ${amount - bank} short.")
        else:
            await ctx.reply('amount must be greater than 0.')
    
    @commands.command(cooldown_after_parsing = True)
    @commands.cooldown(rate = 1, per = 30 * 60, type = commands.BucketType.user)
    async def work(self, ctx):
        if currency_cl.find_one({'user': ctx.author.id}) == None:
            currency_cl.insert_one({
                'user': ctx.author.id,
                'wallet': 0,
                'bank': 0
            })
        gain = random.randint(1, 10)
        currency_cl.find_one_and_update(
            {'user': ctx.author.id},
            {'$inc': {'wallet': gain}}
        )
        await ctx.reply(f'You got ${gain}.')
    
    @commands.command(cooldown_after_parsing = True)
    @commands.guild_only()
    @commands.cooldown(rate = 1, per = 1 * 60 * 60, type = commands.BucketType.user)
    async def give(self, ctx, member: discord.Member, amount: int):
        if currency_cl.find_one({'user': ctx.author.id}) == None:
            currency_cl.insert_one({
                'user': ctx.author.id,
                'wallet': 0,
                'bank': 0
            })
        if member == ctx.author or member.bot:
            await ctx.reply('No')
            return ctx.command.reset_cooldown(ctx)
        if currency_cl.find_one({'user': member.id}) == None:
            currency_cl.insert_one({
                'user': member.id,
                'wallet': 0,
                'bank': 0
            })
        wallet = currency_cl.find_one({'user': ctx.author.id})['wallet']
        if amount > 0:
            if wallet >= amount:
                currency_cl.find_one_and_update(
                    {'user': ctx.author.id},
                    {'$inc': {'wallet': -amount}}
                )
                currency_cl.find_one_and_update(
                    {'user': member.id},
                    {'$inc': {'wallet': amount}}
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
        if currency_cl.find_one({'user': ctx.author.id}) == None:
            currency_cl.insert_one({
                'user': ctx.author.id,
                'wallet': 0,
                'bank': 0
            })
        if member == ctx.author or member.bot:
            await ctx.reply('No')
            return ctx.command.reset_cooldown(ctx)
        if currency_cl.find_one({'user': member.id}) == None:
            currency_cl.insert_one({
                'user': member.id,
                'wallet': 0,
                'bank': 0
            })
        author_wallet = currency_cl.find_one({'user': ctx.author.id})['wallet']
        member_wallet = currency_cl.find_one({'user': member.id})['wallet']
        if author_wallet >= 20:
            if member_wallet >= 20:
                if random.randint(0, 100) < 50:
                    amount = random.randint(20, max(member_wallet // 3, 20))
                    currency_cl.find_one_and_update(
                        {'user': ctx.author.id},
                        {'$inc': {'wallet': amount}}
                    )
                    currency_cl.find_one_and_update(
                        {'user': member.id},
                        {'$inc': {'wallet': -amount}}
                    )
                    await ctx.reply(f'You stole ${amount} from `{member}`.')
                else:
                    amount = random.randint(20, max(author_wallet // 3, 20))
                    currency_cl.find_one_and_update(
                        {'user': ctx.author.id},
                        {'$inc': {'wallet': -amount}}
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
        if currency_cl.find_one({'user': member.id}) == None:
            currency_cl.insert_one({
                'user': member.id,
                'wallet': 0,
                'bank': 0
            })
        if type in ('wallet', 'bank'):
            currency_cl.find_one_and_update(
                {'user': member.id},
                {'$set': {type: amount}}
            )
            await ctx.reply(f'`{member}`\'s {type} balance has been set to ${amount}.')
        else:
            await ctx.reply('invalid type')
    
    @commands.group()
    @commands.guild_only()
    async def shop(self, ctx):
        if shop_cl.find_one({'guild': ctx.guild.id}) == None:
            shop_cl.insert_one({
                'guild': ctx.guild.id,
                'items': {}
            })
        if ctx.invoked_subcommand == None:
            if shop_cl.find_one({'guild': ctx.guild.id})['items'] == {}:
                await ctx.reply('This shop is empty, check again later.')
            else:
                options = [
                    discord.SelectOption(
                        label = name,
                        description = f'${price}'
                    ) for name, price in shop_cl.find_one({'guild': ctx.guild.id})['items'].items()
                ]

                class Shop(discord.ui.View):
                    @discord.ui.select(placeholder = 'Select an item', options = options)
                    async def menu(self, inter, select):
                        if currency_cl.find_one({'user': inter.user.id}) == None:
                            currency_cl.insert_one({
                                'user': inter.user.id,
                                'wallet': 0,
                                'bank': 0
                            })
                        wallet = currency_cl.find_one({'user': inter.user.id})['wallet']
                        price = shop_cl.find_one({'guild': inter.guild_id})['items'][select.values[0]]
                        if wallet >= price:
                            currency_cl.find_one_and_update(
                                {'user': inter.user.id},
                                {'$inc': {'wallet': -price}}
                            )
                            await inter.response.send_message(f'{inter.user.mention} item "{select.values[0]}" purchased.')
                        else:
                            await inter.response.send_message(f'You are ${price - wallet} short.', ephemeral = True)

                message = await ctx.reply('Shop', view = Shop())
    
    @shop.command()
    @commands.has_guild_permissions(manage_guild = True)
    async def add(self, ctx, name, price: int):
        items = shop_cl.find_one({'guild': ctx.guild.id})['items']
        if name not in items:
            if price >= 0:
                items[name] = price
                shop_cl.find_one_and_update(
                    {'guild': ctx.guild.id},
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
        items = shop_cl.find_one({'guild': ctx.guild.id})['items']
        if name in items:
            if other.isnumeric():
                items[name] = int(other)
                shop_cl.find_one_and_update(
                    {'guild': ctx.guild.id},
                    {'$set': {'items': items}}
                )
                await ctx.reply(f'Item "{name}" edited.')
            else:
                items[other] = items[name]
                del items[name]
                shop_cl.find_one_and_update(
                    {'guild': ctx.guild.id},
                    {'$set': {'items': items}}
                )
                await ctx.reply(f'Item "{name}" edited to "{other}".')
        else:
            await ctx.reply(f'Item "{name}" not found.')
    
    @shop.command()
    @commands.has_guild_permissions(manage_guild = True)
    async def remove(self, ctx, *, name):
        items = shop_cl.find_one({'guild': ctx.guild.id})['items']
        if name in items:
            del items[name]
            shop_cl.find_one_and_update(
                {'guild': ctx.guild.id},
                {'$set': {'items': items}}
            )
            await ctx.reply(f'Item "{name}" removed.')
        else:
            await ctx.reply(f'Item "{name}" not found.')

async def setup(bot):
    await bot.add_cog(Currency())
