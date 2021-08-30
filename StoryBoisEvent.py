from number_to_emoji import number_to_emoji
import random
import pickle
import os

class StoryBoisEvent:
    eventsRunning = 0
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

        self.eventsRunning += 1
        

        self.promptThemeMessageReferenceID = []
        self.promptMessagesReferenceID = []

        self.winnerMessageReferenceID = None
        self.storyMessageReferenceID = None
        self.votingMessageReferenceID = None

        self.loaded = False
    

    def __del__(self):
        print("Class destroyed")
        self.eventsRunning -= 1

        if os.path.isfile("storybois.data"):
            os.remove("storybois.data")


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
        self.database = {
            "timePrompt": self.timePrompt,
            "timeVote": self.timeVote,
            "timeStory": self.timeStory,
            "prompts": self.prompts,
            "currentState": self.currentState,
            "promptThemeMessageReferenceID": self.promptThemeMessageReferenceID,
            "promptMessagesReferenceID": self.promptMessagesReferenceID,
            "winnerMessageReferenceID": self.winnerMessageReferenceID,
            "storyMessageReferenceID": self.storyMessageReferenceID,
            "votingMessageReferenceID": self.votingMessageReferenceID,
            "theme": self.theme,
            "themeUser": self.themeUser,
            "winningPrompt": self.winningPrompt,
            "winningPromptUser": self.winningPromptUser,
            "user_to_story_link": self.user_to_story_link,
        }

        with open("storybois.data", "wb") as file:
            pickle.dump(self.database, file)


    def load_data(self):
        if os.path.isfile("storybois.data"):
            with open("storybois.data", "rb") as file:
                print("Storybois event data found and loaded")
                self.database = pickle.load(file)
                self.loaded = True

            self.timePrompt = self.database["timePrompt"]
            self.timeVote = self.database["timeVote"]
            self.timeStory = self.database["timeStory"]
            self.prompts = self.database["prompts"]
            self.currentState = self.database["currentState"]
            self.promptThemeMessageReferenceID = self.database["promptThemeMessageReferenceID"]
            self.promptMessagesReferenceID = self.database["promptMessagesReferenceID"]
            self.winnerMessageReferenceID = self.database["winnerMessageReferenceID"]
            self.storyMessageReferenceID = self.database["storyMessageReferenceID"]
            self.votingMessageReferenceID = self.database["votingMessageReferenceID"]
            self.theme = self.database["theme"]
            self.themeUser = self.database["themeUser"]
            self.winningPrompt = self.database["winningPrompt"]
            self.winningPromptUser = self.database["winningPromptUser"]
            self.user_to_story_link = self.database["user_to_story_link"]
            
        else:
            print("Couldn't load event data from file!")


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