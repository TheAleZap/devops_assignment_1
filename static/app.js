const state = { poll: null, selected: new Set(), trip: null };

const $ = (id) => document.getElementById(id);

// ---------- API ----------

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok) {
    const detail = Array.isArray(data.detail) ? data.detail[0].msg : data.detail;
    throw new Error(detail || "Something went wrong");
  }
  return data;
}

function showMessage(text, isError = false) {
  $("message").textContent = text;
  $("message").classList.toggle("error", isError);
}

// ---------- Date helpers (UTC, so days never shift with the timezone) ----------

function addDays(isoDate, days) {
  const date = new Date(isoDate + "T00:00:00Z");
  date.setUTCDate(date.getUTCDate() + days);
  return date.toISOString().slice(0, 10);
}

function daysBetween(startIso, endIso) {
  const days = [];
  for (let day = startIso; day <= endIso; day = addDays(day, 1)) {
    days.push(day);
  }
  return days;
}

function weekdayIndex(isoDate) {
  // 0 = Monday ... 6 = Sunday
  return (new Date(isoDate + "T00:00:00Z").getUTCDay() + 6) % 7;
}

function formatDate(isoDate) {
  return new Date(isoDate + "T00:00:00Z").toLocaleDateString("en", {
    day: "numeric",
    month: "short",
    timeZone: "UTC",
  });
}

// ---------- Tabs ----------

function showTab(name) {
  const scheduling = name === "scheduling";
  $("panel-scheduling").classList.toggle("hidden", !scheduling);
  $("panel-trips").classList.toggle("hidden", scheduling);
  $("tab-scheduling").classList.toggle("active", scheduling);
  $("tab-trips").classList.toggle("active", !scheduling);
}

// ---------- Scheduling rendering ----------

function countFreePerDay() {
  const counts = {};
  for (const days of Object.values(state.poll.availability)) {
    for (const day of days) {
      counts[day] = (counts[day] || 0) + 1;
    }
  }
  return counts;
}

function renderCalendar() {
  const calendar = $("calendar");
  calendar.innerHTML = "";

  for (const name of ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]) {
    const header = document.createElement("div");
    header.className = "weekday";
    header.textContent = name;
    calendar.appendChild(header);
  }

  const days = daysBetween(state.poll.range_start, state.poll.range_end);
  for (let i = 0; i < weekdayIndex(days[0]); i++) {
    calendar.appendChild(document.createElement("div"));
  }

  const counts = countFreePerDay();
  for (const day of days) {
    const cell = document.createElement("button");
    cell.className = "day";
    if (state.selected.has(day)) {
      cell.classList.add("selected");
    }

    const label = document.createElement("span");
    label.className = "day-number";
    const dayNumber = Number(day.slice(8));
    label.textContent = dayNumber === 1 || day === days[0] ? formatDate(day) : dayNumber;

    const count = document.createElement("span");
    count.className = "day-count";
    count.textContent = counts[day] ? `${counts[day]} free` : "";

    cell.append(label, count);
    cell.addEventListener("click", () => toggleDay(day));
    calendar.appendChild(cell);
  }
}

function renderWindows(windows) {
  const list = $("windows");
  list.innerHTML = "";
  const total = Object.keys(state.poll.availability).length;

  if (windows.length === 0) {
    const empty = document.createElement("li");
    empty.textContent = "No availability yet. Be the first to add your days!";
    list.appendChild(empty);
    return;
  }

  for (const window of windows) {
    const item = document.createElement("li");
    const title = document.createElement("strong");
    title.textContent = `${formatDate(window.start)} – ${formatDate(window.end)}: ${window.available.length} of ${total} can go`;
    item.appendChild(title);

    if (window.missing.length > 0) {
      const missing = document.createElement("div");
      missing.className = "muted";
      missing.textContent = `Missing: ${window.missing.join(", ")}`;
      item.appendChild(missing);
    }
    list.appendChild(item);
  }
}

// ---------- Trips rendering ----------

