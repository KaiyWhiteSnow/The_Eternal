class Functions:
    def load_banned_phrases(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                banned_phrases = [phrase.strip() for phrase in file.read().split(',')]
            return banned_phrases
        except UnicodeDecodeError as e:
            print(f"Error decoding file {file_path}: {e}")
            return []

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