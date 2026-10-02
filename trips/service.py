from trips import repository


class TripsError(ValueError):
    pass


class TripNotFoundError(TripsError):
    pass


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
    return trip


def add_member(trip_id, name):
    trip = get_trip(trip_id)
    member_name = clean_name(name, "member name")
    existing = {member["name"].lower() for member in trip["members"]}
    if member_name.lower() in existing:
        raise TripsError(f"{member_name} is already a member of this trip")
    repository.insert_member(trip_id, member_name)
    return get_trip(trip_id)