function renderTrip() {
  const trip = state.trip;
  $("trip-section").classList.remove("hidden");
  $("trip-heading").textContent = trip.name;
  const destination = trip.destination ? ` · ${trip.destination}` : "";
  const dates =
    trip.start_date && trip.end_date
      ? ` · ${formatDate(trip.start_date)} – ${formatDate(trip.end_date)}`
      : " · dates not confirmed";
  $("trip-meta").textContent = `Trip #${trip.id}${destination}${dates}`;
  $("trip-progress").textContent =
    `Tasks: ${trip.progress.done}/${trip.progress.total} done` +
    ` · ${trip.progress.claimed} claimed`;

  const membersList = $("trip-members-list");
  membersList.innerHTML = "";
  for (const member of trip.members) {
    const item = document.createElement("li");
    item.textContent = member.name;
    membersList.appendChild(item);
  }

  const tasksList = $("trip-tasks-list");
  tasksList.innerHTML = "";
  if (trip.tasks.length === 0) {
    const empty = document.createElement("li");
    empty.className = "muted";
    empty.textContent = "No tasks yet.";
    tasksList.appendChild(empty);
    return;
  }

  for (const task of trip.tasks) {
    const item = document.createElement("li");
    item.className = "task-row";

    const label = document.createElement("span");
    const status = task.done
      ? "done"
      : task.claimed_by
        ? `claimed by ${task.claimed_by}`
        : "unclaimed";
    label.textContent = `${task.title} (${status})`;
    item.appendChild(label);

    if (!task.done) {
      if (!task.claimed_by) {
        const claimInput = document.createElement("input");
        claimInput.type = "text";
        claimInput.placeholder = "Your name";
        claimInput.className = "claim-input";
        const claimButton = document.createElement("button");
        claimButton.type = "button";
        claimButton.className = "secondary";
        claimButton.textContent = "Claim";
        claimButton.addEventListener(
          "click",
          handle(() => claimTask(task.id, claimInput.value)),
        );
        item.append(claimInput, claimButton);
      } else {
        const doneButton = document.createElement("button");
        doneButton.type = "button";
        doneButton.className = "secondary";
        doneButton.textContent = "Complete";
        doneButton.addEventListener(
          "click",
          handle(() => completeTask(task.id)),
        );
        item.appendChild(doneButton);
      }
    }

    tasksList.appendChild(item);
  }
}

// ---------- Scheduling actions ----------

function toggleDay(day) {
  if (state.selected.has(day)) {
    state.selected.delete(day);
  } else {
    state.selected.add(day);
  }
  renderCalendar();
}

function loadSelectionForParticipant() {
  const name = $("participant").value.trim();
  state.selected = new Set(state.poll.availability[name] || []);
}

async function refreshWindows() {
  renderWindows(await api(`/api/scheduling/polls/${state.poll.id}/best-windows`));
}

async function loadPoll(pollId) {
  if (!pollId) {
    throw new Error("Enter a poll ID");
  }
  state.poll = await api(`/api/scheduling/polls/${pollId}`);
  history.replaceState(null, "", `?poll=${state.poll.id}`);

  $("poll-title").textContent = state.poll.title;
  $("poll-meta").textContent =
    `Poll #${state.poll.id} · ${formatDate(state.poll.range_start)} – ${formatDate(state.poll.range_end)}` +
    ` · ${state.poll.trip_length}-day trip · share this page's link with your friends`;
  $("poll-section").classList.remove("hidden");
  $("windows-section").classList.remove("hidden");

  loadSelectionForParticipant();
  renderCalendar();
  await refreshWindows();
  showTab("scheduling");
}

async function createPoll() {
  const poll = await api("/api/scheduling/polls", {
    method: "POST",
    body: JSON.stringify({
      title: $("title").value.trim(),
      range_start: $("range-start").value,
      range_end: $("range-end").value,
      trip_length: Number($("trip-length").value),
    }),
  });
  await loadPoll(poll.id);
  showMessage(`Poll created! Share this page's link with your friends.`);
}

async function saveAvailability() {
  const name = $("participant").value.trim();
  if (!name) {
    throw new Error("Type your name first");
  }
  state.poll = await api(`/api/scheduling/polls/${state.poll.id}/availability`, {
    method: "PUT",
    body: JSON.stringify({ participant: name, days: [...state.selected] }),
  });
  renderCalendar();
  await refreshWindows();
  showMessage(`Saved ${state.selected.size} days for ${name}.`);
}

