from number_to_emoji import number_to_emoji
import random
from replit import db


class StoryBoisEvent:
    states = ("prompt", "voting", "story", "end")

    def __init__(self, timePrompt=1, timeVote=1, timeStory=7, theme=""):
        self.timePrompt = timePrompt
        self.timeVote = timeVote
        self.timeStory = timeStory

        self.prompts = []
        self.currentState = self.states[0]

        # Need to separate the theme announcement from the user submitted prompts. Messages have a 2000 character limit.
        # These variables that hold message Reference links
        self.promptThemeMessageReference = []
        self.promptMessagesReference = []
        self.winnerMessageReference = []

        self.storyMessageReference = None
        self.votingMessageReference = None

        self.theme = theme
        self.themeUser = ""
        self.winningPrompt = ""
        self.winningPromptUser = ""

        self.user_to_story_link = {}
        
        self.promptThemeMessageReferenceID = []
        self.promptMessagesReferenceID = []

        self.winnerMessageReferenceID = None
        self.storyMessageReferenceID = None
        self.votingMessageReferenceID = None
    

    def __del__(self):
        print("Class destroyed")
        self.reset_data()


    # Need to update the current state every day at 00:00. We need this to lock channels, start voting, and start story submissions.
    def update_time(self):
            if self.currentState == "prompt":
                self.timePrompt -= 1
                if self.timePrompt <= 0:
                    self.currentState = self.states[1]

            elif self.currentState == "voting":
                self.timeVote -= 1
                if self.timeVote <= 0:
                    self.currentState = self.states[2]

            elif self.currentState == "story":
                self.timeStory -= 1
                if self.timeStory <= 0:
                    self.currentState = self.states[3]
                    #Delete Itself from Database

            self.save_data()
            return self.currentState

    def save_data(self):
        print("--Data Saved--")
        db["timePrompt"] = self.timePrompt
        db["timeVote"] = self.timeVote
        db["timeStory"] = self.timeStory
        db["prompts"] = self.prompts
        db["currentState"] = self.currentState
        db["promptThemeMessageReferenceID"] = self.promptThemeMessageReferenceID
        db["promptMessagesReferenceID"] = self.promptMessagesReferenceID
        db["winnerMessageReferenceID"] = self.winnerMessageReferenceID
        db["storyMessageReferenceID"] = self.storyMessageReferenceID
        db["votingMessageReferenceID"] = self.votingMessageReferenceID
        db["theme"] = self.theme
        db["themeUser"] = self.themeUser
        db["winningPrompt"] = self.winningPrompt
        db["winningPromptUser"] = self.winningPromptUser
        db["user_to_story_link"] = self.user_to_story_link


    def load_data(self):
            self.timePrompt = db["timePrompt"]
            self.timeVote = db["timeVote"]
            self.timeStory = db["timeStory"]
            self.prompts = db["prompts"]
            self.currentState = db["currentState"]
            self.promptThemeMessageReferenceID = db["promptThemeMessageReferenceID"]
            self.promptMessagesReferenceID = db["promptMessagesReferenceID"]
            self.winnerMessageReferenceID = db["winnerMessageReferenceID"]
            self.storyMessageReferenceID = db["storyMessageReferenceID"]
            self.votingMessageReferenceID = db["votingMessageReferenceID"]
            self.theme = db["theme"]
            self.themeUser = db["themeUser"]
            self.winningPrompt = db["winningPrompt"]
            self.winningPromptUser = db["winningPromptUser"]
            self.user_to_story_link = db["user_to_story_link"]
    

    def reset_data(self):
        del db["timePrompt"]
        del db["timeVote"]
        del db["timeStory"]
        del db["prompts"]
        del db["currentState"]
        del db["promptThemeMessageReferenceID"]
        del db["promptMessagesReferenceID"]
        del db["winnerMessageReferenceID"]
        del db["storyMessageReferenceID"]
        del db["votingMessageReferenceID"]
        del db["theme"]
        del db["themeUser"]
        del db["winningPrompt"]
        del db["winningPromptUser"]
        del db["user_to_story_link"]
        del db["current_day"] # Need to delete this value to not cause an issue in the future
        db["event"] = False

    # ------------------------
    # | Prompt state Methods |
    # ------------------------
    def add_prompt(self, prompt, userid):
        if(self.currentState == "prompt"):
            self.prompts.append(f"{prompt} | <@{userid}>")
            self.save_data()


    def edit_prompt(self, newPrompt, userid, index):
        if(self.currentState == "prompt"):
            if self.compare_userid_to_prompt(self.prompts[index], userid):
                self.prompts[index] = f"{newPrompt} | <@{userid}>"
                self.save_data()
    

    def delete_prompt(self, userid, index):
        if(self.currentState == "prompt"):
            if self.compare_userid_to_prompt(self.prompts[index], userid):
                del self.prompts[index]
                self.save_data()

    # Remake this method to work for separated messages
    # Possible solution: Save the last ID a message containts, Set up 3 different messages.
    # Separate THEME message from prompt message
    def generate_prompt_main_message(self, theme="TestTheme", userId="1234"):
        if self.currentState == "prompt":
            message = \
            "------------------------------------------------\n" \
            f"Theme: **{theme}** by <@{userId}>\n" \
            "------------------------------------------------\n" \
            f"Voting starts in: **{self.timePrompt} day**\n"

        elif self.currentState == "voting":
            message = \
            "------------------------------------------------\n" \
            f"Theme: **{theme}** by <@{userId}>\n" \
            "------------------------------------------------\n" \
            "**VOTE FOR YOUR FAVOURITES!**\n" \
            f"Voting ends in: **{self.timeVote} day**\n"

        elif self.currentState == "story":
            message = \
            "------------------------------------------------\n" \
            f"Theme: **{theme}** by <@{userId}>\n" \
            "------------------------------------------------\n" \
            f"**VOTING HAS ENDED!**\n"

        return message

    # Return a list that containts a split message based on the discord character limit that is 2000
    # Obvious bug: Only works for 8000 characters
    # Wont work on prompts longer than ~1990 characters
    # But who will be the madlad that writes 2000 characters for a single prompt entry?
    def generate_prompt_messages(self):
        messages = [".", ".", ".", "."] #  Need to create it this way to make sure discord bot will replace the extension text's with a '.' when not needed
        message_id = 0
        prompt_id = 0

        for prompt in self.prompts:
            if len(messages[message_id] + f"\n{number_to_emoji[prompt_id]} {prompt}\n") <= 2000:
                if(messages[message_id] == "."):
                    messages[message_id] = ""
                messages[message_id] += f"\n{number_to_emoji[prompt_id]} {prompt}\n"

            else:
                message_id += 1
                if(messages[message_id] == "."): 
                    messages[message_id] = ""
                messages[message_id] += f"\n{number_to_emoji[prompt_id]} {prompt}\n"

            prompt_id += 1
      
        return messages


    def compare_userid_to_prompt(self, prompt, userid):
        if userid in prompt:
            return True
        else:
            return False



    # ------------------------
    # | Voting state Methods |
    # ------------------------
    def add_voting_emojis(self):
        pass



    # -----------------------
    # | Story state Methods |
    # -----------------------
    # Voting will be done with custom emoji. Number 1-20
    def select_winner(self, indexes):
        if(self.currentState == "story"):
            self.winningPrompt = self.prompts[random.choice(indexes)]
            self.winningPromptUser = int(self.winningPrompt[self.winningPrompt.rfind('|')+4:-1])
            # self.winningPromptUser = self.promptSenders[self.winningPromptUser]


    def generate_story_message(self):
        message = ""

        for user, story_link in self.user_to_story_link.items():
            message += f"{user} {story_link}\n\n"

        return message
