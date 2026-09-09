"""Application de gestion de communauté - Interface utilisateur simple."""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
from datetime import date
import math
from db_connection import get_connection


# ==================== VUES SPÉCIALISÉES ====================


def view_community(conn, individual_id: int) -> List[Dict[str, Any]]:
    """
    Vue Community : Affiche toutes les communautés d'une personne avec statut d'exclusion.
    
    Args:
        conn: Connexion à la base de données
        individual_id: ID de l'individu
        
    Returns:
        Liste des communautés avec statut d'exclusion
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT 
                c.id_community,
                c.name,
                c.description,
                m.joinedAt,
                m.isExcluded,
                COUNT(DISTINCT m2.id_individual) as total_members
            FROM Membership m
            JOIN Community c ON m.id_community = c.id_community
            LEFT JOIN Membership m2 ON m2.id_community = c.id_community
            WHERE m.id_individual = %s
            GROUP BY c.id_community, c.name, c.description, m.joinedAt, m.isExcluded
            ORDER BY c.name
        """, (individual_id,))
        return cur.fetchall()


def view_message(conn, entity_id: int) -> List[Dict[str, Any]]:
    """
    Vue Message : Affiche les messages avec références aux messages originaux.
    
    Args:
        conn: Connexion à la base de données
        entity_id: ID de l'entité (expéditeur ou destinataire)
        
    Returns:
        Liste des messages avec leurs références
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            WITH RECURSIVE message_thread AS (
                -- Messages initiaux (sans réponse)
                SELECT 
                    m.id,
                    m.SentAt,
                    m.Subject,
                    m.body,
                    m.sender_id,
                    m.recipient_id,
                    m.InReplyTo_id,
                    e1.displayName as sender_name,
                    e2.displayName as recipient_name,
                    0 as depth,
                    ARRAY[m.id] as thread_path
                FROM Message m
                JOIN Entity e1 ON m.sender_id = e1.id
                JOIN Entity e2 ON m.recipient_id = e2.id
                WHERE (m.sender_id = %s OR m.recipient_id = %s)
                    AND m.InReplyTo_id IS NULL
                
                UNION ALL
                
                -- Messages de réponse
                SELECT 
                    m.id,
                    m.SentAt,
                    m.Subject,
                    m.body,
                    m.sender_id,
                    m.recipient_id,
                    m.InReplyTo_id,
                    e1.displayName as sender_name,
                    e2.displayName as recipient_name,
                    mt.depth + 1,
                    mt.thread_path || m.id
                FROM Message m
                JOIN Entity e1 ON m.sender_id = e1.id
                JOIN Entity e2 ON m.recipient_id = e2.id
                JOIN message_thread mt ON m.InReplyTo_id = mt.id
                WHERE (m.sender_id = %s OR m.recipient_id = %s)
            )
            SELECT * FROM message_thread
            ORDER BY thread_path, SentAt
        """, (entity_id, entity_id, entity_id, entity_id))
        return cur.fetchall()


def view_proximity(conn, individual_id: int, max_distance_km: float = 1.0) -> List[Dict[str, Any]]:
    """
    Vue Proximity : Affiche les individus proches d'un individu donné dans un rayon spécifié.
    
    Utilise la vue vProximity pour trouver les individus à distance inférieure à max_distance_km.
    
    Args:
        conn: Connexion à la base de données
        individual_id: ID de l'individu de référence
        max_distance_km: Distance maximale en km (défaut: 1.0)
        
    Returns:
        Liste des individus proches avec leur distance
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Utiliser la vue vProximity pour obtenir les individus proches
        cur.execute("""
            SELECT 
                nearby_individual_id as id_individual,
                nearby_name as displayname,
                nearby_email as email,
                CAST(nearby_latitude AS FLOAT) / 1000000.0 as latitude,
                CAST(nearby_longitude AS FLOAT) / 1000000.0 as longitude,
                distance_km
            FROM vProximity
            WHERE reference_individual_id = %s
                AND distance_km IS NOT NULL
                AND distance_km <= %s
            ORDER BY distance_km
        """, (individual_id, max_distance_km))
        
        results = cur.fetchall()
        return list(results)


# ==================== RECHERCHE ====================


def search_people(conn, search_term: str) -> List[Dict[str, Any]]:
    """Recherche des personnes par nom ou email."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT 
                i.id_individual,
                e.displayName,
                i.email,
                i.latitude,
                i.longitude
            FROM Individual i
            JOIN Entity e ON i.id_individual = e.id
            WHERE LOWER(e.displayName) LIKE LOWER(%s)
                OR LOWER(i.email) LIKE LOWER(%s)
            ORDER BY e.displayName
        """, (f'%{search_term}%', f'%{search_term}%'))
        return cur.fetchall()


def search_communities(conn, search_term: str) -> List[Dict[str, Any]]:
    """Recherche des communautés par nom ou description."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT 
                c.id_community,
                c.name,
                c.description,
                COUNT(DISTINCT m.id_individual) as member_count
            FROM Community c
            LEFT JOIN Membership m ON c.id_community = m.id_community
            WHERE LOWER(c.name) LIKE LOWER(%s)
                OR LOWER(c.description) LIKE LOWER(%s)
            GROUP BY c.id_community, c.name, c.description
            ORDER BY c.name
        """, (f'%{search_term}%', f'%{search_term}%'))
        return cur.fetchall()


def search_skills(conn, search_term: str) -> List[Dict[str, Any]]:
    """Recherche des compétences par label ou description."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT 
                s.id,
                s.label,
                s.description,
                COUNT(DISTINCT es.entity_id) as entity_count
            FROM Skill s
            LEFT JOIN EntitySkill es ON s.id = es.skill_id
            WHERE LOWER(s.label) LIKE LOWER(%s)
                OR LOWER(s.description) LIKE LOWER(%s)
            GROUP BY s.id, s.label, s.description
            ORDER BY s.label
        """, (f'%{search_term}%', f'%{search_term}%'))
        return cur.fetchall()


def search_services(conn, search_term: str) -> List[Dict[str, Any]]:
    """Recherche des services par titre ou description."""
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT 
                s.id,
                s.title,
                s.type,
                s.description,
                e.displayName as provider_name
            FROM Service s
            JOIN Entity e ON s.entity_id = e.id
            WHERE LOWER(s.title) LIKE LOWER(%s)
                OR LOWER(s.description) LIKE LOWER(%s)
            ORDER BY s.title
        """, (f'%{search_term}%', f'%{search_term}%'))
        return cur.fetchall()


