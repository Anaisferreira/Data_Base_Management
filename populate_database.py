"""
Script to populate the database with sample data.

This script creates realistic and consistent data for testing the application.
"""

import psycopg2
from datetime import date, timedelta
import random
import string
from typing import List, Tuple
from db_connection import get_connection


def generate_random_string(length: int = 10) -> str:
    """Generates a random string."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_public_key() -> str:
    """Generates a simulated public key."""
    return '0x' + ''.join(random.choices(string.hexdigits, k=64))


def populate_entities(conn, count: int) -> List[int]:
    """
    Creates base entities.
    
    Args:
        conn: Database connection
        count: Number of entities to create
        
    Returns:
        List of created IDs
    """
    print(f"Creating {count} entities...")
    entity_ids = []
    
    with conn.cursor() as cur:
        # Check existing IDs
        cur.execute("SELECT COALESCE(MAX(id), 0) FROM Entity")
        max_id = cur.fetchone()[0]
        start_id = max_id + 1
        
        names = [
            "Alice Martin", "Bob Dupont", "Claire Bernard", "David Leroy",
            "Emma Moreau", "François Petit", "Gabrielle Rousseau", "Henri Dubois",
            "Isabelle Girard", "Julien Lambert", "Karine Simon", "Louis Michel",
            "Marie Durand", "Nicolas Laurent", "Olivia Martinez", "Pierre Roux",
            "Quentin Blanc", "Rose Vincent", "Sophie Garnier", "Thomas Lefebvre"
        ]
        
        for i in range(count):
            entity_id = start_id + i
            display_name = names[i % len(names)] if i < len(names) else f"Person {entity_id}"
            created_at = date.today() - timedelta(days=random.randint(0, 365))
            
            # Some entities may have a nearby entity
            entity_near = None
            if entity_ids and random.random() < 0.3:
                entity_near = random.choice(entity_ids)
            
            cur.execute("""
                INSERT INTO Entity (id, displayName, createdAt, entity_near)
                VALUES (%s, %s, %s, %s)
            """, (entity_id, display_name, created_at, entity_near))
            
            entity_ids.append(entity_id)
        
        conn.commit()
        print(f"✓ {count} entities created (IDs: {start_id} to {start_id + count - 1})")
    
    return entity_ids


def populate_skills(conn, count: int) -> List[int]:
    """
    Creates skills.
    
    Args:
        conn: Database connection
        count: Number of skills to create
        
    Returns:
        List of created IDs
    """
    print(f"Creating {count} skills...")
    skill_ids = []
    
    skills_data = [
        ("Python", "Python programming"),
        ("JavaScript", "Web development with JavaScript"),
        ("SQL", "Databases and SQL queries"),
        ("Java", "Object-oriented programming in Java"),
        ("C++", "System programming in C++"),
        ("React", "React framework for frontend development"),
        ("Node.js", "Backend development with Node.js"),
        ("Docker", "Containerization with Docker"),
        ("Git", "Version control with Git"),
        ("Linux", "Linux system administration"),
        ("Machine Learning", "Artificial intelligence and machine learning"),
        ("Cybersecurity", "Information security and data protection"),
        ("UX/UI Design", "User interface design"),
        ("Digital Marketing", "Online marketing strategies"),
        ("Project Management", "Project management methodologies")
    ]
    
    with conn.cursor() as cur:
        cur.execute("SELECT COALESCE(MAX(id), 0) FROM Skill")
        max_id = cur.fetchone()[0]
        start_id = max_id + 1
        
        for i in range(count):
            skill_id = start_id + i
            if i < len(skills_data):
                label, description = skills_data[i]
            else:
                label = f"Skill {skill_id}"
                description = f"Description of skill {skill_id}"
            
            cur.execute("""
                INSERT INTO Skill (id, label, description)
                VALUES (%s, %s, %s)
            """, (skill_id, label, description))
            
            skill_ids.append(skill_id)
        
        conn.commit()
        print(f"✓ {count} skills created")
    
    return skill_ids


def populate_individuals(conn, entity_ids: List[int], count: int) -> List[int]:
    """
    Creates individuals from existing entities.
    
    Args:
        conn: Database connection
        entity_ids: List of available entity IDs
        count: Number of individuals to create
        
    Returns:
        List of created individual IDs
    """
    print(f"Creating {count} individuals...")
    individual_ids = []
    
    emails = [
        "alice.martin@email.com", "bob.dupont@email.com", "claire.bernard@email.com",
        "david.leroy@email.com", "emma.moreau@email.com", "francois.petit@email.com",
        "gabrielle.rousseau@email.com", "henri.dubois@email.com", "isabelle.girard@email.com",
        "julien.lambert@email.com", "karine.simon@email.com", "louis.michel@email.com",
        "marie.durand@email.com", "nicolas.laurent@email.com", "olivia.martinez@email.com"
    ]
    
    # Coordinates around Compiègne (France)
    base_lat = 49.4179
    base_lon = 2.8261
    
    with conn.cursor() as cur:
        selected_entities = random.sample(entity_ids, min(count, len(entity_ids)))
        
        for i, entity_id in enumerate(selected_entities):
            email = emails[i % len(emails)] if i < len(emails) else f"user{entity_id}@email.com"
            
            # Random coordinates around Compiègne (±0.1 degree ≈ ±11 km)
            latitude = int((base_lat + random.uniform(-0.1, 0.1)) * 1000000)
            longitude = int((base_lon + random.uniform(-0.1, 0.1)) * 1000000)
            
            # Some individuals may not have coordinates
            if random.random() < 0.2:
                latitude = None
                longitude = None
            
            cur.execute("""
                INSERT INTO Individual (id_individual, email, latitude, longitude)
                VALUES (%s, %s, %s, %s)
            """, (entity_id, email, latitude, longitude))
            
            individual_ids.append(entity_id)
        
        conn.commit()
        print(f"✓ {count} individuals created")
    
    return individual_ids


def populate_communities(conn, entity_ids: List[int], count: int) -> List[int]:
    """
    Creates communities from existing entities.
    
    Args:
        conn: Database connection
        entity_ids: List of available entity IDs
        count: Number of communities to create
        
    Returns:
        List of created community IDs
    """
    print(f"Creating {count} communities...")
    community_ids = []
    
    communities_data = [
        ("Python Developers", "Community of passionate Python developers"),
        ("UTC Students", "Community of UTC students"),
        ("Cybersecurity", "Group of cybersecurity experts"),
        ("Designers", "Community of UX/UI designers"),
        ("Startupers", "Network of entrepreneurs and startups"),
        ("Data Scientists", "Community of data scientists"),
        ("Open Source", "Contributors to open source projects"),
        ("Gaming", "Gaming community"),
        ("Photography", "Amateurs and professional photographers"),
        ("Music", "Musicians and music lovers")
    ]
    
    with conn.cursor() as cur:
        selected_entities = random.sample(entity_ids, min(count, len(entity_ids)))
        
        for i, entity_id in enumerate(selected_entities):
            if i < len(communities_data):
                name, description = communities_data[i]
            else:
                name = f"Community {entity_id}"
                description = f"Description of community {entity_id}"
            
            cur.execute("""
                INSERT INTO Community (id_community, name, description)
                VALUES (%s, %s, %s)
            """, (entity_id, name, description))
            
            community_ids.append(entity_id)
        
        conn.commit()
        print(f"✓ {count} communities created")
    
    return community_ids


def populate_messages(conn, entity_ids: List[int], count: int) -> List[int]:
    """
    Creates messages between entities.
    
    Args:
        conn: Database connection
        entity_ids: List of available entity IDs
        count: Number of messages to create
        
    Returns:
        List of created message IDs
    """
    print(f"Creating {count} messages...")
    message_ids = []
    
    subjects = [
        "Hello", "Important question", "Meeting tomorrow", "Thank you for your help",
        "Collaboration proposal", "Invitation", "Reminder", "New feature",
        "Problem solved", "Welcome to the community"
    ]
    
    bodies = [
        "Hello, I hope you are doing well.",
        "I would like to discuss an interesting project.",
        "Can you help me with this question?",
        "Thank you very much for your contribution!",
        "I have a proposal that might interest you.",
        "You are invited to join our event.",
        "Reminder: the meeting is scheduled for tomorrow.",
        "We have added a new feature.",
        "The problem has been solved successfully.",
        "Welcome! We are delighted to have you with us."
    ]
    
    with conn.cursor() as cur:
        cur.execute("SELECT COALESCE(MAX(id), 0) FROM Message")
        max_id = cur.fetchone()[0]
        start_id = max_id + 1
        
        for i in range(count):
            message_id = start_id + i
            sender_id = random.choice(entity_ids)
            recipient_id = random.choice([eid for eid in entity_ids if eid != sender_id])
            
            subject = random.choice(subjects)
            body = random.choice(bodies)
            sent_at = date.today() - timedelta(days=random.randint(0, 90))
            
            # Some messages may be replies
            in_reply_to = None
            if message_ids and random.random() < 0.3:
                in_reply_to = random.choice(message_ids)
            
            cur.execute("""
                INSERT INTO Message (id, SentAt, Subject, body, sender_id, recipient_id, InReplyTo_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (message_id, sent_at, subject, body, sender_id, recipient_id, in_reply_to))
            
            message_ids.append(message_id)
        
        conn.commit()
        print(f"✓ {count} messages created")
    
    return message_ids


