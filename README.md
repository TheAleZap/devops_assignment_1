# Trip-algo (nombre pendiente..)

Planning trips with friends, without the group chat chaos. 

## What's the problem?
Group trips usually die at the first question: when can everyone actually go? Availability gets scattered across group chats, decisions never get closed, and nobody knows who is in charge of booking what. "Who books the flights?" "Where are we stayig?" 

## What does this project do?
The app is split into two independent feature domains:

### 1. Scheduling, the decision making component.
- Each member marks the days they're available.
- The app finds the best date windows for a trip of x days, ranked by how many people can attend (For example, "Oct 10–13 works for 5 of 6").
- Simple polls with deadlines for other decisions (destination, activities).

### 2. Trips, the actual organizing.
- The trip itself: members, final dates, destination.
- A day-by-day itinerary.
- A task board where members claim responsibilities
  ("book accommodation", "rent car", "Lucas drives").

### How they connect
Scheduling knows nothing about trips. It receives a list of participants and a trip length, and returns candidate date windows. Trips asks for these and stores the dates the group chooses. Each domain has its own code and its own database tables, so they could later become separate services.

## Not in the project
- User accounts, login or authentication
- Payments or expense splitting (triicount style)
- Chat, maps, or booking integrations

## Setup
TK

## Running tests
TK