# ==================== OPÉRATIONS CRUD ====================


def get_next_id(conn, table_name: str, id_column: str) -> int:
    """
    Récupère le prochain ID disponible pour une table.
    
    Args:
        conn: Connexion à la base de données
        table_name: Nom de la table (doit être une valeur sûre)
        id_column: Nom de la colonne ID (doit être une valeur sûre)
        
    Returns:
        Prochain ID disponible
        
    Note:
        Les noms de table et colonne sont validés pour éviter l'injection SQL.
        Seules les tables et colonnes connues sont acceptées.
    """
    # Validation stricte des noms de tables et colonnes pour éviter l'injection SQL
    valid_tables = {
        'Entity': 'id',
        'Individual': 'id_individual',
        'Community': 'id_community',
        'Message': 'id',
        'Membership': 'id',
        'Skill': 'id',
        'EntitySkill': 'id',
        'Service': 'id',
        'ExclusionVote': 'id',
        'G1Account': 'id',
    }
    
    if table_name not in valid_tables:
        raise ValueError(f"Unauthorized table: {table_name}")
    if id_column != valid_tables[table_name]:
        raise ValueError(f"Invalid ID column for {table_name}: {id_column}")
    
    with conn.cursor() as cur:
        # Utilisation de formatage sûr car les valeurs sont validées
        cur.execute(f"SELECT COALESCE(MAX({id_column}), 0) + 1 FROM {table_name}")
        result = cur.fetchone()
        return result[0] if result else 1


def add_individual(conn, display_name: str, email: str, latitude: Optional[float] = None, 
                   longitude: Optional[float] = None, entity_near: Optional[int] = None) -> int:
    """
    Ajoute un nouvel individu à la base de données.
    
    Args:
        conn: Connexion à la base de données
        display_name: Nom d'affichage
        email: Adresse email (doit être unique)
        latitude: Latitude (optionnel)
        longitude: Longitude (optionnel)
        entity_near: ID d'une entité proche (optionnel)
        
    Returns:
        ID de l'individu créé
        
    Raises:
        psycopg2.IntegrityError: Si l'email existe déjà
    """
    with conn.cursor() as cur:
        # Récupérer le prochain ID pour Entity
        entity_id = get_next_id(conn, "Entity", "id")
        
        # Créer l'entité
        cur.execute("""
            INSERT INTO Entity (id, displayName, createdAt, entity_near)
            VALUES (%s, %s, %s, %s)
        """, (entity_id, display_name, date.today(), entity_near))
        
        # Créer l'individu
        cur.execute("""
            INSERT INTO Individual (id_individual, email, latitude, longitude)
            VALUES (%s, %s, %s, %s)
        """, (entity_id, email, int(latitude) if latitude else None, 
              int(longitude) if longitude else None))
        
        conn.commit()
        return entity_id


def add_community(conn, name: str, description: Optional[str] = None, 
                  entity_near: Optional[int] = None) -> int:
    """
    Ajoute une nouvelle communauté à la base de données.
    
    Args:
        conn: Connexion à la base de données
        name: Nom de la communauté (doit être unique)
        description: Description (optionnel)
        entity_near: ID d'une entité proche (optionnel)
        
    Returns:
        ID de la communauté créée
        
    Raises:
        psycopg2.IntegrityError: Si le nom existe déjà
    """
    with conn.cursor() as cur:
        # Récupérer le prochain ID pour Entity
        entity_id = get_next_id(conn, "Entity", "id")
        
        # Créer l'entité
        cur.execute("""
            INSERT INTO Entity (id, displayName, createdAt, entity_near)
            VALUES (%s, %s, %s, %s)
        """, (entity_id, name, date.today(), entity_near))
        
        # Créer la communauté
        cur.execute("""
            INSERT INTO Community (id_community, name, description)
            VALUES (%s, %s, %s)
        """, (entity_id, name, description))
        
        conn.commit()
        return entity_id