def populate_memberships(conn, individual_ids: List[int], community_ids: List[int], count: int) -> List[int]:
    """
    Creates memberships of individuals to communities.
    
    Args:
        conn: Database connection
        individual_ids: List of individual IDs
        community_ids: List of community IDs
        count: Number of memberships to create
        
    Returns:
        List of created membership IDs
    """
    print(f"Creating {count} memberships...")
    membership_ids = []
    memberships_created = set()
    
    with conn.cursor() as cur:
        cur.execute("SELECT COALESCE(MAX(id), 0) FROM Membership")
        max_id = cur.fetchone()[0]
        start_id = max_id + 1
        
        for i in range(count):
            membership_id = start_id + i
            individual_id = random.choice(individual_ids)
            community_id = random.choice(community_ids)
            
            # Avoid duplicates
            membership_key = (individual_id, community_id)
            if membership_key in memberships_created:
                continue
            
            memberships_created.add(membership_key)
            
            joined_at = date.today() - timedelta(days=random.randint(0, 180))
            is_excluded = random.random() < 0.1  # 10% excluded
            
            cur.execute("""
                INSERT INTO Membership (id, joinedAt, isExcluded, id_community, id_individual)
                VALUES (%s, %s, %s, %s, %s)
            """, (membership_id, joined_at, is_excluded, community_id, individual_id))
            
            membership_ids.append(membership_id)
        
        conn.commit()
        print(f"✓ {len(membership_ids)} memberships created")
    
    return membership_ids


