-- ============================
-- Table Entity
-- ============================
CREATE TABLE Entity (
    id INT PRIMARY KEY,
    displayName VARCHAR,
    createdAt DATE,
    entity_near INT,
    FOREIGN KEY (entity_near) REFERENCES Entity(id)
);

-- ============================
-- Table Skill
-- ============================
CREATE TABLE Skill (
    id INT PRIMARY KEY,
    label VARCHAR,
    description VARCHAR
);

-- ============================
-- Table Individual
-- ============================
CREATE TABLE Individual (
    id_individual INT PRIMARY KEY,
    email VARCHAR UNIQUE,
    latitude INT,
    longitude INT,
    FOREIGN KEY (id_individual) REFERENCES Entity(id)
);

-- ============================
-- Table Community
-- ============================
CREATE TABLE Community (
    id_community INT PRIMARY KEY,
    name VARCHAR UNIQUE,
    description VARCHAR,
    FOREIGN KEY (id_community) REFERENCES Entity(id)
);

-- ============================
-- Table Service
-- ============================
CREATE TABLE Service (
    id INT PRIMARY KEY,
    title VARCHAR NOT NULL,
    type VARCHAR NOT NULL CHECK (type IN ('FREE','EXCHANGE','COMMERCIAL_G1')),
    description VARCHAR,
    entity_id INT NOT NULL,
    FOREIGN KEY (entity_id) REFERENCES Entity(id)
);

-- ============================
-- Table EntitySkill
-- ============================
CREATE TABLE EntitySkill (
    id INT PRIMARY KEY,
    level INT CHECK (level BETWEEN 1 AND 5),
    entity_id INT NOT NULL,
    skill_id INT NOT NULL,
    FOREIGN KEY (entity_id) REFERENCES Entity(id),
    FOREIGN KEY (skill_id) REFERENCES Skill(id)
);

-- ============================
-- Community Collaboration
-- ============================
CREATE TABLE Community_Collaboration (
    id_community1 INT,
    id_community2 INT,
    PRIMARY KEY (id_community1, id_community2),
    FOREIGN KEY (id_community1) REFERENCES Community(id_community),
    FOREIGN KEY (id_community2) REFERENCES Community(id_community)
);

-- ============================
-- Individual Connection
-- ============================
CREATE TABLE Individual_Connexion (
    id_individual1 INT,
    id_individual2 INT,
    PRIMARY KEY (id_individual1, id_individual2),
    FOREIGN KEY (id_individual1) REFERENCES Individual(id_individual),
    FOREIGN KEY (id_individual2) REFERENCES Individual(id_individual)
);

-- ============================
-- Membership
-- ============================
CREATE TABLE Membership (
    id INT PRIMARY KEY,
    joinedAt DATE,
    isExcluded BOOLEAN,
    id_community INT NOT NULL,
    id_individual INT NOT NULL,
    FOREIGN KEY (id_community) REFERENCES Community(id_community),
    FOREIGN KEY (id_individual) REFERENCES Individual(id_individual)
);

-- ============================
-- Exclusion Vote
-- ============================
CREATE TABLE ExclusionVote (
    id INT PRIMARY KEY,
    votedAt DATE,
    vote BOOLEAN,
    membership_id INT NOT NULL,
    FOREIGN KEY (membership_id) REFERENCES Membership(id)
);

-- ============================
-- G1 Account
-- ============================
CREATE TABLE G1Account (
    id INT PRIMARY KEY,
    publicKey VARCHAR NOT NULL UNIQUE,
    entity_id INT NOT NULL,
    FOREIGN KEY (entity_id) REFERENCES Entity(id)
);

-- ============================
-- Message
-- ============================
CREATE TABLE Message (
    id INT PRIMARY KEY,
    SentAt DATE,
    Subject VARCHAR,
    body VARCHAR,
    sender_id INT NOT NULL,
    recipient_id INT NOT NULL,
    InReplyTo_id INT,
    FOREIGN KEY (sender_id) REFERENCES Entity(id),
    FOREIGN KEY (recipient_id) REFERENCES Entity(id),
    FOREIGN KEY (InReplyTo_id) REFERENCES Message(id)
);

-- ============================
-- Vues
-- ============================
CREATE VIEW vIndividual AS
SELECT e.id, e.displayName, e.createdAt, e.entity_near,
       i.email, i.latitude, i.longitude
FROM Entity e
JOIN Individual i ON e.id = i.id_individual;

CREATE VIEW vCommunity AS
SELECT e.id, e.displayName, e.createdAt, e.entity_near,
       c.name, c.description
FROM Entity e
JOIN Community c ON e.id = c.id_community;
