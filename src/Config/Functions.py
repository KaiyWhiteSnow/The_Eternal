class Functions:
    def load_banned_words(file_path):
        with open(file_path, 'r') as file:
            banned_words = [word.strip() for word in file.readlines()]
        return banned_words

    def is_message_banned(message, banned_words):
        # Check message content
        for word in banned_words:
            if word.lower() in message.content.lower():
                return True

        # Check author's name
        for word in banned_words:
            if word.lower() in message.author.name.lower():
                return True

        return False