// ---------- Trips actions ----------

async function loadTrip(tripId) {
  if (!tripId) {
    throw new Error("Enter a trip ID");
  }
  state.trip = await api(`/api/trips/${tripId}`);
  history.replaceState(null, "", `?trip=${state.trip.id}`);
  renderTrip();
  showTab("trips");
}

async function createTrip() {
  const members = $("trip-members")
    .value.split(",")
    .map((name) => name.trim())
    .filter(Boolean);
  const trip = await api("/api/trips", {
    method: "POST",
    body: JSON.stringify({
      name: $("trip-name").value.trim(),
      destination: $("trip-destination").value.trim() || null,
      members,
    }),
  });
  state.trip = trip;
  history.replaceState(null, "", `?trip=${trip.id}`);
  renderTrip();
  showTab("trips");
  showMessage(`Trip #${trip.id} created.`);
}

async function addMember() {
  const name = $("new-member").value.trim();
  if (!name) {
    throw new Error("Type a member name");
  }
  state.trip = await api(`/api/trips/${state.trip.id}/members`, {
    method: "POST",
    body: JSON.stringify({ name }),
  });
  $("new-member").value = "";
  renderTrip();
  showMessage(`Added ${name}.`);
}

async function addTask() {
  const title = $("new-task").value.trim();
  if (!title) {
    throw new Error("Type a task title");
  }
  state.trip = await api(`/api/trips/${state.trip.id}/tasks`, {
    method: "POST",
    body: JSON.stringify({ title }),
  });
  $("new-task").value = "";
  renderTrip();
  showMessage(`Added task "${title}".`);
}

async function claimTask(taskId, memberName) {
  if (!memberName.trim()) {
    throw new Error("Type your name to claim");
  }
  state.trip = await api(`/api/trips/${state.trip.id}/tasks/${taskId}/claim`, {
    method: "POST",
    body: JSON.stringify({ member: memberName.trim() }),
  });
  renderTrip();
  showMessage("Task claimed.");
}

async function completeTask(taskId) {
  state.trip = await api(`/api/trips/${state.trip.id}/tasks/${taskId}/complete`, {
    method: "POST",
  });
  renderTrip();
  showMessage("Task marked done.");
}

async function confirmDates() {
  const datePollId = Number($("confirm-poll-id").value);
  const start = $("confirm-start").value;
  if (!datePollId || !start) {
    throw new Error("Enter a poll ID and a window start date");
  }
  state.trip = await api(`/api/trips/${state.trip.id}/dates`, {
    method: "PUT",
    body: JSON.stringify({ date_poll_id: datePollId, start }),
  });
  renderTrip();
  const window = state.trip.confirmed_window;
  showMessage(
    `Dates confirmed: ${window.start} – ${window.end}` +
      ` (${window.available.length} available).`,
  );
}

// ---------- Wiring ----------

function handle(action) {
  return async () => {
    try {
      showMessage("");
      await action();
    } catch (error) {
      showMessage(error.message, true);
    }
  };
}

$("tab-scheduling").addEventListener("click", () => showTab("scheduling"));
$("tab-trips").addEventListener("click", () => showTab("trips"));

$("create-button").addEventListener("click", handle(createPoll));
$("open-button").addEventListener("click", handle(() => loadPoll($("poll-id-input").value)));
$("save-button").addEventListener("click", handle(saveAvailability));
$("participant").addEventListener("change", () => {
  if (state.poll) {
    loadSelectionForParticipant();
    renderCalendar();
  }
});

$("create-trip-button").addEventListener("click", handle(createTrip));
$("open-trip-button").addEventListener("click", handle(() => loadTrip($("trip-id-input").value)));
$("add-member-button").addEventListener("click", handle(addMember));
$("add-task-button").addEventListener("click", handle(addTask));
$("confirm-dates-button").addEventListener("click", handle(confirmDates));

const params = new URLSearchParams(location.search);
const pollFromUrl = params.get("poll");
const tripFromUrl = params.get("trip");
if (tripFromUrl) {
  handle(() => loadTrip(tripFromUrl))();
} else if (pollFromUrl) {
  handle(() => loadPoll(pollFromUrl))();
}
