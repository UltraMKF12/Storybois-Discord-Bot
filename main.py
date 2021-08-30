import discord
from discord.ext import commands
import tokens
from StoryBoisEvent import StoryBoisEvent
from discord.ext import tasks
import datetime
from number_to_emoji import number_to_emoji
from keep_alive import keep_alive
import os

bot = commands.Bot(command_prefix=".", case_insensitive=True)
storybois = None
reference_loaded = True

@bot.event
async def on_ready():
    print(f"{bot.user} is ready!")
    if os.path.isfile("storybois.data"):
        global reference_loaded
        reference_loaded = False

        global storybois
        storybois = StoryBoisEvent()
        storybois.load_data()

        channel_prompt = bot.get_channel(tokens.PROMPT_ROOM_ID)
        channel_story = bot.get_channel(tokens.STORY_ROOM_ID)
        channel_general = bot.get_channel(tokens.GENERAL_ROOM_ID)

        try:
            storybois.storyMessageReference = await channel_story.fetch_message(storybois.storyMessageReferenceID)
        except:
            pass

        try:
            storybois.winnerMessageReference = await channel_prompt.fetch_message(storybois.winnerMessageReferenceID)
        except:
            pass

        try:
            storybois.votingMessageReference = await channel_prompt.fetch_message(storybois.votingMessageReferenceID)
        except:
            pass

        for i in range(3):
            try:
                storybois.promptThemeMessageReference.append(await channel_prompt.fetch_message(storybois.promptThemeMessageReferenceID[i]))
            except:
                try:
                    storybois.promptThemeMessageReference.append(await channel_story.fetch_message(storybois.promptThemeMessageReferenceID[i]))
                except:
                    try:
                        storybois.promptThemeMessageReference.append(await channel_general.fetch_message(storybois.promptThemeMessageReferenceID[i]))
                    except:
                        pass

        for i in range(4):
            storybois.promptMessagesReference.append(await channel_prompt.fetch_message(storybois.promptMessagesReferenceID[i]))
        
        reference_loaded = True
        print("MESSAGE REFERENCES LOADED!")


        
        
    

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    # if not reference_loaded and channel.id in[tokens.PROMPT_ROOM_ID, tokens.STORY_ROOM_ID]:
    #     await message.delete()

    # Handling prompt sending and voting state
    if message.channel.id == tokens.PROMPT_ROOM_ID and reference_loaded:
        await message.delete()
        await bot.process_commands(message)

        # We don't want commands added to the prompt list.
        if not message.content.startswith(".") and storybois != None:
            if storybois.currentState == "prompt":
                storybois.add_prompt(message.content, message.author.id)
                bot.dispatch("refresh_prompt")
    
    # Handling story state
    elif message.channel.id == tokens.STORY_ROOM_ID and reference_loaded:
        await message.delete()
        await bot.process_commands(message)

        if not message.content.startswith(".") and storybois != None:
            if storybois.currentState == "story":
                storybois.user_to_story_link[f"{message.author.mention}"] = message.content
                bot.dispatch("refresh_story_message")
                storybois.save_data()


# This function is responsible for updating the time left
# Check every hour if its a new day ()
@tasks.loop(hours=1)
async def update_time():
    current_time = datetime.datetime.now()
    print(f"TIMER LOOP! - Current time(h:m:s) >> {current_time.hour}:{current_time.minute}:{current_time.second}")
    if storybois != current_time.hour == 0:
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
        update_time.cancel() # Start the timer to check for a new day

        bot.dispatch("disable_message", tokens.STORY_ROOM_ID)
        bot.dispatch("enable_message", tokens.PROMPT_ROOM_ID)

        # Create or Load event class
        bot.dispatch("create_storybois_event", theme, user)

        bot.dispatch("send_event_main_message", tokens.STORY_ROOM_ID)
        bot.dispatch("send_event_main_message", tokens.GENERAL_ROOM_ID)
        bot.dispatch("send_event_main_message", tokens.PROMPT_ROOM_ID) # Also generates Prompt messages

    else:
        await ctx.send(f"`Event already started with the theme: {storybois.theme}`")


