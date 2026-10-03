from scheduling import service as scheduling_service
from trips import repository


class TripsError(ValueError):
    pass


class TripNotFoundError(TripsError):
    pass


class TaskNotFoundError(TripsError):
    pass


# ---------- Pure helpers ----------

def clean_name(name, field="name"):
    cleaned = name.strip()
    if not cleaned:
        raise TripsError(f"{field} cannot be empty")
    return cleaned


def unique_names(names):
    seen = set()
    result = []
    for name in names:
        cleaned = clean_name(name, "member name")
        key = cleaned.lower()
        if key not in seen:
            seen.add(key)
            result.append(cleaned)
    return result


def find_member(members, name):
    key = name.strip().lower()
    for member in members:
        if member["name"].lower() == key:
            return member
    return None


def find_task(tasks, task_id):
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise TaskNotFoundError(f"Task {task_id} not found in this trip")


def summarize_tasks(tasks):
    return {
        "total": len(tasks),
        "claimed": sum(1 for task in tasks if task["claimed_by"] is not None),
        "done": sum(1 for task in tasks if task["done"]),
    }


# ---------- Trips and members ----------

def create_trip(name, destination=None, members=()):
    trip_name = clean_name(name, "trip name")
    clean_destination = (destination or "").strip() or None
    trip_id = repository.insert_trip_with_members(
        trip_name, clean_destination, unique_names(members)
    )
    return get_trip(trip_id)


def get_trip(trip_id):
    trip = repository.get_trip(trip_id)
    if trip is None:
        raise TripNotFoundError(f"Trip {trip_id} not found")
    trip["members"] = repository.get_members(trip_id)
    trip["tasks"] = [
        {**task, "done": bool(task["done"])} for task in repository.get_tasks(trip_id)
    ]
    trip["progress"] = summarize_tasks(trip["tasks"])
    return trip


def add_member(trip_id, name):
    trip = get_trip(trip_id)
    member_name = clean_name(name, "member name")
    if find_member(trip["members"], member_name) is not None:
        raise TripsError(f"{member_name} is already a member of this trip")
    repository.insert_member(trip_id, member_name)
    return get_trip(trip_id)


# ---------- Task board ----------

def add_task(trip_id, title):
    get_trip(trip_id)
    repository.insert_task(trip_id, clean_name(title, "task title"))
    return get_trip(trip_id)


def claim_task(trip_id, task_id, member_name):
    trip = get_trip(trip_id)
    task = find_task(trip["tasks"], task_id)
    member = find_member(trip["members"], member_name)
    if member is None:
        raise TripsError(f"{member_name.strip()} is not a member of this trip")
    if task["claimed_by"] is not None and task["claimed_by"] != member["name"]:
        raise TripsError(f"Task already claimed by {task['claimed_by']}")
    repository.set_task_claim(task_id, member["id"])
    return get_trip(trip_id)


def complete_task(trip_id, task_id):
    trip = get_trip(trip_id)
    task = find_task(trip["tasks"], task_id)
    if task["claimed_by"] is None:
        raise TripsError("Claim the task before marking it done")
    repository.set_task_done(task_id)
    return get_trip(trip_id)


# ---------- Dates (the seam with Scheduling) ----------

def confirm_dates(trip_id, date_poll_id, start):
    get_trip(trip_id)
    try:
        window = scheduling_service.describe_window(date_poll_id, start)
    except scheduling_service.SchedulingError as error:
        raise TripsError(str(error))
    repository.set_trip_dates(trip_id, window["start"], window["end"], date_poll_id)
    trip = get_trip(trip_id)
    trip["confirmed_window"] = window
    return trip
