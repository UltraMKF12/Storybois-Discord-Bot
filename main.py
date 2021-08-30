import discord
from discord import embeds
from discord import message
from discord.ext import commands
import tokens
from StoryBoisEvent import StoryBoisEvent
from discord.ext import tasks
import datetime
from number_to_emoji import number_to_emoji

bot = commands.Bot(command_prefix=".", case_insensitive=True)
storybois = None
#Here comes command that loads storybois from database

@bot.event
async def on_ready():
    print(f"{bot.user} is ready!")

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
        if not message.content.startswith(".") and storybois != None:
            if storybois.currentState == "prompt":
                storybois.add_prompt(message.content, message.author.id)
                storybois.promptSenders[message.author.id] = message.author # Need this for us to be able to reference the winner prompt author
                bot.dispatch("refresh_prompt")

        return

# This function is responsible for updating the time left
# Check every hour if its a new day ()
@tasks.loop(hours=1)
async def update_time():
    if storybois != None and datetime.datetime.now().hour == 0:
        bot.dispatch("check_and_update_state")
    
    elif storybois == None:
        update_time.stop()




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
@bot.group(invoke_without_command=True, aliases=["e"])
@commands.has_role(tokens.EVENT_ROLE_ID)
async def event(ctx):
    pass


# The most important command. Used to start an event
# .event create {USER} {THEME}
@event.command(aliases=["c"])
@commands.has_role(tokens.EVENT_ROLE_ID)
async def create(ctx, user: discord.Member, *, theme):
    if storybois == None:
        print(f".event create {user} {theme}")

        # Create or Load event class
        bot.dispatch("create_storybois_event", theme, user)

        bot.dispatch("send_event_main_message", tokens.BOT_TEST_ROOM_ID)

        # Generating the needed text messages to a room
        bot.dispatch("generating_prompt_message_references", tokens.BOT_TEST_ROOM_ID)

        update_time.cancel() # Start the timer to check for a new day
    else:
        await ctx.send(f"`Event already started with the theme: {storybois.theme}`")


# It simulates subtracts 1 day from the current state.
# .event next
@event.command(aliases=["n"])
@commands.has_role(tokens.EVENT_ROLE_ID)
async def next(ctx):
    print(".event next")
    bot.dispatch("check_and_update_state")
    bot.dispatch("refresh_prompt")


# Ends an event
# .event end
@event.command()
@commands.has_role(tokens.EVENT_ROLE_ID)
async def end(ctx):
    update_time.stop() # Stop updating the timer
    print(".event end")
    global storybois
    storybois = None



# CREATES AN ERROR ON EVENT CREATION. I HAVE NO IDEA WHAT THE PROBLEM MIGHT BE
# Deletes an event
# This deletes all messages associated with it.
# .event delete
@event.command()
@commands.has_role(tokens.EVENT_ROLE_ID)
async def delete(ctx):
    update_time.stop() # Stop updating the timer
    global storybois
    #Remove instance from database HERE
    await storybois.promptThemeMessageReference.delete()
    for message in storybois.promptMessagesReference:
        await message.delete()
    
    if storybois.votingMessageReference != None:
        await storybois.votingMessageReference.delete()
    
    if storybois.storyMessageReference != None:
        await storybois.storyMessageReference.delete()

    bot.dispatch("event_deleted", ctx, storybois.theme)
    storybois = None




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
    if storybois != None:
        print(f".event edit prompt {days}")
        storybois.timePrompt = int(days)
        bot.dispatch("refresh_event_main_message")

# Changes time left in Voting state. (in days)
# .event edit vote {DAYS}
@edit.command()
@commands.has_role(tokens.EVENT_ROLE_ID)
async def vote(ctx, days):
    if storybois != None:
        print(f".event edit vote {days}")
        storybois.timeVote = int(days)
        if(storybois.currentState == "voting"):
            bot.dispatch("refresh_vote_message")

# Changes time left in Story Submission state. (in days)
# .event edit story {DAYS}
@edit.command()
@commands.has_role(tokens.EVENT_ROLE_ID)
async def story(ctx, days):
    if storybois != None:
        print(f".event edit story {days}")
        storybois.timeStory = int(days)
        #REFRESH STORY MESSAGE





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
async def on_winner_selected(channelID):
    channel = bot.get_channel(channelID)

    embed=discord.Embed(title=f"The winning prompt for the theme: **{storybois.theme}**", description=f"{storybois.winningPrompt}", color=discord.Color.dark_gold())
    embed.set_thumbnail(url=storybois.winningPromptUser.avatar_url)
    await channel.send(embed=embed)


# Handles things needed when an event is created. Currently: Embeds
# bot.dispatch("send_event_main_message", user, theme)
@bot.event
async def on_send_event_main_message(channelID):
    channel = bot.get_channel(channelID)

    embed=discord.Embed(title=f"**Event created!**", description=f"Theme >> **{storybois.theme}** {storybois.themeUser.mention}", color=discord.Color.blue())
    embed.set_thumbnail(url=storybois.themeUser.avatar_url)
    # embed.set_footer(text=f"Event created by: {ctx.author.name}")
    embed.set_footer(text=f"Voting starts in: {storybois.timePrompt} day")
    storybois.promptThemeMessageReference = await channel.send(embed=embed)