# It simulates subtracts 1 day from the current state.
# .event next
@event.command(aliases=["n"])
@commands.has_role(tokens.EVENT_ROLE_ID)
async def next(ctx):
    print(".event next")
    bot.dispatch("check_and_update_state")


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

    if storybois != None:
        # Removing multiple messages for prompt entry
        for message in storybois.promptMessagesReference:
            await message.delete()

        # These messages are sent to multiple channels
        for message in storybois.promptThemeMessageReference:
            await message.delete()


        if storybois.winnerMessageReference != None:
            await storybois.winnerMessageReference.delete()

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
        if storybois.currentState == "prompt":
            bot.dispatch("refresh_event_main_message")
            storybois.save_data()

# Changes time left in Voting state. (in days)
# .event edit vote {DAYS}
@edit.command()
@commands.has_role(tokens.EVENT_ROLE_ID)
async def vote(ctx, days):
    if storybois != None:
        print(f".event edit vote {days}")
        storybois.timeVote = int(days)
        if storybois.currentState == "voting":
            bot.dispatch("refresh_event_main_message")
            bot.dispatch("refresh_vote_message")
            storybois.save_data()

# Changes time left in Story Submission state. (in days)
# .event edit story {DAYS}
@edit.command()
@commands.has_role(tokens.EVENT_ROLE_ID)
async def story(ctx, days):
    if storybois != None:
        print(f".event edit story {days}")
        storybois.timeStory = int(days)
        if storybois.currentState == "story":
            bot.dispatch("refresh_event_main_message")
            bot.dispatch("refresh_story_message")
            storybois.save_data()





# ////
# Some functions
# ////

# This is for disabling message sending
# bot.dispatch("disable_message", message.channel)
@bot.event
async def on_disable_message(channelID):
    channel = bot.get_channel(channelID)
    print(f"Disabled message sending in {channel.name}")
    await channel.set_permissions(channel.guild.default_role, send_messages=False)


# This is for enabling message sending
# bot.dispatch("enable_message", message.channel)
@bot.event
async def on_enable_message(channelID):
    channel = bot.get_channel(channelID)
    print(f"Enabled message sending in {channel.name}")
    await channel.set_permissions(channel.guild.default_role, send_messages=True)


# Send a message to the prompt channel to notify everyone that a winner has been selected
# bot.dispatch("winner_selected",message.channel, message.author, message.content, "WinnerTest")
@bot.event
async def on_winner_selected(channelID):
    channel = bot.get_channel(channelID)
    winningPromptUser = await bot.fetch_user(storybois.winningPromptUser)

    embed=discord.Embed(title=f"The winning prompt for the theme: **{storybois.theme}**", description=f"{storybois.winningPrompt}", color=discord.Color.dark_gold())
    embed.set_thumbnail(url=winningPromptUser.avatar_url)
    msg = await channel.send(embed=embed)
    storybois.winnerMessageReference = msg
    storybois.winnerMessageReferenceID = msg.id

    bot.dispatch("create_story_message",tokens.STORY_ROOM_ID)


# Handles things needed when an event is created. Currently: Embeds
# bot.dispatch("send_event_main_message", user, theme)
@bot.event
async def on_send_event_main_message(channelID):
    channel = bot.get_channel(channelID)
    themeUser = await bot.fetch_user(storybois.themeUser)

    if channelID == tokens.PROMPT_ROOM_ID:
        bot.dispatch("generating_prompt_message_references", tokens.PROMPT_ROOM_ID)

    embed=discord.Embed(title=f"**Event created!**", description=f"Theme >> **{storybois.theme}** {themeUser.mention}", color=discord.Color.blue())
    embed.set_thumbnail(url=themeUser.avatar_url)
    # embed.set_footer(text=f"Event created by: {ctx.author.name}")
    embed.set_footer(text=f"Voting starts in: {storybois.timePrompt} day")
    msg = await channel.send(embed=embed)
    storybois.promptThemeMessageReference.append(msg)
    storybois.promptThemeMessageReferenceID.append(msg.id)


