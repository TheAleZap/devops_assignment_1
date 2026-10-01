from datetime import date

import pytest

from scheduling import service


# --- validate_poll ---

def test_validate_poll_accepts_trip_that_exactly_fits_range():
    service.validate_poll(date(2026, 10, 1), date(2026, 10, 3), 3)


def test_validate_poll_rejects_end_before_start():
    with pytest.raises(service.SchedulingError):
        service.validate_poll(date(2026, 10, 5), date(2026, 10, 1), 2)


def test_validate_poll_rejects_trip_longer_than_range():
    with pytest.raises(service.SchedulingError):
        service.validate_poll(date(2026, 10, 1), date(2026, 10, 3), 4)


# --- validate_days ---

def test_validate_days_accepts_range_boundaries():
    service.validate_days(
        [date(2026, 10, 1), date(2026, 10, 31)], date(2026, 10, 1), date(2026, 10, 31)
    )


def test_validate_days_rejects_day_outside_range():
    with pytest.raises(service.SchedulingError):
        service.validate_days([date(2026, 11, 1)], date(2026, 10, 1), date(2026, 10, 31))


# --- group_by_participant ---

def test_group_by_participant_groups_days_per_person():
    rows = [
        {"participant": "Ana", "day": "2026-10-01"},
        {"participant": "Ana", "day": "2026-10-02"},
        {"participant": "Ben", "day": "2026-10-01"},
    ]
    assert service.group_by_participant(rows) == {
        "Ana": ["2026-10-01", "2026-10-02"],
        "Ben": ["2026-10-01"],
    }


# --- find_best_windows ---

def test_find_best_windows_returns_empty_list_without_availability():
    assert service.find_best_windows(date(2026, 10, 1), date(2026, 10, 31), 3, {}) == []


def test_window_where_everyone_is_free_ranks_first():
    availability = {
        "Ana": ["2026-10-05", "2026-10-06"],
        "Ben": ["2026-10-05", "2026-10-06"],
    }
    result = service.find_best_windows(date(2026, 10, 1), date(2026, 10, 10), 2, availability)
    assert result[0]["start"] == "2026-10-05"
    assert result[0]["available"] == ["Ana", "Ben"]
    assert result[0]["missing"] == []


def test_person_free_on_only_some_days_counts_as_missing():
    availability = {"Ana": ["2026-10-01", "2026-10-02"]}
    result = service.find_best_windows(date(2026, 10, 1), date(2026, 10, 3), 3, availability)
    assert result == [{
        "start": "2026-10-01",
        "end": "2026-10-03",
        "available": [],
        "missing": ["Ana"],
        "missed_days": 1,
    }]


def test_fewer_missed_days_beats_earlier_start_when_attendance_ties():
    availability = {"Ana": ["2026-10-04"]}
    result = service.find_best_windows(date(2026, 10, 1), date(2026, 10, 4), 2, availability)
    assert result[0]["start"] == "2026-10-03"
    assert result[0]["missed_days"] == 1


def test_earliest_start_breaks_a_full_tie():
    availability = {"Ana": ["2026-10-01", "2026-10-02", "2026-10-03", "2026-10-04"]}
    result = service.find_best_windows(date(2026, 10, 1), date(2026, 10, 4), 2, availability)
    assert [w["start"] for w in result] == ["2026-10-01", "2026-10-02", "2026-10-03"]


def test_last_window_does_not_run_past_range_end():
    days = ["2026-10-01", "2026-10-02", "2026-10-03", "2026-10-04", "2026-10-05"]
    result = service.find_best_windows(
        date(2026, 10, 1), date(2026, 10, 5), 3, {"Ana": days}, limit=10
    )
    assert len(result) == 3
    assert max(w["end"] for w in result) == "2026-10-05"


def test_limit_caps_number_of_windows_returned():
    days = [f"2026-10-{d:02d}" for d in range(1, 11)]
    result = service.find_best_windows(
        date(2026, 10, 1), date(2026, 10, 10), 2, {"Ana": days}, limit=2
    )
    assert len(result) == 2


# --- service functions using the database ---

def test_create_poll_starts_with_no_availability(temp_db):
    poll = service.create_poll("Trip", date(2026, 10, 1), date(2026, 10, 31), 3)
    assert poll["title"] == "Trip"
    assert poll["availability"] == {}


def test_get_poll_raises_when_poll_does_not_exist(temp_db):
    with pytest.raises(service.PollNotFoundError):
        service.get_poll(999)


def test_set_availability_replaces_previous_days(temp_db):
    poll = service.create_poll("Trip", date(2026, 10, 1), date(2026, 10, 31), 2)
    service.set_availability(poll["id"], "Ana", [date(2026, 10, 1), date(2026, 10, 2)])
    updated = service.set_availability(poll["id"], "Ana", [date(2026, 10, 5)])
    assert updated["availability"] == {"Ana": ["2026-10-05"]}


def test_set_availability_removes_duplicates_and_sorts_days(temp_db):
    poll = service.create_poll("Trip", date(2026, 10, 1), date(2026, 10, 31), 2)
    updated = service.set_availability(
        poll["id"], "Ana", [date(2026, 10, 3), date(2026, 10, 1), date(2026, 10, 3)]
    )
    assert updated["availability"] == {"Ana": ["2026-10-01", "2026-10-03"]}


def test_get_best_windows_uses_saved_availability(temp_db):
    poll = service.create_poll("Trip", date(2026, 10, 1), date(2026, 10, 5), 2)
    service.set_availability(poll["id"], "Ana", [date(2026, 10, 2), date(2026, 10, 3)])
    result = service.get_best_windows(poll["id"])
    assert result[0]["start"] == "2026-10-02"
    assert result[0]["available"] == ["Ana"]
