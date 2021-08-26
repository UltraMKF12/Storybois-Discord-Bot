from discord import message
from StoryBoisEvent import StoryBoisEvent

event = StoryBoisEvent()


event.add_prompt("Elso prompt", "MKF12")
event.add_prompt("Masodik prompt", "MKF12")
event.add_prompt("Harmadik prompt", "MKF12")

messages = event.generate_prompt_messages()
for i in messages:
    print(i)

event.edit_prompt("utolso Prompt", "MKF12", 0)

messages = event.generate_prompt_messages()
for i in messages:
    print(i)

event.delete_prompt("MKF12", 1)

messages = event.generate_prompt_messages()
for i in messages:
    print(i)