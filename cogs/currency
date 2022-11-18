import discord
from discord.ext import commands
from replit import db
import random

if 'Currency' not in db:
    db['Currency'] = {} #{'user.id': [0, 0]}
if 'Shop' not in db:
    db['Shop'] = {} #{'guild.id': {'name': price}}

class Currency(commands.Cog):
    @commands.command(aliases = ['bal'])
    async def balance(self, ctx, *, member: discord.Member = None):
        if member == None:
            member = ctx.author
        if member.bot:
            return await ctx.reply('No')
        if str(member.id) not in db['Currency']:
            db['Currency'][str(member.id)] = [0, 0]
        await ctx.reply(embed = discord.Embed(
            title = f"{member.display_name}'s Balance",
            description = f'''
Wallet: ${db["Currency"][str(member.id)][0]}
Bank: ${db["Currency"][str(member.id)][1]}
            ''',
            color = 0xffe5ce
        ).set_footer(
            text = ctx.author.display_name,
            icon_url = ctx.author.display_avatar.url
        ))
    
    @commands.command(aliases = ['lb'])
    async def leaderboard(self, ctx):
        paginator = tuple(f'{index}. `{member}`: ${amount}' for index, (member, amount) in enumerate(sorted(filter(lambda i: i[0] != None and i[1] > 0, ((ctx.guild.get_member(int(i[0])), sum(i[1])) for i in db['Currency'].items())), key = lambda i: i[1], reverse = True), start = 1))
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
        if str(ctx.author.id) not in db['Currency']:
            db['Currency'][str(ctx.author.id)] = [0, 0]
        if amount.lower() == 'all':
            amount = db['Currency'][str(ctx.author.id)][0]
        else:
            amount = int(amount)
        if amount > 0:
            if db['Currency'][str(ctx.author.id)][0] >= amount:
                db['Currency'][str(ctx.author.id)][0] -= amount
                db['Currency'][str(ctx.author.id)][1] += amount
                await ctx.reply(f'${amount} deposited.')
            else:
                await ctx.reply(f"You're ${amount - db['Currency'][str(ctx.author.id)][0]} short.")
        else:
            await ctx.reply('amount must be greater than 0.')
    
    @commands.command(aliases = ['with'])
    async def withdraw(self, ctx, amount):
        if str(ctx.author.id) not in db['Currency']:
            db['Currency'][str(ctx.author.id)] = [0, 0]
        if amount.lower() == 'all':
            amount = db['Currency'][str(ctx.author.id)][1]
        else:
            amount = int(amount)
        if amount > 0:
            if db['Currency'][str(ctx.author.id)][1] >= amount:
                db['Currency'][str(ctx.author.id)][0] += amount
                db['Currency'][str(ctx.author.id)][1] -= amount
                await ctx.reply(f'${amount} withdrawn.')
            else:
                await ctx.reply(f"You're ${amount - db['Currency'][str(ctx.author.id)][1]} short.")
        else:
            await ctx.reply('amount must be greater than 0.')
    
    @commands.command(cooldown_after_parsing = True)
    @commands.cooldown(rate = 1, per = 1 * 60 * 60, type = commands.BucketType.user)
    async def work(self, ctx):
        if str(ctx.author.id) not in db['Currency']:
            db['Currency'][str(ctx.author.id)] = [0, 0]
        gain = random.randint(1, 10)
        db['Currency'][str(ctx.author.id)][0] += gain
        await ctx.reply(f'You got ${gain}.')
    
    @commands.command(cooldown_after_parsing = True)
    @commands.guild_only()
    @commands.cooldown(rate = 1, per = 1 * 60 * 60, type = commands.BucketType.user)
    async def give(self, ctx, member: discord.Member, amount: int):
        if str(ctx.author.id) not in db['Currency']:
            db['Currency'][str(ctx.author.id)] = [0, 0]
        if member == ctx.author or member.bot:
            await ctx.reply('No')
            return ctx.command.reset_cooldown(ctx)
        if str(member.id) not in db['Currency']:
            db['Currency'][str(member.id)] = [0, 0]
        if amount > 0:
            if db['Currency'][str(ctx.author.id)][0] >= amount:
                db['Currency'][str(ctx.author.id)][0] -= amount
                db['Currency'][str(member.id)][0] += amount
                await ctx.reply(f'You gave ${amount} to `{member}`.')
            else:
                await ctx.reply(f"You're ${amount - db['Currency'][str(ctx.author.id)][0]} short.")
                ctx.command.reset_cooldown(ctx)
        else:
            await ctx.reply('amount must be greater than 0.')
            ctx.command.reset_cooldown(ctx)
    
    @commands.command(cooldown_after_parsing = True)
    @commands.guild_only()
    @commands.cooldown(rate = 1, per = 2 * 60 * 60, type = commands.BucketType.user)
    async def rob(self, ctx, *, member: discord.Member):
        if str(ctx.author.id) not in db['Currency']:
            db['Currency'][str(ctx.author.id)] = [0, 0]
        if member == ctx.author or member.bot:
            await ctx.reply('No')
            return ctx.command.reset_cooldown(ctx)
        if str(member.id) not in db['Currency']:
            db['Currency'][str(member.id)] = [0, 0]
        if db['Currency'][str(ctx.author.id)][0] >= 20:
            if db['Currency'][str(member.id)][0] >= 20:
                if random.randint(0, 100) < 50:
                    amount = random.randint(20, max(db['Currency'][str(member.id)][0] // 3, 20))
                    db['Currency'][str(ctx.author.id)][0] += amount
                    db['Currency'][str(member.id)][0] -= amount
                    await ctx.reply(f'You stole ${amount} from `{member}`.')
                else:
                    amount = random.randint(20, max(db['Currency'][str(ctx.author.id)][0] // 3, 20))
                    db['Currency'][str(ctx.author.id)][0] -= amount
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
        if str(member.id) not in db['Currency']:
            db['Currency'][str(member.id)] = [0, 0]
        try:
            db['Currency'][str(member.id)][('wallet', 'bank').index(type)] = amount
            await ctx.reply(f"`{member}`'s {type} balance has been set to ${amount}.")
        except KeyError:
            await ctx.reply('invalid type')
    
    @commands.group()
    @commands.guild_only()
    async def shop(self, ctx):
        if str(ctx.guild.id) not in db['Shop']:
            db['Shop'][str(ctx.guild.id)] = {} #{'name': price}
        if ctx.invoked_subcommand == None:
            if db['Shop'][str(ctx.guild.id)] == {}:
                await ctx.reply('This shop is empty, check again later.')
            else:
                options = [discord.SelectOption(label = name, description = f'${price}') for name, price in db['Shop'][str(ctx.guild.id)].items()]

                class Shop(discord.ui.View):
                    @discord.ui.select(placeholder = 'Select an item', options = options)
                    async def menu(self, inter, select):
                        if str(inter.user.id) not in db['Currency']:
                            db['Currency'][str(inter.user.id)] = [0, 0]
                        if db['Currency'][str(inter.user.id)][0] >= db['Shop'][str(ctx.guild.id)][select.values[0]]:
                            db['Currency'][str(inter.user.id)][0] -= db['Shop'][str(ctx.guild.id)][select.values[0]]
                            await inter.response.send_message(f'{inter.user.mention} item "{select.values[0]}" purchased.')
                        else:
                            await inter.response.send_message(f'You are ${db["Shop"][str(ctx.guild.id)][select.values[0]] - db["Currency"][str(inter.user.id)][0]} short.', ephemeral = True)

                message = await ctx.reply('Shop', view = Shop())
    
    @shop.command()
    @commands.has_guild_permissions(manage_guild = True)
    async def add(self, ctx, name, price: int):
        if name not in db['Shop'][str(ctx.guild.id)]:
            if price >= 0:
                db['Shop'][str(ctx.guild.id)][name] = price
                await ctx.reply(f'Item "{name}" added.')
            else:
                await ctx.reply('price must be greater than or equal to 0.')
        else:
            await ctx.reply(f'Item "{name}" is already added.')
    
    @shop.command()
    @commands.has_guild_permissions(manage_guild = True)
    async def edit(self, ctx, name, other):
        if name in db['Shop'][str(ctx.guild.id)]:
            if other.isnumeric():
                db['Shop'][str(ctx.guild.id)][name] = int(other)
                await ctx.reply(f'Item "{name}" edited.')
            else:
                db['Shop'][str(ctx.guild.id)][other] = db['Shop'][str(ctx.guild.id)][name]
                del db['Shop'][str(ctx.guild.id)][name]
                await ctx.reply(f'Item "{name}" edited to "{other}".')
        else:
            await ctx.reply(f'Item "{name}" not found.')
    
    @shop.command()
    @commands.has_guild_permissions(manage_guild = True)
    async def remove(self, ctx, *, name):
        if name in db['Shop'][str(ctx.guild.id)]:
            del db['Shop'][str(ctx.guild.id)][name]
            await ctx.reply(f'Item "{name}" removed.')
        else:
            await ctx.reply(f'Item "{name}" not found.')

async def setup(bot):
    await bot.add_cog(Currency())
