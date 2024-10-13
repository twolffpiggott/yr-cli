import os


def is_iterm2():
    return "ITERM_SESSION_ID" in os.environ


def get_output_method():
    return "iterm2" if is_iterm2() else "rich"
