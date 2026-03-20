from datetime import datetime


def get_current_datetime() -> str:
    time_now = datetime.now().astimezone()
    return f"Current date and time: {time_now.strftime('%Y-%m-%d %H:%M:%S %z')}"