@bot.event
async def on_refresh_event_main_message():
    themeUser = await bot.fetch_user(storybois.themeUser)
    if (storybois.currentState == "prompt"):
        embed=discord.Embed(title=f"**Event created!**", description=f"Theme >> **{storybois.theme}** {themeUser.mention}", color=discord.Color.blue())
        embed.set_footer(text=f"Voting starts in: {storybois.timePrompt} day")

    elif storybois.currentState == "voting":
        embed=discord.Embed(title=f"**Event created!**", description=f"Theme >> **{storybois.theme}** {themeUser.mention}", color=discord.Color.dark_blue())
        embed.set_footer(text=f"Voting ends in: {storybois.timeVote} day")
    
    elif storybois.currentState == "story":
        embed=discord.Embed(title=f"**Event created!**", description=f"Theme >> **{storybois.theme}** {themeUser.mention}\nPrompt >> **{storybois.winningPrompt}**", color=discord.Color.green())
        embed.set_footer(text=f"Time remaining to send stories: {storybois.timeStory} day")
    
    else:
        embed=discord.Embed(title=f"**Event created!**", description=f"Theme >> **{storybois.theme}** {themeUser.mention}\nPrompt >> **{storybois.winningPrompt}**", color=discord.Color.red())
        embed.set_footer(text=f"Event ended!")
    
    embed.set_thumbnail(url=themeUser.avatar_url)
    for message in storybois.promptThemeMessageReference:
        await message.edit(embed=embed)

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

    for i in range(4):
        message = await channel.send(".")
        storybois.promptMessagesReference.append(message)
        storybois.promptMessagesReferenceID.append(message.id)
    
    storybois.save_data()


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

    # Need this, because for some unknown reason it updates the OLD messages. Fixes bug with .event delete
    storybois.promptThemeMessageReference = []
    storybois.promptMessagesReference = []
    storybois.winnerMessageReference = []
    
    storybois.themeUser = user.id

    update_time.start() # Start timer

@bot.event
async def on_send_vote_message(channelID):
    channel = bot.get_channel(channelID)

    embed=discord.Embed(title="Voting started!", description=f"Vote for prompts you like!\nTime left: **{storybois.timeVote} day**", color=discord.Color.green())
    msg = await channel.send(embed=embed)
    storybois.votingMessageReference = msg
    storybois.votingMessageReferenceID = msg.id
    storybois.save_data()

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

    storybois.save_data()
    bot.dispatch("winner_selected", channelID) # Also generater story message
    bot.dispatch("refresh_event_main_message") # Need to update main event message with prompt


@bot.event
async def on_create_story_message(channelID):
    channel = bot.get_channel(channelID)

    prompt_and_time_left = f"Prompt: **{storybois.winningPrompt}**\nTime left: **{storybois.timeStory} day**\n\n"
    embed=discord.Embed(title=f"Theme: **{storybois.theme}**", description=prompt_and_time_left, color=discord.colour.Color.dark_green())
    msg = await channel.send(embed=embed)
    storybois.storyMessageReference = msg
    storybois.storyMessageReferenceID = msg.id
    storybois.save_data()

@bot.event
async def on_refresh_story_message():
    global storybois

    # This also deletes the storybois class
    if(storybois.currentState == "end"):
        prompt_and_time_left = f"Prompt: **{storybois.winningPrompt}**\n\n\n"
        people = storybois.generate_story_message()
        description = prompt_and_time_left + people

        embed=discord.Embed(title=f"Theme: **{storybois.theme}**", description=description, color=discord.colour.Color.dark_red())
        await storybois.storyMessageReference.edit(embed=embed)
        storybois = None

    else:
        prompt_and_time_left = f"Prompt: **{storybois.winningPrompt}**\nTime left: **{storybois.timeStory} day**\n\n\n"
        people = storybois.generate_story_message()
        description = prompt_and_time_left + people

        embed=discord.Embed(title=f"Theme: **{storybois.theme}**", description=description, color=discord.colour.Color.dark_green())
        await storybois.storyMessageReference.edit(embed=embed)


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
            bot.dispatch("send_vote_message", tokens.PROMPT_ROOM_ID)
            bot.dispatch("disable_message", tokens.PROMPT_ROOM_ID)
        else:
            bot.dispatch("refresh_vote_message")

    elif state == "story":
        bot.dispatch("refresh_event_main_message")

        if storybois.storyMessageReference == None:
            bot.dispatch("count_votes", tokens.PROMPT_ROOM_ID) # Generates winning prompt message, that generates story message
            bot.dispatch("vote_end_message_change")
            bot.dispatch("enable_message", tokens.STORY_ROOM_ID)
        else:
            bot.dispatch("refresh_story_message")


    elif state == "end":
        bot.dispatch("refresh_event_main_message")

        update_time.stop() # Stop updating the timer
        bot.dispatch("disable_message", tokens.STORY_ROOM_ID)
        bot.dispatch("refresh_story_message") # For making story message red colored also deletes storybois class


# Discord SLASH command plugin
# https://discord-py-slash-command.readthedocs.io/en/latest/quickstart.html
keep_alive()
bot.run(os.environ['TOKEN'])