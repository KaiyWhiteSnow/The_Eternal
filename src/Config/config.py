from datetime import datetime
from termcolor import colored

class DiscordConfig:
    client_token = ""
    
    def getPrefix():
        """
        Retrieves a formatted prefix string containing the current date and time
        along with a custom label for use in console output.

        Returns:
        str: A formatted prefix string.

        Example:
        >>> getPrefix()
        '2024-02-06 15:30:00 The Eternal || '
        """
        now = datetime.now()
        dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
        prefix = str(colored(dt_string, "dark_grey")) + str(colored(" The Eternal || ", "cyan"))
        return prefix