def send_message(conn, sender_id: int, recipient_id: int, subject: Optional[str] = None,
                 body: Optional[str] = None, in_reply_to_id: Optional[int] = None) -> int:
    """
    Envoie un message entre deux entités.
    
    Args:
        conn: Connexion à la base de données
        sender_id: ID de l'expéditeur
        recipient_id: ID du destinataire
        subject: Sujet du message (optionnel)
        body: Corps du message (optionnel)
        in_reply_to_id: ID du message auquel répondre (optionnel)
        
    Returns:
        ID du message créé
        
    Raises:
        psycopg2.IntegrityError: Si les IDs d'entité n'existent pas
    """
    with conn.cursor() as cur:
        message_id = get_next_id(conn, "Message", "id")
        
        cur.execute("""
            INSERT INTO Message (id, SentAt, Subject, body, sender_id, recipient_id, InReplyTo_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (message_id, date.today(), subject, body, sender_id, recipient_id, in_reply_to_id))
        
        conn.commit()
        return message_id


def join_community(conn, individual_id: int, community_id: int, 
                   is_excluded: bool = False) -> int:
    """
    Fait rejoindre un individu à une communauté.
    
    Args:
        conn: Connexion à la base de données
        individual_id: ID de l'individu
        community_id: ID de la communauté
        is_excluded: Statut d'exclusion (défaut: False)
        
    Returns:
        ID du membership créé
        
    Raises:
        psycopg2.IntegrityError: Si l'individu ou la communauté n'existe pas
    """
    with conn.cursor() as cur:
        membership_id = get_next_id(conn, "Membership", "id")
        
        cur.execute("""
            INSERT INTO Membership (id, joinedAt, isExcluded, id_community, id_individual)
            VALUES (%s, %s, %s, %s, %s)
        """, (membership_id, date.today(), is_excluded, community_id, individual_id))
        
        conn.commit()
        return membership_id


def leave_community(conn, individual_id: int, community_id: int) -> bool:
    """
    Fait quitter un individu d'une communauté.
    
    Args:
        conn: Connexion à la base de données
        individual_id: ID de l'individu
        community_id: ID de la communauté
        
    Returns:
        True si l'adhésion a été supprimée, False sinon
    """
    with conn.cursor() as cur:
        cur.execute("""
            DELETE FROM Membership
            WHERE id_individual = %s AND id_community = %s
        """, (individual_id, community_id))
        conn.commit()
        return cur.rowcount > 0


def add_skill(conn, label: str, description: Optional[str] = None) -> int:
    """
    Ajoute une nouvelle compétence à la base de données.
    
    Args:
        conn: Connexion à la base de données
        label: Label de la compétence
        description: Description (optionnel)
        
    Returns:
        ID de la compétence créée
    """
    with conn.cursor() as cur:
        skill_id = get_next_id(conn, "Skill", "id")
        
        cur.execute("""
            INSERT INTO Skill (id, label, description)
            VALUES (%s, %s, %s)
        """, (skill_id, label, description))
        
        conn.commit()
        return skill_id


def add_entity_skill(conn, entity_id: int, skill_id: int, level: int) -> int:
    """
    Associe une compétence à une entité avec un niveau.
    
    Args:
        conn: Connexion à la base de données
        entity_id: ID de l'entité
        skill_id: ID de la compétence
        level: Niveau de compétence (1-5)
        
    Returns:
        ID de l'association créée
        
    Raises:
        ValueError: Si le niveau n'est pas entre 1 et 5
    """
    if not (1 <= level <= 5):
        raise ValueError("Level must be between 1 and 5")
    
    with conn.cursor() as cur:
        entity_skill_id = get_next_id(conn, "EntitySkill", "id")
        
        cur.execute("""
            INSERT INTO EntitySkill (id, level, entity_id, skill_id)
            VALUES (%s, %s, %s, %s)
        """, (entity_skill_id, level, entity_id, skill_id))
        
        conn.commit()
        return entity_skill_id


def add_service(conn, entity_id: int, title: str, service_type: str,
                description: Optional[str] = None) -> int:
    """
    Ajoute un nouveau service à la base de données.
    
    Args:
        conn: Connexion à la base de données
        entity_id: ID de l'entité fournisseur
        title: Titre du service
        service_type: Type de service ('FREE', 'EXCHANGE', 'COMMERCIAL_G1')
        description: Description (optionnel)
        
    Returns:
        ID du service créé
        
    Raises:
        ValueError: Si le type de service est invalide
    """
    valid_types = {'FREE', 'EXCHANGE', 'COMMERCIAL_G1'}
    if service_type not in valid_types:
        raise ValueError(f"Invalid service type. Must be one of: {valid_types}")
    
    with conn.cursor() as cur:
        service_id = get_next_id(conn, "Service", "id")
        
        cur.execute("""
            INSERT INTO Service (id, title, type, description, entity_id)
            VALUES (%s, %s, %s, %s, %s)
        """, (service_id, title, service_type, description, entity_id))
        
        conn.commit()
        return service_id


def connect_individuals(conn, individual1_id: int, individual2_id: int) -> None:
    """
    Crée une connexion entre deux individus.
    
    Args:
        conn: Connexion à la base de données
        individual1_id: ID du premier individu
        individual2_id: ID du deuxième individu
        
    Raises:
        psycopg2.IntegrityError: Si la connexion existe déjà ou si les IDs n'existent pas
    """
    with conn.cursor() as cur:
        # S'assurer que individual1_id < individual2_id pour éviter les doublons
        id1, id2 = min(individual1_id, individual2_id), max(individual1_id, individual2_id)
        
        cur.execute("""
            INSERT INTO Individual_Connexion (id_individual1, id_individual2)
            VALUES (%s, %s)
        """, (id1, id2))
        
        conn.commit()


def add_community_collaboration(conn, community1_id: int, community2_id: int) -> None:
    """
    Crée une collaboration entre deux communautés.
    
    Args:
        conn: Connexion à la base de données
        community1_id: ID de la première communauté
        community2_id: ID de la deuxième communauté
        
    Raises:
        psycopg2.IntegrityError: Si la collaboration existe déjà ou si les IDs n'existent pas
    """
    with conn.cursor() as cur:
        # S'assurer que community1_id < community2_id pour éviter les doublons
        id1, id2 = min(community1_id, community2_id), max(community1_id, community2_id)
        
        cur.execute("""
            INSERT INTO Community_Collaboration (id_community1, id_community2)
            VALUES (%s, %s)
        """, (id1, id2))
        
        conn.commit()


def view_individual_connections(conn, individual_id: int) -> List[Dict[str, Any]]:
    """
    Affiche toutes les connexions d'un individu.
    
    Args:
        conn: Connexion à la base de données
        individual_id: ID de l'individu
        
    Returns:
        Liste des individus connectés avec leurs informations
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT 
                CASE 
                    WHEN ic.id_individual1 = %s THEN ic.id_individual2
                    ELSE ic.id_individual1
                END as connected_individual_id,
                e.displayName as connected_name,
                i.email as connected_email,
                CAST(i.latitude AS FLOAT) / 1000000.0 as latitude,
                CAST(i.longitude AS FLOAT) / 1000000.0 as longitude
            FROM Individual_Connexion ic
            JOIN Individual i ON (
                CASE 
                    WHEN ic.id_individual1 = %s THEN i.id_individual = ic.id_individual2
                    ELSE i.id_individual = ic.id_individual1
                END
            )
            JOIN Entity e ON i.id_individual = e.id
            WHERE ic.id_individual1 = %s OR ic.id_individual2 = %s
            ORDER BY e.displayName
        """, (individual_id, individual_id, individual_id, individual_id))
        return cur.fetchall()


def view_community_collaborations(conn, community_id: int) -> List[Dict[str, Any]]:
    """
    Affiche toutes les collaborations d'une communauté.
    
    Args:
        conn: Connexion à la base de données
        community_id: ID de la communauté
        
    Returns:
        Liste des communautés collaboratrices avec leurs informations
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT 
                CASE 
                    WHEN cc.id_community1 = %s THEN cc.id_community2
                    ELSE cc.id_community1
                END as collaborating_community_id,
                c.name as collaborating_name,
                c.description as collaborating_description
            FROM Community_Collaboration cc
            JOIN Community c ON (
                CASE 
                    WHEN cc.id_community1 = %s THEN c.id_community = cc.id_community2
                    ELSE c.id_community = cc.id_community1
                END
            )
            WHERE cc.id_community1 = %s OR cc.id_community2 = %s
            ORDER BY c.name
        """, (community_id, community_id, community_id, community_id))
        return cur.fetchall()


def get_community_members(conn, community_id: int) -> List[Dict[str, Any]]:
    """
    Récupère tous les membres d'une communauté.
    
    Args:
        conn: Connexion à la base de données
        community_id: ID de la communauté
        
    Returns:
        Liste des membres avec leurs informations
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT 
                m.id as membership_id,
                i.id_individual,
                e.displayName,
                i.email,
                m.joinedAt,
                m.isExcluded
            FROM Membership m
            JOIN Individual i ON m.id_individual = i.id_individual
            JOIN Entity e ON i.id_individual = e.id
            WHERE m.id_community = %s
            ORDER BY e.displayName
        """, (community_id,))
        return cur.fetchall()


def cast_exclusion_vote(conn, voter_individual_id: int, membership_id: int, vote: bool) -> int:
    """
    Enregistre un vote d'exclusion pour un membership.
    
    Args:
        conn: Connexion à la base de données
        voter_individual_id: ID de l'individu qui vote
        membership_id: ID du membership à voter
        vote: True pour exclure, False pour garder
        
    Returns:
        ID du vote créé
        
    Raises:
        ValueError: Si le votant n'est pas membre de la même communauté
    """
    with conn.cursor() as cur:
        # Vérifier que le votant est membre de la même communauté
        cur.execute("""
            SELECT m1.id_community
            FROM Membership m1
            JOIN Membership m2 ON m1.id_community = m2.id_community
            WHERE m1.id_individual = %s AND m2.id = %s
        """, (voter_individual_id, membership_id))
        
        if not cur.fetchone():
            raise ValueError("You must be a member of the same community to vote.")
        
        # Créer le vote
        vote_id = get_next_id(conn, "ExclusionVote", "id")
        
        cur.execute("""
            INSERT INTO ExclusionVote (id, votedAt, vote, membership_id)
            VALUES (%s, %s, %s, %s)
        """, (vote_id, date.today(), vote, membership_id))
        
        conn.commit()
        
        # Vérifier si l'exclusion doit être appliquée
        check_and_apply_exclusion(conn, membership_id)
        
        return vote_id


def check_and_apply_exclusion(conn, membership_id: int) -> bool:
    """
    Vérifie les votes d'exclusion et applique l'exclusion si >50% votent pour.
    
    Args:
        conn: Connexion à la base de données
        membership_id: ID du membership à vérifier
        
    Returns:
        True si l'exclusion a été appliquée, False sinon
    """
    with conn.cursor() as cur:
        # Récupérer le membership
        cur.execute("""
            SELECT id_community, id_individual, isExcluded
            FROM Membership
            WHERE id = %s
        """, (membership_id,))
        membership = cur.fetchone()
        
        if not membership:
            return False
        
        community_id, individual_id, is_excluded = membership
        
        # Si déjà exclu, ne rien faire
        if is_excluded:
            return False
        
        # Compter les votes
        cur.execute("""
            SELECT 
                COUNT(*) as total_votes,
                SUM(CASE WHEN vote = TRUE THEN 1 ELSE 0 END) as votes_for_exclusion
            FROM ExclusionVote
            WHERE membership_id = %s
        """, (membership_id,))
        
        vote_stats = cur.fetchone()
        total_votes = vote_stats[0] or 0
        votes_for_exclusion = vote_stats[1] or 0
        
        # Compter le nombre total de membres de la communauté
        cur.execute("""
            SELECT COUNT(*) 
            FROM Membership
            WHERE id_community = %s AND isExcluded = FALSE
        """, (community_id,))
        total_members = cur.fetchone()[0] or 1
        
        # Si plus de 50% votent pour l'exclusion, exclure
        if total_votes > 0 and votes_for_exclusion > (total_members / 2):
            cur.execute("""
                UPDATE Membership
                SET isExcluded = TRUE
                WHERE id = %s
            """, (membership_id,))
            conn.commit()
            return True
        
        return False


def get_exclusion_votes(conn, membership_id: int) -> List[Dict[str, Any]]:
    """
    Récupère tous les votes d'exclusion pour un membership.
    
    Args:
        conn: Connexion à la base de données
        membership_id: ID du membership
        
    Returns:
        Liste des votes avec statistiques
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT 
                ev.id,
                ev.votedAt,
                ev.vote,
                ev.membership_id,
                m.id_community,
                m.id_individual,
                e.displayName as individual_name,
                c.name as community_name
            FROM ExclusionVote ev
            JOIN Membership m ON ev.membership_id = m.id
            JOIN Individual i ON m.id_individual = i.id_individual
            JOIN Entity e ON i.id_individual = e.id
            JOIN Community c ON m.id_community = c.id_community
            WHERE ev.membership_id = %s
            ORDER BY ev.votedAt DESC
        """, (membership_id,))
        return cur.fetchall()


def get_exclusion_vote_stats(conn, membership_id: int) -> Dict[str, Any]:
    """
    Récupère les statistiques des votes d'exclusion pour un membership.
    
    Args:
        conn: Connexion à la base de données
        membership_id: ID du membership
        
    Returns:
        Dictionnaire avec les statistiques des votes
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Récupérer le membership
        cur.execute("""
            SELECT m.id_community, m.id_individual, m.isExcluded,
                   e.displayName as individual_name,
                   c.name as community_name
            FROM Membership m
            JOIN Individual i ON m.id_individual = i.id_individual
            JOIN Entity e ON i.id_individual = e.id
            JOIN Community c ON m.id_community = c.id_community
            WHERE m.id = %s
        """, (membership_id,))
        membership = cur.fetchone()
        
        if not membership:
            return {}
        
        # Compter les votes
        cur.execute("""
            SELECT 
                COUNT(*) as total_votes,
                SUM(CASE WHEN vote = TRUE THEN 1 ELSE 0 END) as votes_for_exclusion,
                SUM(CASE WHEN vote = FALSE THEN 1 ELSE 0 END) as votes_against_exclusion
            FROM ExclusionVote
            WHERE membership_id = %s
        """, (membership_id,))
        
        vote_stats = cur.fetchone()
        
        # Compter le nombre total de membres
        cur.execute("""
            SELECT COUNT(*) 
            FROM Membership
            WHERE id_community = %s AND isExcluded = FALSE
        """, (membership['id_community'],))
        total_members = cur.fetchone()[0] or 1
        
        return {
            'membership_id': membership_id,
            'individual_id': membership['id_individual'],
            'individual_name': membership['individual_name'],
            'community_id': membership['id_community'],
            'community_name': membership['community_name'],
            'is_excluded': membership['isexcluded'],
            'total_votes': vote_stats['total_votes'] or 0,
            'votes_for_exclusion': vote_stats['votes_for_exclusion'] or 0,
            'votes_against_exclusion': vote_stats['votes_against_exclusion'] or 0,
            'total_members': total_members,
            'threshold': total_members / 2,
            'needs_exclusion': (vote_stats['votes_for_exclusion'] or 0) > (total_members / 2) if vote_stats['total_votes'] else False
        }


# ==================== INTERFACE UTILISATEUR ====================


def print_menu():
    """Displays the main menu."""
    print("\n" + "="*60)
    print("COMMUNITY MANAGEMENT SYSTEM")
    print("="*60)
    print("=== VIEWS ===")
    print("1. Community View (my communities)")
    print("2. Message View (my messages)")
    print("3. Proximity View (geographic proximity)")
    print("\n=== SEARCH ===")
    print("4. Search people")
    print("5. Search communities")
    print("6. Search skills")
    print("7. Search services")
    print("\n=== CREATION ===")
    print("8. Add a person")
    print("9. Add a community")
    print("10. Send a message")
    print("11. Join a community")
    print("12. Add a skill")
    print("13. Associate a skill with an entity")
    print("14. Add a service")
    print("15. Connect two individuals")
    print("16. Create a collaboration between communities")
    print("\n0. Quit")
    print("="*60)


def display_community_view(conn):
    """Displays the community view for an individual."""
    try:
        individual_id = int(input("Enter the individual ID: "))
        results = view_community(conn, individual_id)
        
        if not results:
            print("No community found.")
            return
        
        print(f"\n{'Communities of individual ' + str(individual_id):^60}")
        print("-" * 60)
        for row in results:
            status = "EXCLUDED" if row['isexcluded'] else "ACTIVE"
            print(f"ID: {row['id_community']}")
            print(f"Name: {row['name']}")
            print(f"Description: {row['description'] or 'N/A'}")
            print(f"Join date: {row['joinedat']}")
            print(f"Status: {status}")
            print(f"Members: {row['total_members']}")
            print("-" * 60)
    except ValueError:
        print("Error: Invalid ID")
    except Exception as e:
        print(f"Error: {e}")


def display_message_view(conn):
    """Displays the message view for an entity."""
    try:
        entity_id = int(input("Enter the entity ID: "))
        results = view_message(conn, entity_id)
        
        if not results:
            print("No message found.")
            return
        
        print(f"\n{'Messages of entity ' + str(entity_id):^60}")
        print("-" * 60)
        for row in results:
            indent = "  " * row['depth']
            print(f"{indent}ID: {row['id']}")
            print(f"{indent}Date: {row['sentat']}")
            print(f"{indent}From: {row['sender_name']} (ID: {row['sender_id']})")
            print(f"{indent}To: {row['recipient_name']} (ID: {row['recipient_id']})")
            if row['inreplyto_id']:
                print(f"{indent}In reply to: Message #{row['inreplyto_id']}")
            print(f"{indent}Subject: {row['subject'] or 'No subject'}")
            print(f"{indent}Body: {row['body'] or 'Empty'}")
            print("-" * 60)
    except ValueError:
        print("Error: Invalid ID")
    except Exception as e:
        print(f"Error: {e}")


def display_proximity_view(conn):
    """Displays the proximity view."""
    try:
        individual_id = int(input("Enter the individual ID: "))
        distance = input("Max distance in km (default: 1.0): ").strip()
        max_distance = float(distance) if distance else 1.0
        
        results = view_proximity(conn, individual_id, max_distance)
        
        print(f"\n{'Proximity View for Individual ' + str(individual_id) + ' (' + str(max_distance) + ' km)':^60}")
        print("-" * 60)
        
        print("\nNEARBY INDIVIDUALS:")
        if results:
            for ind in results:
                print(f"  ID: {ind['id_individual']}")
                print(f"  Name: {ind['displayname']}")
                print(f"  Email: {ind['email']}")
                print(f"  Position: ({ind['latitude']:.6f}, {ind['longitude']:.6f})")
                print(f"  Distance: {ind['distance_km']:.2f} km")
                if ind['latitude'] and ind['longitude']:
                    zoom = 17
                    url = f"https://www.openstreetmap.org/#map={zoom}/{ind['latitude']}/{ind['longitude']}"
                    print(f"  Map: {url}")
                print("-" * 60)
        else:
            print("  No individual found in this radius.")
            
    except ValueError:
        print("Error: Invalid individual ID or distance")
    except Exception as e:
        print(f"Error: {e}")


def display_search_people(conn):
    """Displays search results for people."""
    search_term = input("Search term: ").strip()
    if not search_term:
        print("Empty search term.")
        return
    
    results = search_people(conn, search_term)
    
    print(f"\n{'Search results: ' + search_term:^60}")
    print("-" * 60)
    if results:
        for row in results:
            print(f"ID: {row['id_individual']}")
            print(f"Name: {row['displayname']}")
            print(f"Email: {row['email']}")
            if row['latitude'] and row['longitude']:
                print(f"Position: ({row['latitude']}, {row['longitude']})")
            print("-" * 60)
    else:
        print("No results found.")


def display_search_communities(conn):
    """Displays search results for communities."""
    search_term = input("Search term: ").strip()
    if not search_term:
        print("Empty search term.")
        return
    
    results = search_communities(conn, search_term)
    
    print(f"\n{'Search results: ' + search_term:^60}")
    print("-" * 60)
    if results:
        for row in results:
            print(f"ID: {row['id_community']}")
            print(f"Name: {row['name']}")
            print(f"Description: {row['description'] or 'N/A'}")
            print(f"Members: {row['member_count']}")
            print("-" * 60)
    else:
        print("No results found.")


def display_search_skills(conn):
    """Displays search results for skills."""
    search_term = input("Search term: ").strip()
    if not search_term:
        print("Empty search term.")
        return
    
    results = search_skills(conn, search_term)
    
    print(f"\n{'Search results: ' + search_term:^60}")
    print("-" * 60)
    if results:
        for row in results:
            print(f"ID: {row['id']}")
            print(f"Label: {row['label']}")
            print(f"Description: {row['description'] or 'N/A'}")
            print(f"Owned by: {row['entity_count']} entity(ies)")
            print("-" * 60)
    else:
        print("No results found.")


def display_search_services(conn):
    """Displays search results for services."""
    search_term = input("Search term: ").strip()
    if not search_term:
        print("Empty search term.")
        return
    
    results = search_services(conn, search_term)
    
    print(f"\n{'Search results: ' + search_term:^60}")
    print("-" * 60)
    if results:
        for row in results:
            type_map = {
                'FREE': 'Free',
                'EXCHANGE': 'Exchange',
                'COMMERCIAL_G1': 'Commercial (G1)'
            }
            service_type = type_map.get(row['type'], row['type'])
            print(f"ID: {row['id']}")
            print(f"Title: {row['title']}")
            print(f"Type: {service_type}")
            print(f"Description: {row['description'] or 'N/A'}")
            print(f"Provider: {row['provider_name']}")
            print("-" * 60)
    else:
        print("No results found.")


def display_add_individual(conn):
    """Interface to add an individual."""
    try:
        print("\n=== Add a new individual ===")
        display_name = input("Display name: ").strip()
        if not display_name:
            print("Error: Display name is required.")
            return
        
        email = input("Email: ").strip()
        if not email:
            print("Error: Email is required.")
            return
        
        latitude_input = input("Latitude (optional, press Enter to skip): ").strip()
        latitude = float(latitude_input) if latitude_input else None
        
        longitude_input = input("Longitude (optional, press Enter to skip): ").strip()
        longitude = float(longitude_input) if longitude_input else None
        
        entity_near_input = input("Nearby entity ID (optional, press Enter to skip): ").strip()
        entity_near = int(entity_near_input) if entity_near_input else None
        
        individual_id = add_individual(conn, display_name, email, latitude, longitude, entity_near)
        print(f"\n✓ Individual created successfully! ID: {individual_id}")
        
    except ValueError as e:
        print(f"Error: Invalid value - {e}")
        conn.rollback()
    except psycopg2.IntegrityError as e:
        print(f"Error: Constraint violation - {e}")
        conn.rollback()
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()


def display_add_community(conn):
    """Interface to add a community."""
    try:
        print("\n=== Add a new community ===")
        name = input("Community name: ").strip()
        if not name:
            print("Error: Name is required.")
            return
        
        description = input("Description (optional, press Enter to skip): ").strip()
        description = description if description else None
        
        entity_near_input = input("Nearby entity ID (optional, press Enter to skip): ").strip()
        entity_near = int(entity_near_input) if entity_near_input else None
        
        community_id = add_community(conn, name, description, entity_near)
        print(f"\n✓ Community created successfully! ID: {community_id}")
        
    except ValueError as e:
        print(f"Error: Invalid value - {e}")
        conn.rollback()
    except psycopg2.IntegrityError as e:
        print(f"Error: Constraint violation - {e}")
        conn.rollback()
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()


def display_send_message(conn):
    """Interface to send a message."""
    try:
        print("\n=== Send a message ===")
        sender_id = int(input("Sender ID: "))
        recipient_id = int(input("Recipient ID: "))
        
        subject = input("Subject (optional, press Enter to skip): ").strip()
        subject = subject if subject else None
        
        body = input("Message body (optional, press Enter to skip): ").strip()
        body = body if body else None
        
        in_reply_to_input = input("Message ID to reply to (optional, press Enter to skip): ").strip()
        in_reply_to_id = int(in_reply_to_input) if in_reply_to_input else None
        
        message_id = send_message(conn, sender_id, recipient_id, subject, body, in_reply_to_id)
        print(f"\n✓ Message sent successfully! ID: {message_id}")
        
    except ValueError as e:
        print(f"Error: Invalid value - {e}")
        conn.rollback()
    except psycopg2.IntegrityError as e:
        print(f"Error: Constraint violation - {e}")
        conn.rollback()
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()


def display_join_community(conn):
    """Interface to join a community."""
    try:
        print("\n=== Join a community ===")
        individual_id = int(input("Individual ID: "))
        community_id = int(input("Community ID: "))
        
        excluded_input = input("Excluded? (y/n, default: n): ").strip().lower()
        is_excluded = excluded_input == 'y'
        
        membership_id = join_community(conn, individual_id, community_id, is_excluded)
        print(f"\n✓ Membership created successfully! ID: {membership_id}")
        
    except ValueError as e:
        print(f"Error: Invalid value - {e}")
        conn.rollback()
    except psycopg2.IntegrityError as e:
        print(f"Error: Constraint violation - {e}")
        conn.rollback()
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()


def display_add_skill(conn):
    """Interface to add a skill."""
    try:
        print("\n=== Add a skill ===")
        label = input("Skill label: ").strip()
        if not label:
            print("Error: Label is required.")
            return
        
        description = input("Description (optional, press Enter to skip): ").strip()
        description = description if description else None
        
        skill_id = add_skill(conn, label, description)
        print(f"\n✓ Skill created successfully! ID: {skill_id}")
        
    except ValueError as e:
        print(f"Error: Invalid value - {e}")
        conn.rollback()
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()


def display_add_entity_skill(conn):
    """Interface to associate a skill with an entity."""
    try:
        print("\n=== Entity-skill association ===")
        entity_id = int(input("Entity ID: "))
        skill_id = int(input("Skill ID: "))
        level = int(input("Level (1-5): "))
        
        entity_skill_id = add_entity_skill(conn, entity_id, skill_id, level)
        print(f"\n✓ Association created successfully! ID: {entity_skill_id}")
        
    except ValueError as e:
        print(f"Error: Invalid value - {e}")
        conn.rollback()
    except psycopg2.IntegrityError as e:
        print(f"Error: Constraint violation - {e}")
        conn.rollback()
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()


def display_add_service(conn):
    """Interface to add a service."""
    try:
        print("\n=== Add a service ===")
        entity_id = int(input("Provider entity ID: "))
        title = input("Service title: ").strip()
        if not title:
            print("Error: Title is required.")
            return
        
        print("Available types: FREE, EXCHANGE, COMMERCIAL_G1")
        service_type = input("Service type: ").strip().upper()
        
        description = input("Description (optional, press Enter to skip): ").strip()
        description = description if description else None
        
        service_id = add_service(conn, entity_id, title, service_type, description)
        print(f"\n✓ Service created successfully! ID: {service_id}")
        
    except ValueError as e:
        print(f"Error: Invalid value - {e}")
        conn.rollback()
    except psycopg2.IntegrityError as e:
        print(f"Error: Constraint violation - {e}")
        conn.rollback()
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()


def display_connect_individuals(conn):
    """Interface to connect two individuals."""
    try:
        print("\n=== Connect individuals ===")
        individual1_id = int(input("First individual ID: "))
        individual2_id = int(input("Second individual ID: "))
        
        connect_individuals(conn, individual1_id, individual2_id)
        print(f"\n✓ Connection created successfully!")
        
    except ValueError as e:
        print(f"Error: Invalid value - {e}")
        conn.rollback()
    except psycopg2.IntegrityError as e:
        print(f"Error: Constraint violation - {e}")
        conn.rollback()
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()


def display_add_community_collaboration(conn):
    """Interface to create a collaboration between communities."""
    try:
        print("\n=== Community collaboration ===")
        community1_id = int(input("First community ID: "))
        community2_id = int(input("Second community ID: "))
        
        add_community_collaboration(conn, community1_id, community2_id)
        print(f"\n✓ Collaboration created successfully!")
        
    except ValueError as e:
        print(f"Error: Invalid value - {e}")
        conn.rollback()
    except psycopg2.IntegrityError as e:
        print(f"Error: Constraint violation - {e}")
        conn.rollback()
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()


def main():
    """Main application function."""
    try:
        conn = get_connection()
        print("Database connection established.")
        
        while True:
            print_menu()
            choice = input("Your choice: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                display_community_view(conn)
            elif choice == '2':
                display_message_view(conn)
            elif choice == '3':
                display_proximity_view(conn)
            elif choice == '4':
                display_search_people(conn)
            elif choice == '5':
                display_search_communities(conn)
            elif choice == '6':
                display_search_skills(conn)
            elif choice == '7':
                display_search_services(conn)
            elif choice == '8':
                display_add_individual(conn)
            elif choice == '9':
                display_add_community(conn)
            elif choice == '10':
                display_send_message(conn)
            elif choice == '11':
                display_join_community(conn)
            elif choice == '12':
                display_add_skill(conn)
            elif choice == '13':
                display_add_entity_skill(conn)
            elif choice == '14':
                display_add_service(conn)
            elif choice == '15':
                display_connect_individuals(conn)
            elif choice == '16':
                display_add_community_collaboration(conn)
            else:
                print("Invalid choice. Please try again.")
        
        conn.close()
        print("\nGoodbye!")
        
    except psycopg2.OperationalError as e:
        error_msg = str(e)
        if "could not translate host name" in error_msg or "Name or service not known" in error_msg:
            print(f"\n❌ Network connection error: {e}")
            print("\n💡 The server 'tuxa.sme.utc' is not accessible from your current network.")
            print("   Possible solutions:")
            print("   - Connect to the university network")
            print("   - Enable the university VPN if available")
            print("   - Verify that you are connected to the internal network")
        else:
            print(f"Connection error: {e}")
    except psycopg2.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()