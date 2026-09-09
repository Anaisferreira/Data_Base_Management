# Community Management System
*The Resilience Project*

---

## Team Members

* **Laura Brule**
* **Anaïs Ferreira**
* **Mithia Ratsimbarison**
* **Thalia Ghali**

---

## Project Description

The *Resilience Project – Community Management System* is a desktop application developed as part of a database systems course. Its objective is to design and implement a collaborative platform that connects individuals and communities within a network of mutual assistance, skill sharing, and democratic governance.

The project goes beyond simple database design and covers the entire development process, from UML modeling and logical data modeling to the implementation of a fully functional Python application with a graphical user interface. The system relies on a PostgreSQL database to ensure structured, consistent, and persistent data storage.

The project was carried out **entirely as a team of four**, with collective decision-making throughout all phases of design and implementation.

---

## Core Architecture and Data Flow

The application is implemented in **Python** and is structured around a clear separation between the user interface, the application logic, and the database layer.

The core logic of the system is centralized in `main.py`, which acts as an intermediary between the graphical interfaces and the PostgreSQL database. This file is responsible for:

* enforcing business rules,
* handling searches and filters,
* managing all CRUD (Create, Read, Update, Delete) operations.

Users interact with the system through two graphical interfaces:

* a **full-featured administrative interface** (`gui.py`),
* a **user-specific portal** (`user_gui.py`).

The underlying data model is built around a generic `Entity` table, from which **Individuals** and **Communities** inherit their identity. This design choice allows shared functionalities (such as messaging or currency accounts) to be handled uniformly, while preserving entity-specific attributes.

---

## Database Design and Modeling

The database was designed using a structured logical data model. The central `Entity` table groups attributes common to both individuals and communities, simplifying the management of relationships and shared features.

The model includes relations for:

* memberships and collaborations,
* individual connections,
* skills and services,
* messaging,
* exclusion votes,
* geolocation data.

Several SQL views were created to answer specific functional needs, particularly for proximity-based queries and community-related displays. The schema was designed to remain readable and scalable, avoiding unnecessary complexity when logic could be handled more effectively in Python.

---

## Constraint Management and Technical Choices

A key design decision was to **manage most business constraints directly in Python**, rather than enforcing them exclusively through SQL constraints. This approach allows the system’s rules to remain centralized, easier to understand, and more flexible.

For example:

* exclusion vote logic is computed dynamically in Python,
* users can only vote against members of communities they belong to,
* messaging rules are validated before message creation.

Regarding geolocation, although the initial project specification mentioned a fixed distance of 1 km, we implemented a **configurable distance parameter**. Users can choose the radius used to search for nearby individuals or communities, making the system more adaptable to different contexts.

---

## Graphical Interface and Styling

The graphical user interface was developed in **Python using Tkinter**, with additional use of **ttk (Themed Tkinter)** widgets to structure the application through tabs, tables, and frames.

The visual design relies on **simple and classic color choices**, manually defined at the widget level. This approach was deliberately chosen to prioritize clarity, readability, and usability over advanced graphical customization. No external graphical libraries were used, ensuring simplicity, stability, and ease of maintenance.

---

## Key Functional Pillars

### Relationship Management

The system manages:

* **individual connections** (unidirectional links with a description),
* **community collaborations**,
* **membership status** of individuals within communities.

### Skills and Services

Users can declare **skills** with a proficiency level ranging from 1 to 5. Based on these skills, they can propose **services**, which fall into three categories:

* `FREE`,
* `EXCHANGE` (in exchange for another service),
* `COMMERCIAL_G1` (paid using the Ğ1 cryptocurrency).

Both individuals and communities can own **Ğ1 accounts** to support commercial interactions.

### Exclusion Mechanism (Social Governance Rule)

A central social rule of the system is the exclusion mechanism. Members of a community can cast an **exclusion vote** against another member. If more than 50% of the active members vote against a person, their membership status is automatically updated (`isExcluded = TRUE`). This rule is fully managed by the application logic.

### Communication and Proximity

* **Messaging**: Entities can exchange messages. Messages are owned by their sender and can reference another message (`InReplyTo_id`), enabling structured discussion threads.
* **Geolocation**: Individuals can provide geographic coordinates. A dedicated SQL view computes distances between individuals, allowing users to search for nearby entities within a chosen radius. Results include OpenStreetMap links for visualization.

---

## Difficulties Encountered

Several challenges were encountered during development. Implementing the exclusion mechanism required careful handling of dynamic community sizes and majority calculations. The messaging system also posed challenges, particularly enforcing reply constraints without blocking valid interactions.

Designing a graphical interface capable of displaying heterogeneous data dynamically required multiple iterations to maintain both usability and stability.

---

## Deliverables  

| Deliverable | Link |
|------------|------|
| Assignment 1 — Clarification Note + First Version of DCM | [Assignement1](./Assignement1) |
| Assignment 2 — Corrected DCM + Logical Data Model |  [Assignement2](./Assignement2) |
| Assignment 3 — SQL Implementation |  [Assignement3](./Assignement3)|
| Assignment 4 — Python Application |  [Assignement4](./Assignement4)|
| Assignment 5 — Oral presentation | [Assignment 5](./Assignment 5) |

---
## Conclusion

This project allowed us to design and implement a complete community management system, combining database modeling, backend logic, and graphical interface development. Teamwork played a central role in the success of the project, and the resulting application fulfills the functional requirements while remaining extensible for future improvements.

---