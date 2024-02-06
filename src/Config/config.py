from datetime import datetime
from termcolor import colored

class DiscordConfig:
    client_token = ""
    
    def getPrefix():
        now = datetime.now()
        dt_string = now.strftime("%d-%m-%Y %H:%M:%S")
        prefix = str(colored(dt_string, "grey")) + str(colored(" The Eternal || ", "cyan"))
        return prefix