@bot.event
async def on_refresh_event_main_message():
    embed=discord.Embed(title=f"**Event created!**", description=f"Theme >> **{storybois.theme}** {storybois.themeUser.mention}", color=discord.Color.blue())
    embed.set_thumbnail(url=storybois.themeUser.avatar_url)
    # embed.set_footer(text=f"Event created by: {ctx.author.name}")
    if (storybois.currentState == "prompt"):
        embed.set_footer(text=f"Voting starts in: {storybois.timePrompt} day")
    else:
        embed.set_footer(text=f"Voting started!")
    await storybois.promptThemeMessageReference.edit(embed=embed)

# Handles things needed when an event is deleted. Currently: Embeds
# bot.dispatch("event_deleted", theme)
@bot.event
async def on_event_deleted(ctx, theme):
    embed=discord.Embed(title=f"**Event DELETED!**", description=f"Theme of the event was: **{theme}**!", color=discord.Color.dark_red())
    embed.set_thumbnail(url=ctx.author.avatar_url)
    embed.set_footer(text=f"Event deleted by: {ctx.author.name}")
    await ctx.channel.send(embed=embed)


# Need to have messages that the bot will edit, to see the current prompts available. Passing those message references to the storybois class.
# Only enables 4 text for prompts
# bot.dispatch("generating_prompt_message_references", tokens.BOT_TEST_ROOM_ID)
@bot.event
async def on_generating_prompt_message_references(channelId):
    channel = bot.get_channel(channelId)
    # message = await channel.send("Main message")
    # storybois.promptThemeMessageReference = message
    # await message.edit(content=storybois.generate_prompt_main_message())

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
    # await storybois.promptThemeMessageReference.edit(content=storybois.generate_prompt_main_message())

    # Refresh prompt texts
    messages = storybois.generate_prompt_messages()
    for i in range(len(messages)):
        await storybois.promptMessagesReference[i].edit(content=messages[i])


# bot.dispatch("create_storybois_event")
@bot.event
async def on_create_storybois_event(theme, user):
    #check database if it has an event saved!!
    
    global storybois
    storybois = StoryBoisEvent(theme=theme)
    storybois.promptMessagesReference = [] # Need this, because for some unknown reason it updates the OLD messages. Fixes bug with .event delete
    storybois.themeUser = user

@bot.event
async def on_send_vote_message(channelID):
    channel = bot.get_channel(channelID)

    embed=discord.Embed(title="Voting started!", description=f"Vote for prompts you like!\nTime left: **{storybois.timeVote} day**", color=discord.Color.green())
    storybois.votingMessageReference = await channel.send(embed=embed)

    for i in range(len(storybois.prompts)):
        await storybois.votingMessageReference.add_reaction(number_to_emoji[i])

@bot.event
async def on_refresh_vote_message():
    embed=discord.Embed(title="Voting started!", description=f"Vote for prompts you like!\nTime left: **{storybois.timeVote} day**", color=discord.Color.green())
    await storybois.votingMessageReference.edit(embed=embed)

@bot.event
async def on_vote_end_message_change():
    embed=discord.Embed(title="Voting ended!", color=discord.Color.red())
    await storybois.votingMessageReference.edit(embed=embed)

@bot.event
async def on_count_votes(channelID):
    channel = bot.get_channel(channelID)
    msg = await channel.fetch_message(storybois.votingMessageReference.id)

    reactionList = []

    for reaction in msg.reactions:
        reactionList.append(reaction.count)
    
    # Gets the index of the most upvoted prompts
    m = max(reactionList)
    reactionList = [i for i, j in enumerate(reactionList) if j == m]

    print(reactionList)
    storybois.select_winner(reactionList)

    bot.dispatch("winner_selected", channelID)


@bot.event
async def on_check_and_update_state():
    global storybois
    state = storybois.update_time()

    if state == "prompt":
        bot.dispatch("refresh_event_main_message")
        bot.dispatch("refresh_prompt")

    elif state == "voting":
        bot.dispatch("refresh_event_main_message")
        bot.dispatch("refresh_prompt")

        if storybois.votingMessageReference == None:
            bot.dispatch("send_vote_message", tokens.BOT_TEST_ROOM_ID)
            bot.dispatch("disable_message", tokens.PROMPT_ROOM_ID)
        else:
            bot.dispatch("refresh_vote_message")

    elif state == "story":
        if storybois.storyMessageReference == None:
            #MAKE STORY MESSAGE
            bot.dispatch("count_votes", tokens.BOT_TEST_ROOM_ID)
            bot.dispatch("vote_end_message_change")
            bot.dispatch("enable_message", tokens.STORY_ROOM_ID)
        else:
            #UPDATE STORY MESSAGE
            pass

    elif state == "end":
        update_time.stop() # Stop updating the timer
        storybois = None
        bot.dispatch("disable_message", tokens.STORY_ROOM_ID)
        #Some Kind of EVENT ENDED MESSAGE


# Discord SLASH command plugin
# https://discord-py-slash-command.readthedocs.io/en/latest/quickstart.html
bot.run(tokens.DISCORD_TOKEN)
