from datetime import date

from scheduling import repository


class SchedulingError(ValueError):
    pass


class PollNotFoundError(SchedulingError):
    pass


def validate_poll(range_start, range_end, trip_length):
    if range_end < range_start:
        raise SchedulingError("range_end must be on or after range_start")
    range_days = (range_end - range_start).days + 1
    if trip_length > range_days:
        raise SchedulingError("trip_length is longer than the date range")


def validate_days(days, range_start, range_end):
    for day in days:
        if day < range_start or day > range_end:
            raise SchedulingError(f"{day} is outside the poll's date range")


def group_by_participant(rows):
    grouped = {}
    for row in rows:
        grouped.setdefault(row["participant"], []).append(row["day"])
    return grouped


def create_poll(title, range_start, range_end, trip_length):
    validate_poll(range_start, range_end, trip_length)
    poll_id = repository.insert_poll(
        title.strip(), range_start.isoformat(), range_end.isoformat(), trip_length
    )
    return get_poll(poll_id)


def get_poll(poll_id):
    poll = repository.get_poll(poll_id)
    if poll is None:
        raise PollNotFoundError(f"Poll {poll_id} not found")
    poll["availability"] = group_by_participant(repository.get_availability(poll_id))
    return poll


def set_availability(poll_id, participant, days):
    poll = get_poll(poll_id)
    validate_days(
        days,
        date.fromisoformat(poll["range_start"]),
        date.fromisoformat(poll["range_end"]),
    )
    unique_days = sorted({day.isoformat() for day in days})
    repository.replace_availability(poll_id, participant.strip(), unique_days)
    return get_poll(poll_id)
