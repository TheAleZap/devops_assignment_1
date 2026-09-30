# Architecture Decision Records


## 1. Backend framework and architecture
Date: 2026-09-28
Status: Decided
**Context:** The core feature is an interactive availability calendar where friend groups of 4–10 people mark free days and see the best date windows update live. Taking this into account, I decided that a "reload-per-action" form interface would handle this poorly. 
The app must run as a single process, and its two domains will later be split into separate services.

**Decision:** Build a JSON API with Python and FastAPI (using one APIRouter per feature domain), served by uvicorn from a single `python app.py` command, with a plain HTML/CSS/JavaScript frontend served as static files by the same process.
Alternatives considered: Flask with server-rendered Jinja templates was rejected because every calendar interaction would require a full page reload, undermining the main feature. React was rejected because it requires npm and a second dependency manifest, which the single-manifest constraint forbids, plus a build step the app doesn't need. Django was rejected because its ORM, admin panel and authentication solve problems this app doesn't have.

**Consequences:** Because each domain already communicates through its own API endpoints, splitting them into separate services later mostly means moving routers rather than rewriting logic. The cost is maintaining two languages and handling frontend state in JavaScript myself.


## 2. Scoping Scheduling and Trips as independently modularizable domains
Date: 2026-09-30
Status: Decided
Context: This project has two separate responsibilities: getting a group to agree on dates, and organizing the trip once dates are chosen. Assignment 2 will split the app into separate services, so if the two share code or tables, the split would require rewriting both.

Decision: Scheduling is a generic domain that receives participant names and a trip length and returns ranked date windows, with no informatio about trips. Trips owns trips, members, itinerary and tasks. Each domain has its own folder (router, service, repository), its own APIRouter prefix and its own tables, and Trips calls Scheduling only through scheduling/service.py

Alternatives considered: A single trips module with availability stored as part of each trip. Rejected because it would give that module two reasons to change (trip organization and date finding), violating the Single Responsibility Principle, and would make date finding depend on trip tables, so it couldn't be reused for other kinds of group plans or deployed separately without rewriting both the logic and the schema.

Consequences: In Assignment 2, the in-process call from Trips to scheduling.service becomes a single HTTP call, and each domain takes its own tables with it. The cost is some duplicated data: participant names are stored by both domains instead of being shared through a join.


## 3. Cross-domain data references without foreign keys
Date: 2026-09-30
Status: Decided
Context: Both domains must share one SQLite file for now, but Assignment 2 will move them into separate services, each with its own database. Trips needs to know which date poll its dates came from, and availability needs to identify each participant.

Decision: Each domain creates and owns its own tables, using foreign keys only within a domain: across domains, trips.date_poll_id is a plain integer and availability.participant is a text name, with no FOREIGN KEY between them. Availability is stored as one row per participant per free day, with dates "YYYY-MM-DD".

Alternatives considered: Foreign keys from availability to members and from trips to date_polls. Rejected because the database would then enforce links across domains, which breaks as soon as the tables live in separate databases. Storing availability as date ranges was also rejected: overlapping ranges make the date window calculation much harder, while one row per day costs at most about 900 rows per poll at our scale.

Consequences: Each domain can later take its tables with it without schema changes. The cost is that the database no longer guarantees a trip's date_poll_id exists or that a participant name matches a member, so the application must check this, and member names are stored in both domains.