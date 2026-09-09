"""Module de gestion de la connexion à la base de données PostgreSQL."""

import psycopg2
from typing import Optional


# Configuration de la base de données
# Le serveur tuxa.sme.utc.fr pointe vers revproxy2.utc.fr (195.83.155.17)
# Si le DNS ne fonctionne pas, utilisez l'IP directement
HOST = "tuxa.sme.utc"  # ou "195.83.155.17" si le DNS ne fonctionne pas
PORT = 5432  # Port PostgreSQL par défaut (non utilisé dans la syntaxe DSN)
USER = "ed05a006"
PASSWORD = "xfnSVer2mLp9"
DATABASE = "dbed05a006"


def get_connection():
    """
    Établit une connexion à la base de données PostgreSQL.
    
    Returns:
        Connexion PostgreSQL
        
    Raises:
        psycopg2.Error: En cas d'erreur de connexion
        
    Note:
        Le serveur est probablement accessible uniquement depuis le réseau
        de l'université ou via VPN.
        Utilise la même syntaxe que l'ancien code fonctionnel.
    """
    try:
        # Essayer d'abord avec le nom de domaine
        return psycopg2.connect(
            "host=%s dbname=%s user=%s password=%s" % (HOST, DATABASE, USER, PASSWORD)
        )
    except psycopg2.OperationalError as e:
        if "could not translate host name" in str(e):
            # Si le DNS échoue, essayer avec l'IP directement
            print("⚠️  DNS échoué, tentative avec l'IP...")
            return psycopg2.connect(
                "host=195.83.155.17 dbname=%s user=%s password=%s" % (DATABASE, USER, PASSWORD)
            )
        raise