def populate_entity_skills(conn, entity_ids: List[int], skill_ids: List[int], count: int) -> List[int]:
    """
    Associates skills with entities.
    
    Args:
        conn: Database connection
        entity_ids: List of entity IDs
        skill_ids: List of skill IDs
        count: Number of associations to create
        
    Returns:
        List of created association IDs
    """
    print(f"Creating {count} entity-skill associations...")
    entity_skill_ids = []
    associations_created = set()
    
    with conn.cursor() as cur:
        cur.execute("SELECT COALESCE(MAX(id), 0) FROM EntitySkill")
        max_id = cur.fetchone()[0]
        start_id = max_id + 1
        
        for i in range(count):
            entity_skill_id = start_id + i
            entity_id = random.choice(entity_ids)
            skill_id = random.choice(skill_ids)
            level = random.randint(1, 5)
            
            # Avoid duplicates
            association_key = (entity_id, skill_id)
            if association_key in associations_created:
                continue
            
            associations_created.add(association_key)
            
            cur.execute("""
                INSERT INTO EntitySkill (id, level, entity_id, skill_id)
                VALUES (%s, %s, %s, %s)
            """, (entity_skill_id, level, entity_id, skill_id))
            
            entity_skill_ids.append(entity_skill_id)
        
        conn.commit()
        print(f"✓ {len(entity_skill_ids)} associations created")
    
    return entity_skill_ids


