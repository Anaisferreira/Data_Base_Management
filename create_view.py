"""
Script to create the vProximity view in the PostgreSQL database.
"""

import psycopg2
from db_connection import get_connection


def create_proximity_view(conn):
    """
    Creates the vProximity view in the database.
    
    Args:
        conn: Database connection
    """
    view_sql = """
    -- Drop view if it exists
    DROP VIEW IF EXISTS vProximity CASCADE;
    
    -- Create the proximity view
    CREATE VIEW vProximity AS
    SELECT 
        i1.id_individual as reference_individual_id,
        i2.id_individual as nearby_individual_id,
        e1.displayName as reference_name,
        e2.displayName as nearby_name,
        i2.email as nearby_email,
        i2.latitude as nearby_latitude,
        i2.longitude as nearby_longitude,
        CASE 
            WHEN i1.latitude IS NOT NULL AND i1.longitude IS NOT NULL 
                 AND i2.latitude IS NOT NULL AND i2.longitude IS NOT NULL THEN
                SQRT(
                    POWER((CAST(i2.latitude AS FLOAT) / 1000000.0 - CAST(i1.latitude AS FLOAT) / 1000000.0) * 111.0, 2) +
                    POWER((CAST(i2.longitude AS FLOAT) / 1000000.0 - CAST(i1.longitude AS FLOAT) / 1000000.0) * 111.0 * COS(RADIANS(CAST(i1.latitude AS FLOAT) / 1000000.0)), 2)
                )
            ELSE NULL
        END as distance_km
    FROM Individual i1
    CROSS JOIN Individual i2
    JOIN Entity e1 ON i1.id_individual = e1.id
    JOIN Entity e2 ON i2.id_individual = e2.id
    WHERE i1.id_individual != i2.id_individual
        AND i1.latitude IS NOT NULL 
        AND i1.longitude IS NOT NULL
        AND i2.latitude IS NOT NULL 
        AND i2.longitude IS NOT NULL;
    """
    
    try:
        with conn.cursor() as cur:
            # Execute the view creation
            cur.execute(view_sql)
            conn.commit()
            print("✓ View vProximity created successfully!")
            return True
    except psycopg2.Error as e:
        print(f"❌ Error creating view: {e}")
        conn.rollback()
        return False


def main():
    """Main function to create the view."""
    print("="*60)
    print("CREATE PROXIMITY VIEW")
    print("="*60)
    
    try:
        conn = get_connection()
        print("✓ Database connection established\n")
        
        if create_proximity_view(conn):
            print("\n✓ View creation completed successfully!")
        else:
            print("\n❌ View creation failed!")
        
        conn.close()
        
    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()

