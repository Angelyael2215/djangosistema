import mysql.connector

def reset_database():
    # Connection parameters
    config = {
        'host': '192.168.1.124',
        'user': 'Admin',
        'password': 'orticorp2209',
    }

    try:
        # Connect to MySQL server
        cnx = mysql.connector.connect(**config)
        cursor = cnx.cursor()

        # Drop and recreate database
        cursor.execute("DROP DATABASE IF EXISTS orticorpsystem")
        cursor.execute("CREATE DATABASE orticorpsystem")
        print("Database reset successfully")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        cursor.close()
        cnx.close()

if __name__ == "__main__":
    reset_database()