BLOCKED_WORDS = ["abuse", "hate", "violence"]

def is_safe(message: str):
    message = message.lower()
    for word in BLOCKED_WORDS:
        if word in message:
            return False
    return True
