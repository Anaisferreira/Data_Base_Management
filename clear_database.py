"""
Script to clear all data from the database (without dropping tables).

This script deletes all records from all tables in the correct order
to respect foreign key constraints.
"""

import psycopg2
from db_connection import get_connection


def clear_database(conn):
    """
    Clears all data from the database.
    
    Args:
        conn: Database connection
        
    Note:
        Tables are deleted in reverse order of creation to respect FK constraints.
    """
    print("="*60)
    print("DATABASE CLEARING SCRIPT")
    print("="*60)
    
    with conn.cursor() as cur:
        # Delete in reverse order of creation to respect foreign key constraints
        
        print("\nDeleting ExclusionVote records...")
        cur.execute("DELETE FROM ExclusionVote")
        count = cur.rowcount
        print(f"✓ {count} exclusion votes deleted")
        
        print("\nDeleting G1Account records...")
        cur.execute("DELETE FROM G1Account")
        count = cur.rowcount
        print(f"✓ {count} G1 accounts deleted")
        
        print("\nDeleting Community_Collaboration records...")
        cur.execute("DELETE FROM Community_Collaboration")
        count = cur.rowcount
        print(f"✓ {count} community collaborations deleted")
        
        print("\nDeleting Individual_Connexion records...")
        cur.execute("DELETE FROM Individual_Connexion")
        count = cur.rowcount
        print(f"✓ {count} individual connections deleted")
        
        print("\nDeleting Service records...")
        cur.execute("DELETE FROM Service")
        count = cur.rowcount
        print(f"✓ {count} services deleted")
        
        print("\nDeleting EntitySkill records...")
        cur.execute("DELETE FROM EntitySkill")
        count = cur.rowcount
        print(f"✓ {count} entity-skill associations deleted")
        
        print("\nDeleting Membership records...")
        cur.execute("DELETE FROM Membership")
        count = cur.rowcount
        print(f"✓ {count} memberships deleted")
        
        print("\nDeleting Message records...")
        cur.execute("DELETE FROM Message")
        count = cur.rowcount
        print(f"✓ {count} messages deleted")
        
        print("\nDeleting Community records...")
        cur.execute("DELETE FROM Community")
        count = cur.rowcount
        print(f"✓ {count} communities deleted")
        
        print("\nDeleting Individual records...")
        cur.execute("DELETE FROM Individual")
        count = cur.rowcount
        print(f"✓ {count} individuals deleted")
        
        print("\nDeleting Skill records...")
        cur.execute("DELETE FROM Skill")
        count = cur.rowcount
        print(f"✓ {count} skills deleted")
        
        print("\nDeleting Entity records...")
        cur.execute("DELETE FROM Entity")
        count = cur.rowcount
        print(f"✓ {count} entities deleted")
        
        conn.commit()
        print("\n" + "="*60)
        print("✓ All data cleared successfully!")
        print("="*60)


def main():
    """Main function to clear the database."""
    try:
        conn = get_connection()
        print("✓ Database connection established\n")
        
        # Ask for confirmation
        print("⚠️  WARNING: This will delete ALL data from the database!")
        print("   Tables will NOT be dropped, only their data will be deleted.\n")
        response = input("Do you want to continue? (yes/no): ").strip().lower()
        
        if response != 'yes':
            print("Operation cancelled.")
            conn.close()
            return
        
        clear_database(conn)
        conn.close()
        
    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
        if conn:
            conn.rollback()
            conn.close()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if conn:
            conn.rollback()
            conn.close()


if __name__ == "__main__":
    main()