def populate_services(conn, entity_ids: List[int], count: int) -> List[int]:
    """
    Creates services offered by entities.
    
    Args:
        conn: Database connection
        entity_ids: List of entity IDs
        count: Number of services to create
        
    Returns:
        List of created service IDs
    """
    print(f"Creating {count} services...")
    service_ids = []
    
    services_data = [
        ("Python Course", "FREE", "Free Python programming course"),
        ("Web Development", "COMMERCIAL_G1", "Custom website creation"),
        ("UX Consultation", "EXCHANGE", "UX services exchange"),
        ("SQL Tutoring", "FREE", "Free help to learn SQL"),
        ("Logo Design", "COMMERCIAL_G1", "Professional logo creation"),
        ("Computer Repair", "EXCHANGE", "Repair services exchange"),
        ("Git Training", "FREE", "Free Git training"),
        ("Mobile Development", "COMMERCIAL_G1", "iOS and Android mobile applications"),
        ("Event Photography", "EXCHANGE", "Photography services"),
        ("Cybersecurity Consulting", "COMMERCIAL_G1", "Security audit and consulting")
    ]
    
    service_types = ['FREE', 'EXCHANGE', 'COMMERCIAL_G1']
    
    with conn.cursor() as cur:
        cur.execute("SELECT COALESCE(MAX(id), 0) FROM Service")
        max_id = cur.fetchone()[0]
        start_id = max_id + 1
        
        for i in range(count):
            service_id = start_id + i
            entity_id = random.choice(entity_ids)
            
            if i < len(services_data):
                title, service_type, description = services_data[i]
            else:
                title = f"Service {service_id}"
                service_type = random.choice(service_types)
                description = f"Description of service {service_id}"
            
            cur.execute("""
                INSERT INTO Service (id, title, type, description, entity_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (service_id, title, service_type, description, entity_id))
            
            service_ids.append(service_id)
        
        conn.commit()
        print(f"✓ {count} services created")
    
    return service_ids


def populate_individual_connections(conn, individual_ids: List[int], count: int) -> None:
    """
    Creates connections between individuals.
    
    Args:
        conn: Database connection
        individual_ids: List of individual IDs
        count: Number of connections to create
    """
    print(f"Creating {count} connections between individuals...")
    connections_created = set()
    
    with conn.cursor() as cur:
        for _ in range(count):
            individual1_id = random.choice(individual_ids)
            individual2_id = random.choice([iid for iid in individual_ids if iid != individual1_id])
            
            # Ensure individual1_id < individual2_id
            id1, id2 = min(individual1_id, individual2_id), max(individual1_id, individual2_id)
            connection_key = (id1, id2)
            
            if connection_key in connections_created:
                continue
            
            connections_created.add(connection_key)
            
            try:
                cur.execute("""
                    INSERT INTO Individual_Connexion (id_individual1, id_individual2)
                    VALUES (%s, %s)
                """, (id1, id2))
            except psycopg2.IntegrityError:
                # Connection already exists, ignore
                continue
        
        conn.commit()
        print(f"✓ {len(connections_created)} connections created")


def populate_community_collaborations(conn, community_ids: List[int], count: int) -> None:
    """
    Creates collaborations between communities.
    
    Args:
        conn: Database connection
        community_ids: List of community IDs
        count: Number of collaborations to create
    """
    print(f"Creating {count} collaborations between communities...")
    collaborations_created = set()
    
    with conn.cursor() as cur:
        for _ in range(count):
            community1_id = random.choice(community_ids)
            community2_id = random.choice([cid for cid in community_ids if cid != community1_id])
            
            # Ensure community1_id < community2_id
            id1, id2 = min(community1_id, community2_id), max(community1_id, community2_id)
            collaboration_key = (id1, id2)
            
            if collaboration_key in collaborations_created:
                continue
            
            collaborations_created.add(collaboration_key)
            
            try:
                cur.execute("""
                    INSERT INTO Community_Collaboration (id_community1, id_community2)
                    VALUES (%s, %s)
                """, (id1, id2))
            except psycopg2.IntegrityError:
                # Collaboration already exists, ignore
                continue
        
        conn.commit()
        print(f"✓ {len(collaborations_created)} collaborations created")


def populate_exclusion_votes(conn, membership_ids: List[int], count: int) -> List[int]:
    """
    Creates exclusion votes.
    
    Args:
        conn: Database connection
        membership_ids: List of membership IDs
        count: Number of votes to create
        
    Returns:
        List of created vote IDs
    """
    print(f"Creating {count} exclusion votes...")
    vote_ids = []
    
    with conn.cursor() as cur:
        cur.execute("SELECT COALESCE(MAX(id), 0) FROM ExclusionVote")
        max_id = cur.fetchone()[0]
        start_id = max_id + 1
        
        for i in range(count):
            vote_id = start_id + i
            membership_id = random.choice(membership_ids)
            vote = random.choice([True, False])
            voted_at = date.today() - timedelta(days=random.randint(0, 30))
            
            cur.execute("""
                INSERT INTO ExclusionVote (id, votedAt, vote, membership_id)
                VALUES (%s, %s, %s, %s)
            """, (vote_id, voted_at, vote, membership_id))
            
            vote_ids.append(vote_id)
        
        conn.commit()
        print(f"✓ {count} votes created")
    
    return vote_ids


def populate_g1_accounts(conn, entity_ids: List[int], count: int) -> List[int]:
    """
    Creates G1 accounts.
    
    Args:
        conn: Database connection
        entity_ids: List of entity IDs
        count: Number of accounts to create
        
    Returns:
        List of created account IDs
    """
    print(f"Creating {count} G1 accounts...")
    account_ids = []
    public_keys_used = set()
    
    with conn.cursor() as cur:
        cur.execute("SELECT COALESCE(MAX(id), 0) FROM G1Account")
        max_id = cur.fetchone()[0]
        start_id = max_id + 1
        
        selected_entities = random.sample(entity_ids, min(count, len(entity_ids)))
        
        for i, entity_id in enumerate(selected_entities):
            account_id = start_id + i
            
            # Generate a unique public key
            public_key = generate_public_key()
            while public_key in public_keys_used:
                public_key = generate_public_key()
            public_keys_used.add(public_key)
            
            cur.execute("""
                INSERT INTO G1Account (id, publicKey, entity_id)
                VALUES (%s, %s, %s)
            """, (account_id, public_key, entity_id))
            
            account_ids.append(account_id)
        
        conn.commit()
        print(f"✓ {count} G1 accounts created")
    
    return account_ids


def main():
    """Main function to populate the database."""
    print("="*60)
    print("DATABASE POPULATION SCRIPT")
    print("="*60)
    
    try:
        conn = get_connection()
        print("✓ Database connection established\n")
        
        # Ask for confirmation
        response = input("Do you want to continue? This will add sample data. (y/n): ").strip().lower()
        if response != 'y':
            print("Operation cancelled.")
            return
        
        print("\nStarting population...\n")
        
        # Create data in correct order (respect FK constraints)
        entity_ids = populate_entities(conn, count=30)
        skill_ids = populate_skills(conn, count=15)
        
        # Reserve some entities for communities
        # Take first ones for individuals, next ones for communities
        individual_entity_ids = entity_ids[:15]
        community_entity_ids = entity_ids[15:25]
        
        individual_ids = populate_individuals(conn, individual_entity_ids, count=15)
        community_ids = populate_communities(conn, community_entity_ids, count=10)
        message_ids = populate_messages(conn, entity_ids, count=25)
        membership_ids = populate_memberships(conn, individual_ids, community_ids, count=30)
        entity_skill_ids = populate_entity_skills(conn, entity_ids, skill_ids, count=40)
        service_ids = populate_services(conn, entity_ids, count=15)
        populate_individual_connections(conn, individual_ids, count=20)
        populate_community_collaborations(conn, community_ids, count=8)
        vote_ids = populate_exclusion_votes(conn, membership_ids, count=10)
        g1_account_ids = populate_g1_accounts(conn, entity_ids, count=10)
        
        print("\n" + "="*60)
        print("✓ Population completed successfully!")
        print("="*60)
        print(f"\nSummary:")
        print(f"  - Entities: {len(entity_ids)}")
        print(f"  - Individuals: {len(individual_ids)}")
        print(f"  - Communities: {len(community_ids)}")
        print(f"  - Skills: {len(skill_ids)}")
        print(f"  - Messages: {len(message_ids)}")
        print(f"  - Memberships: {len(membership_ids)}")
        print(f"  - Services: {len(service_ids)}")
        print(f"  - G1 Accounts: {len(g1_account_ids)}")
        
        conn.close()
        
    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if conn:
            conn.rollback()


if __name__ == "__main__":
    main()

