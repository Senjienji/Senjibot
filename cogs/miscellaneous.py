import discord
from discord.ext import commands
from replit import db
import asyncio
import random
import time
import json

class Miscellanous(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.help_command.cog = self

    @commands.command(name = "eval")
    async def evaluate(self, ctx, *, content):
        await ctx.reply(embed = discord.Embed(
            title = "Evaluation",
            description = str(eval(content, {
                "ctx": ctx,
                "bot": self.bot,
                "discord": discord,
                "choose": random.choice,
                "timestamp": time.time,
                "shuffle": lambda x: random.sample(x, len(x)),
                "db": json.loads(db.dumps(dict(db))),
                "replied": (ctx.message.reference.resolved if ctx.message.reference != None else None)
            }, {
                "__import__": None,
                "copyright": None,
                "credits": None,
                "license": None,
                "print": None,
                "eval": None,
                "exec": None,
                "help": None,
                "exit": None,
                "quit": None,
                "open": None
            })),
            color = 0xffe5ce
        ).set_footer(
            text = ctx.author.display_name,
            icon_url = ctx.author.avatar
        ))
    
    @commands.command(aliases = ["chr"])
    async def character(self, ctx, *, content):
        await ctx.reply(sum(ord(i) for i in content) / len(content))
    
    @commands.command()
    async def math(self, ctx):
        equation = f"{random.randint(1, 99)} {random.choice(('+', '-', '*', '%', '//'))} {random.randint(1, 99)}"
        reply = await ctx.reply(f"{equation} = ?")
        try:
            message = await self.bot.wait_for("message", check = lambda message: message.channel == ctx.channel and message.author == ctx.author, timeout = 60)
            embed = discord.Embed(
                description = f"{equation} = {eval(equation)}",
                color = 0xffe5ce
            ).set_footer(
                text = f"{int((message.created_at - reply.created_at).total_seconds())} seconds"
            )
            try:
                if int(message.content) == eval(equation):
                    embed.title = "Correct!"
                else:
                    embed.title = "Wrong!"
            except ValueError:
                embed.title = "Invalid number passed."
            await message.reply(embed = embed)
        except asyncio.TimeoutError:
            await reply.edit(content = f"{equation} = {eval(equation)}\nYou didn't reply in time.")
    
    @commands.command()
    async def rps(self, ctx, member: discord.Member = None):
        if member == None:
            member = self.bot.user
        if member == ctx.author:
            return await ctx.reply("No")
        view = discord.ui.View(timeout = 60)
        view.add_item(discord.ui.Select(placeholder = "Select a move", options = [discord.SelectOption(
            label = "Rock",
            emoji = "🪨"
        ), discord.SelectOption(
            label = "Paper",
            emoji = "📄"
        ), discord.SelectOption(
            label = "Scissors",
            emoji = "✂️"
        )]))
        message = await ctx.reply(f"{ctx.author.mention} Select a move:", view = view)
        try:
            interaction = await self.bot.wait_for("interaction", check = lambda interaction: interaction.message == message and interaction.user == ctx.author, timeout = 60)
            moves = ("Rock", "Paper", "Scissors")
            p1 = moves.index(view.children[0].values[0])
            if member.bot:
                p2 = random.randint(0, 2)
            else:
                await message.edit(content = f"{member.mention} Select a move:")
                try:
                    interaction = await bot.wait_for("interaction", check = lambda interaction: interaction.message == message and interaction.user == member, timeout = 60)
                    p2 = moves.index(view.children[0].values[0])
                except asyncio.TimeoutError:
                    await message.edit(content = f"{member.mention} You didn't select in time.", view = None)
                    return view.stop()
            if p1 - p2 in (-2, 1):
                content = f"{ctx.author.display_name} won!"
            elif p1 - p2 in (-1, 2):
                content = f"{member.display_name} won!"
            else:
                content = "It's a tie!"
            content += f"\n\n`{ctx.author.display_name}`: {moves[p1]}\n`{member.display_name}`: {moves[p2]}"
            await message.edit(content = content, view = None)
        except asyncio.TimeoutError:
            await message.edit(content = f"{ctx.author.mention} You didn't select in time.", view = None)
            return view.stop()
    
    @commands.command(aliases = ["cd"])
    async def cooldown(self, ctx):
        await ctx.reply(embed = discord.Embed(
            title = "Cooldowns",
            description = "\n".join(f"{index}. `{command.name}`: <t:{int(time.time() + command.get_cooldown_retry_after(ctx))}:F>" for index, command in enumerate(filter(lambda command: command.is_on_cooldown(ctx), self.bot.commands), start = 1)) or "Nothing found.",
            color = 0xffe5ce
        ).set_footer(
            text = ctx.author.display_name,
            icon_url = ctx.author.avatar
        ))
    
    @commands.command()
    async def embed(self, ctx, title, description):
        embed = discord.Embed(
            title = title,
            description = description,
            color = 0xffe5ce
        )
        if ctx.message.attachments != []:
            embed.set_image(url = ctx.message.attachments[0].url)
        await ctx.send(embed = embed)
    
    @commands.command()
    async def invite(self, ctx):
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            label = "Invite",
            url = "https://Senjibot.senjienji.repl.co/invite",
            style = discord.ButtonStyle.link
        ))
        await ctx.reply("<https://Senjibot.senjienji.repl.co/invite>", view = view)
    
    @commands.command()
    async def bot(self, ctx):
        await ctx.reply(embed = discord.Embed(
            title = "Bot Info",
            description = f"""
In: {len(self.bot.guilds)} guilds
Latency: {int(self.bot.latency * 1000)}ms
Uptime: <t:{int(self.bot.launch_time)}:R>
Version: {discord.__version__}
            """,
            color = 0xffe5ce
        ).set_footer(
            text = ctx.author.display_name,
            icon_url = ctx.author.avatar
        ))
    
    @commands.command()
    async def emoji(self, ctx, *, emoji: discord.Emoji):
        await ctx.reply(emoji.url)
    
    @commands.command()
    async def poll(self, ctx, name, *options):
        message = await ctx.send(embed = discord.Embed(
            title = f"Poll: {name}",
            description = "\n".join(f"{index}. {option}" for index, option in enumerate(options[:10], start = 1)),
            color = 0xffe5ce
        ).set_footer(
            text = f"By {ctx.author}",
            icon_url = ctx.author.avatar
        ))
        for i in range(len(options[:10])):
            await message.add_reaction("1️⃣ 2️⃣ 3️⃣ 4️⃣ 5️⃣ 6️⃣ 7️⃣ 8️⃣ 9️⃣ 🔟".split()[i])

def setup(bot):
    bot.add_cog(Miscellanous(bot))