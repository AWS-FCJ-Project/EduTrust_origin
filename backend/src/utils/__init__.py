import datetime


def get_current_datetime() -> str:
    time_now = datetime.datetime.now().astimezone()
    return f"Current date and time: {time_now.strftime('%Y-%m-%d %H:%M:%S %z')}"


def utc_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)
