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
        page = 0
        view = discord.ui.View(timeout = 60)
        view.add_item(discord.ui.Button(
            label = 'Previous',
            emoji = '⬅️',
            custom_id = '-10'
        ))
        view.add_item(discord.ui.Button(
            label = 'Next',
            emoji = '➡️',
            custom_id = '10'
        ))
        message = await ctx.reply(embed = discord.Embed(
            title = 'Leaderboard',
            description = '\n'.join(paginator[page:page + 10]),
            color = 0xffe5ce
        ).set_footer(
            text = ctx.author.display_name,
            icon_url = ctx.author.display_avatar.url
        ), view = view)
        while True:
            try:
                interaction = await ctx.bot.wait_for('interaction', check = lambda interaction: interaction.message == message, timeout = 60)
                if interaction.user == ctx.author:
                    page += int(interaction.data['custom_id'])
                    page = min(max(page, 0), (len(paginator) - 1) // 10 * 10)
                    await message.edit(embed = discord.Embed(
                        title = 'Leaderboard',
                        description = '\n'.join(paginator[page:page + 10]),
                        color = 0xffe5ce
                    ).set_footer(
                        text = ctx.author.display_name,
                        icon_url = ctx.author.display_avatar.url
                    ))
                else:
                    await interaction.followup.send('This button is not for you.', ephemeral = True)
            except discord.utils.asyncio.TimeoutError:
                await message.edit(view = None)
                view.stop()
                break
    
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
        gain = random.randint(1000, 2500)
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
        if db['Currency'][str(ctx.author.id)][0] >= 500:
            if db['Currency'][str(member.id)][0] >= 500:
                if random.randint(0, 100) < 50:
                    amount = random.randint(500, max(db['Currency'][str(member.id)][0] // 3, 500))
                    db['Currency'][str(ctx.author.id)][0] += amount
                    db['Currency'][str(member.id)][0] -= amount
                    await ctx.reply(f'You stole ${amount} from `{member}`.')
                else:
                    amount = random.randint(500, max(db['Currency'][str(ctx.author.id)][0] // 3, 500))
                    db['Currency'][str(ctx.author.id)][0] -= amount
                    await ctx.reply(f'You got caught and lost ${amount}.')
            else:
                await ctx.reply('Your target has less than $500.')
                ctx.command.reset_cooldown(ctx)
        else:
            await ctx.reply('You need at least $500 to rob someone.')
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
        if str(ctx.guild.id) not in db['Shop'] or db['Shop'][str(ctx.guild.id)] == {}:
            db['Shop'][str(ctx.guild.id)] = {'nothing': 0} #{'name': price}
        if ctx.invoked_subcommand == None:
            menu = discord.ui.Select(placeholder = 'Select an item')
            for name, price in db['Shop'][str(ctx.guild.id)].items():
                menu.add_option(
                    label = f'{name}: ${price}',
                    value = name
                )
            view = discord.ui.View(timeout = 1 * 60 * 60)
            view.add_item(menu)
            message = await ctx.reply('Shop', view = view)
            while True:
                try:
                    interaction = await ctx.bot.wait_for('interaction', check = lambda interaction: interaction.message == message, timeout = 1 * 60 * 60)
                    if str(interaction.user.id) not in db['Currency']:
                        db['Currency'][str(interaction.user.id)] = [0, 0]
                    if db['Currency'][str(interaction.user.id)][0] >= db['Shop'][str(ctx.guild.id)][view.children[0].values[0]]:
                        db['Currency'][str(interaction.user.id)][0] -= db['Shop'][str(ctx.guild.id)][view.children[0].values[0]]
                        await interaction.followup.send(f'{interaction.user.mention} item "{view.children[0].values[0]}" purchased.')
                    else:
                        await interaction.followup.send(f'You are ${db["Shop"][str(ctx.guild.id)][view.children[0].values[0]] - db["Currency"][str(interaction.user.id)][0]} short.', ephemeral = True)
                except discord.utils.asyncio.TimeoutError:
                    await message.edit(view = None)
                    menu.disable = True
                    view.stop()
                    break
    
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

def setup(bot):
    bot.add_cog(Currency())