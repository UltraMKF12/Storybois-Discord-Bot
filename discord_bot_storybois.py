import discord
from discord import embeds
from discord import message
from discord.ext import commands
import tokens
from StoryBoisEvent import StoryBoisEvent

bot = commands.Bot(command_prefix=".", case_insensitive=True)
storybois = StoryBoisEvent()

@bot.event
async def on_ready():
    print(f"{bot.user} is ready!")

    # Generating the needed text messages to a room
    bot.dispatch("generating_prompt_message_references", tokens.BOT_TEST_ROOM_ID)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Only check for messages in a specific room for testing
    if message.channel.id == tokens.BOT_TEST_ROOM_ID:

        # Need to get rid of the user message as fast as possible for comfort.
        await message.delete()

        # Need this to make the bot check for commands
        await bot.process_commands(message)

        # We don't want commands added to the prompt list.
        if not message.content.startswith("."):
            storybois.add_prompt(message.content, message.author.id)
            bot.dispatch("refresh_prompt")

        return

# ////
# Some commands
# ////

# 2 commands to make users able to edit or delete the prompts they sent in.
@bot.group(invoke_without_command=True)
async def prompt(ctx):
    pass

# .prompt edit {INDEX} {NEW PROMPT}
@prompt.command()
async def edit(ctx, index, *, message):
    storybois.edit_prompt(message, str(ctx.author.id), int(index))
    bot.dispatch("refresh_prompt")

# .prompt delete {INDEX}
@prompt.command()
async def delete(ctx, index):
    storybois.delete_prompt(str(ctx.author.id), int(index))
    bot.dispatch("refresh_prompt")




# Event role specific commands to handle unexpected situations, or bugfixing.
# They can also start and edit events
@bot.group(invoke_without_command=True)
@commands.has_role(tokens.EVENT_ROLE_ID)
async def event(ctx):
    pass

# The most important command. Used to start an event
# .event create {USER} {THEME}
@event.command()
@commands.has_role(tokens.EVENT_ROLE_ID)
async def create(ctx, user: discord.Member, *, theme):
    print(f".event create {user} {theme}")
    bot.dispatch("event_created", ctx, user, theme)

# It simulates subtracts 1 day from the current state.
# .event next
@event.command()
@commands.has_role(tokens.EVENT_ROLE_ID)
async def next(ctx):
    print(".event next")
    storybois.update_time()
    bot.dispatch("refresh_prompt")


# Ends an event
# .event end
@event.command()
@commands.has_role(tokens.EVENT_ROLE_ID)
async def end(ctx):
    print(".event end")

# Deletes an event
# This deletes all messages associated with it.
# .event delete
@event.command()
@commands.has_role(tokens.EVENT_ROLE_ID)
async def delete(ctx):
    print(".event delete")



# A subcommand group for editing event specific details
@event.group(invoke_without_command=True)
@commands.has_role(tokens.EVENT_ROLE_ID)
async def edit(ctx):
    pass

# Changes time left in Prompt Submission state. (in days)
# .event edit prompt {DAYS}
@edit.command()
@commands.has_role(tokens.EVENT_ROLE_ID)
async def prompt(ctx, days):
    print(f".event edit prompt {days}")

# Changes time left in Voting state. (in days)
# .event edit voting {DAYS}
@edit.command()
@commands.has_role(tokens.EVENT_ROLE_ID)
async def voting(ctx, days):
    print(f".event edit voting {days}")

# Changes time left in Story Submission state. (in days)
# .event edit story {DAYS}
@edit.command()
@commands.has_role(tokens.EVENT_ROLE_ID)
async def story(ctx, days):
    print(f".event edit story {days}")





# ////
# Some functions
# ////

# This is for disabling message sending
# bot.dispatch("disable_message", message.channel)
@bot.event
async def on_disable_message(channel):
    print(f"Disabled message sending in {channel.name}")
    await channel.set_permissions(channel.guild.default_role, send_messages=False)


# This is for enabling message sending
# bot.dispatch("enable_message", message.channel)
@bot.event
async def on_enable_message(channel):
    print(f"Enabled message sending in {channel.name}")
    await channel.set_permissions(channel.guild.default_role, send_messages=True)


# Send a message to the prompt channel to notify everyone that a winner has been selected
# bot.dispatch("winner_selected",message.channel, message.author, message.content, "WinnerTest")
@bot.event
async def on_winner_selected(channel, winner, prompt, theme):
    embed=discord.Embed(title=f"The winning prompt for the theme: **{theme}**", description=f"{prompt} {winner.mention}", color=discord.Color.dark_gold())
    embed.set_thumbnail(url=winner.avatar_url)
    await channel.send(embed=embed)


# Handles things needed when an event is created. Currently: Embeds
# bot.dispatch("event_created", theme)
@bot.event
async def on_event_created(ctx, user, theme):
    embed=discord.Embed(title=f"**Event created!**", description=f"Theme of the event is: **{theme}** by:{user.mention}", color=discord.Color.blue())
    embed.set_thumbnail(url=user.avatar_url)
    embed.set_footer(text=f"Event created by: {ctx.author.name}")
    await ctx.channel.send(embed=embed)


# Need to have messages that the bot will edit, to see the current prompts available. Passing those message references to the storybois class.
# Only enables 4 text for prompts
# bot.dispatch("generating_prompt_message_references", tokens.BOT_TEST_ROOM_ID)
@bot.event
async def on_generating_prompt_message_references(channelId):
    channel = bot.get_channel(channelId)
    message = await channel.send("Main message")
    storybois.promptThemeMessageReference = message
    await message.edit(content=storybois.generate_prompt_main_message())

    message = await channel.send(".")
    storybois.promptMessagesReference.append(message)
    message = await  channel.send(".")
    storybois.promptMessagesReference.append(message)
    message = await channel.send(".")
    storybois.promptMessagesReference.append(message)
    message = await channel.send(".")
    storybois.promptMessagesReference.append(message)


# Regenerate the prompt messages to update a change
# bot.dispatch("refresh_prompt")
@bot.event
async def on_refresh_prompt():
    # Refresh theme text
    await storybois.promptThemeMessageReference.edit(content=storybois.generate_prompt_main_message())

    # Refresh prompt texts
    messages = storybois.generate_prompt_messages()
    for i in range(len(messages)):
        await storybois.promptMessagesReference[i].edit(content=messages[i])


# Discord SLASH command plugin
# https://discord-py-slash-command.readthedocs.io/en/latest/quickstart.html
bot.run(tokens.DISCORD_TOKEN)