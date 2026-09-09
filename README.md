# Community Management System

**Authors:**
- Anaïs Ferreira
- Laura Brulé
- Thalia Ghalia
- Mithia Ratsimbarison

**Date:** December 2025

---

## Table of Contents

1. [Introduction](#introduction)
2. [Database Architecture](#database-architecture)
3. [Implemented Features](#implemented-features)
4. [Specialized Views](#specialized-views)
5. [Graphical Interfaces](#graphical-interfaces)
6. [Installation and Usage](#installation-and-usage)
7. [Conclusion](#conclusion)

---

## Introduction

This project implements a comprehensive community management system built around a PostgreSQL database. The system manages individuals, communities, skills, services, and their interactions through two distinct graphical interfaces: an administration interface and a user interface with authentication.

### Project Objectives

The project aims to achieve several key objectives:

- Model and implement a complex relational database with integrity constraints
- Create specialized SQL views including recursive queries for message threading
- Develop ergonomic graphical interfaces with Tkinter
- Implement a democratic voting system for member exclusion
- Manage geographical data with proximity calculations
- Ensure data integrity through transactions and validation mechanisms

---

## Database Architecture

### Relational Schema Overview

The system consists of 11 interconnected tables implementing a community management platform. The architecture is built around a central inheritance model that allows both individuals and communities to share common attributes while maintaining their specific characteristics.

#### Core Tables

The Entity table serves as the central inheritance table with the following attributes:
- `id` (INTEGER PRIMARY KEY) - Unique entity identifier
- `displayName` (VARCHAR(255)) - Entity display name
- `createdAt` (DATE) - Creation timestamp
- `entity_near` (INTEGER FK) - Reference to nearby entity

This table forms the foundation for the inheritance pattern used throughout the system.

The Individual table represents an entity specialization:
- `id_individual` (INTEGER PRIMARY KEY, FK to Entity)
- `email` (VARCHAR(255) UNIQUE) - Contact email
- `latitude` (BIGINT) - GPS latitude in microDegrees (×10⁶)
- `longitude` (BIGINT) - GPS longitude in microDegrees (×10⁶)

GPS coordinates are stored as BIGINT values in microDegrees, providing approximately 11cm precision without floating-point rounding errors.

The Community table provides another entity specialization:
- `id_community` (INTEGER PRIMARY KEY, FK to Entity)
- `name` (VARCHAR(255) UNIQUE) - Community name
- `description` (TEXT) - Detailed description

The Membership table establishes the many-to-many relationship between individuals and communities:
- `id` (INTEGER PRIMARY KEY)
- `joinedAt` (DATE) - Join date
- `isExcluded` (BOOLEAN) - Exclusion status
- `id_community` (INTEGER FK)
- `id_individual` (INTEGER FK)
- UNIQUE constraint on (id_community, id_individual)

#### Communication and Skills

The Message table implements a thread-based messaging system:
- `id` (INTEGER PRIMARY KEY)
- `SentAt` (DATE)
- `Subject` (VARCHAR(255))
- `body` (TEXT)
- `sender_id` (INTEGER FK to Entity)
- `recipient_id` (INTEGER FK to Entity)
- `InReplyTo_id` (INTEGER FK to Message) - Enables unlimited threading depth

The self-referential `InReplyTo_id` foreign key enables nested conversations with unlimited depth.

The Skill table maintains a catalog of available skills:
- `id` (INTEGER PRIMARY KEY)
- `label` (VARCHAR(255)) - Skill name
- `description` (TEXT)

The EntitySkill table associates entities with skills while tracking proficiency:
- `id` (INTEGER PRIMARY KEY)
- `level` (INTEGER CHECK (level >= 1 AND level <= 5)) - Proficiency level
- `entity_id` (INTEGER FK)
- `skill_id` (INTEGER FK)

The Service table captures services offered by entities:
- `id` (INTEGER PRIMARY KEY)
- `title` (VARCHAR(255))
- `type` (VARCHAR(50)) - FREE/EXCHANGE/COMMERCIAL_G1
- `description` (TEXT)
- `entity_id` (INTEGER FK)

#### Governance and Connections

The ExclusionVote table implements the democratic exclusion system:
- `id` (INTEGER PRIMARY KEY)
- `votedAt` (DATE)
- `vote` (BOOLEAN) - TRUE for exclusion
- `membership_id` (INTEGER FK)

The Individual_Connexion table manages bilateral relationships:
- `id_individual1` (INTEGER FK, with id1 < id2)
- `id_individual2` (INTEGER FK)

The constraint requiring id1 < id2 prevents duplicate entries and normalizes relationship storage.

The Community_Collaboration table handles inter-community partnerships:
- `id_community1` (INTEGER FK, with id1 < id2)
- `id_community2` (INTEGER FK)

The G1Account table manages cryptocurrency accounts:
- `id` (INTEGER PRIMARY KEY)
- `publicKey` (VARCHAR(255) UNIQUE)
- `entity_id` (INTEGER FK)

### Design Decisions

The single table inheritance pattern was chosen to allow both Individual and Community types to inherit from a common Entity base. This design simplifies queries for common operations such as messaging and skill management while maintaining type-specific attributes in separate specialized tables.

GPS coordinates are stored as BIGINT values in microDegrees rather than floating-point numbers. This eliminates floating-point rounding errors and provides exceptional precision of approximately 11 centimeters per microDegree.

---

## Implemented Features

### Complete CRUD Operations

The system provides comprehensive create, read, update, and delete operations for all major entities.

#### Individual Management

The system offers several functions for managing individuals:

- `add_individual()` performs transactional creation involving insertions into both Entity and Individual tables
- `search_people()` enables case-insensitive searching by name or email address
- `connect_individuals()` manages bilateral connections between individuals
- `view_individual_connections()` displays an individual's complete network

#### Community Management

Community operations include:

- `add_community()` creates new communities with unique name validation
- `search_communities()` performs full-text searches across names and descriptions
- `join_community()` and `leave_community()` handle membership management
- `get_community_members()` retrieves member lists with exclusion status

#### Messaging System

The messaging system provides:

- `send_message()` supports optional reply-to threading for nested conversations
- `view_message()` reconstructs complete discussion threads using recursive CTEs
- `get_recent_messages()` retrieves the latest messages received by an entity

#### Skills and Services

Skills and services are managed through:

- `add_skill()` creates new skills in the catalog
- `add_entity_skill()` associates skills with entities at proficiency levels 1-5
- `search_skills()` and `search_services()` enable multi-criteria searches with usage counts
- `add_service()` creates service offerings with type validation

#### Exclusion Voting

The voting system includes:

- `cast_exclusion_vote()` records votes with automatic membership verification
- `check_and_apply_exclusion()` automatically applies exclusion when votes exceed 50%
- `get_exclusion_votes()` and `get_exclusion_vote_stats()` provide tracking and analytics

### Transaction Management

All write operations utilize explicit transaction management to ensure data integrity:

```python
try:
    cur.execute("INSERT INTO Entity (id, displayName, createdAt) VALUES (%s, %s, %s)",
                (entity_id, name, date))
    cur.execute("INSERT INTO Individual (id_individual, email, latitude, longitude) VALUES (%s, %s, %s, %s)",
                (entity_id, email, lat, lon))
    conn.commit()  # Atomic validation
except Exception as e:
    conn.rollback()  # Complete rollback on error
    raise
```

### How It Works: Key Mechanisms

#### Democratic Exclusion System

When a community member becomes problematic, the system provides a democratic mechanism for their removal. The process works as follows:

1. Any community member casts a vote on a specific membership using `cast_exclusion_vote()`
2. Votes are recorded in the ExclusionVote table with boolean values indicating support for exclusion
3. After each vote, `check_and_apply_exclusion()` automatically triggers a threshold check
4. The system counts total community members (N) and exclusion votes (V)
5. If V > N/2, the membership's `isExcluded` flag is set to TRUE

The algorithm implementation:

```
1. Count total members in the community
2. Count votes for exclusion for this specific membership
3. Calculate threshold: members / 2
4. If votes_for_exclusion > threshold:
     Set isExcluded = TRUE
     Return TRUE (exclusion applied)
5. Else:
     Return FALSE (not enough votes)
```

For example, in a community of 10 members, if 6 members vote to exclude someone, they are automatically excluded (6 > 5). Excluded members remain in the database but are marked as excluded in all community queries.

#### Message Threading System

The messaging system implements unlimited reply depth through a recursive database structure. The process involves:

1. Root messages have `InReplyTo_id` set to NULL
2. Reply messages have `InReplyTo_id` pointing to their parent message
3. This creates a tree structure of conversations

Thread reconstruction uses a recursive CTE:

```sql
WITH RECURSIVE message_thread AS (
    -- Anchor: root messages
    SELECT m.id, m.SentAt, m.Subject, m.body, m.sender_id, m.recipient_id,
           e1.displayName as sender_name, e2.displayName as recipient_name,
           0 as depth, ARRAY[m.id] as thread_path
    FROM Message m
    JOIN Entity e1 ON m.sender_id = e1.id
    JOIN Entity e2 ON m.recipient_id = e2.id
    WHERE (m.sender_id = %s OR m.recipient_id = %s) AND m.InReplyTo_id IS NULL

    UNION ALL

    -- Recursion: replies
    SELECT m.id, m.SentAt, m.Subject, m.body, m.sender_id, m.recipient_id,
           e1.displayName, e2.displayName,
           mt.depth + 1, mt.thread_path || m.id
    FROM Message m
    JOIN Entity e1 ON m.sender_id = e1.id
    JOIN Entity e2 ON m.recipient_id = e2.id
    JOIN message_thread mt ON m.InReplyTo_id = mt.id
    WHERE (m.sender_id = %s OR m.recipient_id = %s)
)
SELECT * FROM message_thread ORDER BY thread_path, SentAt
```

The query walks the message tree intelligently, starting with root messages (depth 0) and recursively finding replies while maintaining the thread_path array. Results display naturally with proper nesting.

Example thread structure:
```
Message 1 (root)
  -> Message 3 (reply to 1)
    -> Message 7 (reply to 3)
  -> Message 5 (reply to 1)
```

#### GPS Proximity Calculation

Finding nearby individuals operates through a two-phase process:

**Phase 1: View Pre-calculation**

The vProximity view pre-calculates distances between all pairs of individuals using a CROSS JOIN:

```sql
CREATE VIEW vProximity AS
SELECT i1.id_individual as reference_individual_id,
       i2.id_individual as nearby_individual_id,
       e2.displayName as nearby_name, i2.email as nearby_email,
       SQRT(
           POWER((CAST(i2.latitude - i1.latitude AS FLOAT) / 1000000.0) * 111.0, 2) +
           POWER((CAST(i2.longitude - i1.longitude AS FLOAT) / 1000000.0) * 111.0
                 * COS(RADIANS(CAST(i1.latitude AS FLOAT) / 1000000.0)), 2)
       ) as distance_km
FROM Individual i1 CROSS JOIN Individual i2
JOIN Entity e2 ON i2.id_individual = e2.id
WHERE i1.id_individual != i2.id_individual
  AND i1.latitude IS NOT NULL AND i1.longitude IS NOT NULL
  AND i2.latitude IS NOT NULL AND i2.longitude IS NOT NULL
```

The distance formula applies a simplified Haversine approximation:
- Converts microDegrees to degrees (÷ 1,000,000)
- Multiplies by 111 km/degree for rough distance
- Applies cosine correction for longitude based on latitude
- Filters out NULL coordinates
- Results in a distance matrix between all individuals

**Phase 2: Query-time Filtering**

The `view_proximity()` function queries the pre-calculated view:

```python
SELECT * FROM vProximity
WHERE reference_individual_id = %s AND distance_km <= %s
ORDER BY distance_km
```

Performance remains excellent: for 100 individuals, the view contains ~10,000 rows but queries return instantly through filtering rather than computing distances on demand.

#### Transaction Atomicity

Entity creation demonstrates atomic multi-table operations. Since Individual and Community inherit from Entity, creating an instance requires inserting into two tables:

**Transaction flow:**
```
BEGIN TRANSACTION
  ├─ Get next entity_id (MAX(id) + 1)
  ├─ INSERT INTO Entity (id, displayName, createdAt, ...)
  ├─ INSERT INTO Individual (id_individual, email, latitude, longitude)
  │
  ├─ If both succeed:
  │    COMMIT (changes become permanent)
  │
  └─ If any fails:
       ROLLBACK (both inserts are undone)
```

Real-world scenario demonstrating the importance:
- User attempts to create account with duplicate email
- Entity insert succeeds
- Individual insert fails (UNIQUE constraint on email)
- Transaction automatically rolls back Entity insert
- Database remains consistent

This pattern applies to all multi-table operations: `add_community()`, `join_community()`, `send_message()`, etc.

---

## Specialized Views

The system implements 3 mandatory views as defined in `tables.sql`.

### vIndividual View

Joins Entity and Individual tables to provide a unified view of individuals:

```sql
CREATE VIEW vIndividual AS
SELECT e.id, e.displayName, e.createdAt, e.entity_near,
       i.email, i.latitude, i.longitude
FROM Entity e
JOIN Individual i ON e.id = i.id_individual;
```

### vCommunity View

Joins Entity and Community tables:

```sql
CREATE VIEW vCommunity AS
SELECT e.id, e.displayName, e.createdAt, e.entity_near,
       c.name, c.description
FROM Entity e
JOIN Community c ON e.id = c.id_community;
```

### vProximity View

Pre-calculates geographic distances between all pairs of individuals using a simplified Haversine formula:

```sql
CREATE VIEW vProximity AS
SELECT
    i1.id_individual as reference_individual_id,
    i2.id_individual as nearby_individual_id,
    e2.displayName as nearby_name,
    i2.email as nearby_email,
    SQRT(
        POWER((CAST(i2.latitude AS FLOAT) / 1000000.0 - CAST(i1.latitude AS FLOAT) / 1000000.0) * 111.0, 2) +
        POWER((CAST(i2.longitude AS FLOAT) / 1000000.0 - CAST(i1.longitude AS FLOAT) / 1000000.0) * 111.0
              * COS(RADIANS(CAST(i1.latitude AS FLOAT) / 1000000.0)), 2)
    ) as distance_km
FROM Individual i1
CROSS JOIN Individual i2
JOIN Entity e2 ON i2.id_individual = e2.id
WHERE i1.id_individual != i2.id_individual;
```

The view provides:
- Distance calculations between all individual pairs
- Simplified Haversine formula with ±50m accuracy
- Coordinates stored in microDegrees (×10⁶)

### Message View (Recursive)

The message view reconstructs complete discussion threads with proper hierarchy. The recursive CTE has two parts:

**Anchor portion** (root messages):
```sql
SELECT m.id, m.SentAt, m.Subject, m.body, m.sender_id, m.recipient_id,
       e1.displayName as sender_name, e2.displayName as recipient_name,
       0 as depth, ARRAY[m.id] as thread_path
FROM Message m
JOIN Entity e1 ON m.sender_id = e1.id
JOIN Entity e2 ON m.recipient_id = e2.id
WHERE (m.sender_id = %s OR m.recipient_id = %s) AND m.InReplyTo_id IS NULL
```

**Recursive portion** (replies):
```sql
SELECT m.id, m.SentAt, m.Subject, m.body, m.sender_id, m.recipient_id,
       e1.displayName, e2.displayName,
       mt.depth + 1, mt.thread_path || m.id
FROM Message m
JOIN Entity e1 ON m.sender_id = e1.id
JOIN Entity e2 ON m.recipient_id = e2.id
JOIN message_thread mt ON m.InReplyTo_id = mt.id
WHERE (m.sender_id = %s OR m.recipient_id = %s)
```

The view provides:
- Unlimited threading depth
- Chronological ordering within threads
- Path tracking for hierarchical display
- Proper nesting of replies under parent messages

---

## Graphical Interfaces

### Administration Interface

The administration interface provides comprehensive management through five tabbed sections:

**Views Tab**
- Query communities for any individual
- Display message threads for any entity
- Show proximity data with distance filtering

**Search Tab**
- Case-insensitive search across people by name/email
- Community search in names and descriptions
- Skill and service searches with usage statistics
- Real-time result filtering

**Create Tab**
- Forms for all entity types
- Individual creation with GPS coordinates
- Community creation with descriptions
- Message composition with reply threading
- Membership management
- Skill and service creation
- Connection establishment between entities

**Connections Tab**
- Visualize individual connection networks
- Display community collaborations
- Network statistics and analysis

**Exclusion Votes Tab**
- Cast votes on memberships
- View voting statistics by community
- Monitor exclusion thresholds
- Track voting history

Interface features:
- Dynamic result display using `ttk.Treeview` widgets
- Automatic column configuration based on query results
- Error handling with automatic rollback
- Real-time result counts

### User Interface

The user interface provides a personalized experience with authentication. Upon launch, users authenticate using their individual identifier.

**Dashboard**
- Personal statistics: communities, connections, skills, services
- Message summary with unread counts
- Recent activity feed

**Communities Tab**
- Current memberships with join dates and exclusion status
- Search all available communities
- Join or leave communities directly
- View member lists for joined communities

**Messages Tab**
- Send new messages or reply to existing threads
- View received messages with sender information
- Display complete conversation threads with proper nesting
- Mark messages as read/unread

**Skills Tab**
- Manage personal skill inventory
- Associate skills with proficiency levels (1-5)
- Update skill levels as expertise develops
- View skills of other community members

**Services Tab**
- Create new service offerings
- Specify service types (FREE/EXCHANGE/COMMERCIAL_G1)
- Search services offered by other members
- Filter by service type and description

**Proximity Tab**
- Find nearby individuals within configurable radius
- Display names, emails, and exact distances
- View locations on coordinate display
- Filter results by maximum distance

**Exclusion Votes Tab**
- Participate in democratic governance
- Vote on member exclusions
- View voting statistics and progress
- Track exclusion decisions

Security is enforced by filtering all queries by the authenticated user's identifier, preventing unauthorized data access.

---

## Installation and Usage

### Prerequisites

The system requires:
- Python 3.8 or higher
- PostgreSQL 12 or higher
- psycopg2-binary library
- **Network access**: Connection to UTC network (on-campus) or UTC VPN

### Setup

**Install dependencies:**
```bash
pip install psycopg2-binary
```

**Configure database connection** in `db_connection.py`:
```python
HOST = "tuxa.sme.utc"
USER = "your_username"
PASSWORD = "your_password"
DATABASE = "your_database"
```

> **Note**: Database credentials are provided separately and should not be committed to version control.

**Create proximity view:**
```bash
python create_view.py
```

**Optional - Generate test data:**
```bash
python populate_database.py
```

### Running the Application

**Administrator interface:**
```bash
python gui.py
```

**User interface (requires login):**
```bash
python user_gui.py
```

### Utility Scripts

**populate_database.py** generates comprehensive test data:
- 30 entities (15 individuals, 10 communities)
- 25 messages with threading relationships
- 30 community memberships
- 40 skill associations with proficiency levels
- 15 service offerings of different types
- 20 individual connections forming a social network
- 10 exclusion votes for testing governance

Generated individuals are centered around Compiegne with ±11km dispersion for realistic proximity testing.

**clear_database.py** safely deletes all data:
- Prompts for confirmation (type "yes" to proceed)
- Deletes records in reverse FK dependency order
- Prevents accidental data loss
- Respects referential integrity

**create_view.py** creates or recreates the vProximity view:
- Drops existing view if present
- Creates fresh view with distance calculations
- Can be run multiple times safely

---

## Conclusion

This project successfully demonstrates:

- 11 interconnected tables with inheritance patterns
- Recursive CTEs for message threading
- Proximity calculations with GPS coordinates
- Democratic exclusion voting system
- Dual interface (admin + user) with Tkinter
- Transaction management for data integrity

---

## File Structure

```
Assignment5/
├── README.md                 # This document
├── tables.sql                # SQL schema (tables + views)
├── db_connection.py          # PostgreSQL connection management
├── main.py                   # Business logic (CRUD, views, searches)
├── gui.py                    # Administrator interface
├── user_gui.py               # User interface with authentication
├── populate_database.py      # Test data generation
├── clear_database.py         # Database cleaning utility
└── create_view.py            # vProximity view creation
```

---

**End of Report**
