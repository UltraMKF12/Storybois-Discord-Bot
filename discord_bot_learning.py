import discord
from discord import embeds
from discord.ext import commands

bot = commands.Bot(command_prefix=".", case_insensitive=True)
forbidden_words = ["alma", "kaka", "kuki"]


@bot.event
async def on_ready():
    print(f"{bot.user} is ready!")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if isinstance(message.channel, discord.channel.DMChannel):
        await message.channel.send("Use the StoryBois Discord Sever to talk with me!")

    if any(word in message.content.lower() for word in forbidden_words):
        await message.delete()
        await message.channel.send(f"{message.author.mention} That is a forbidden word!")
        bot.dispatch('forbidden', message, "alma")
        return

    else:
        await bot.process_commands(message)


@bot.event
async def on_forbidden(message, word):
    channel = bot.get_channel(879779070861266954)

    embed = discord.Embed(title = "Forbidden Word ALERT!", description=f"{message.author.name} just said ||{message.content}||\nThe {word} be with you brave men!", color=discord.Color.blurple())

    await message.author.send("DO NOT USE FORBIDDEN WORDS!!")
    await channel.send(embed=embed)


@bot.command(description="Just a test commant to test things")
async def test(ctx):
    await ctx.send(f"Tested by: {ctx.author.name}")


@bot.command(title="welcome", description="Sends and embed to the user")
async def welcome(ctx):
    try:
        embed = discord.Embed(title=f"Welcome {ctx.author.name}", description=f"Thanks for being part of {ctx.author.guild.name}!")

    #Made it work in DM's.
    except:
        embed = discord.Embed(title=f"Welcome {ctx.author.name}", description=f"Thanks for being part of the TEST!")
    
    if isinstance(ctx.channel, discord.channel.DMChannel):
        await ctx.send("Also thanks for DM-ing me")

    embed.set_thumbnail(url=ctx.author.avatar_url)

    await ctx.send(embed=embed)

# Discord SLASH command plugin
# https://discord-py-slash-command.readthedocs.io/en/latest/quickstart.html
bot.run("ODc5NDA0MTQwMDI2MDA3NjAy.YSPO7Q.H-1j6eKIszH0ncTVd0_lZw-DVBc")