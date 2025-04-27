from pymongo import MongoClient
from urllib.parse import quote_plus

def create_database_and_user(db_name, new_username, new_password):
    admin_username = quote_plus("admin")
    admin_password = quote_plus("admin@123")  # Encode special characters in the password

    admin_uri = f"mongodb://{admin_username}:{admin_password}@10.10.22.190:27017/admin"
    client = MongoClient(admin_uri)

    admin_db = client['admin']

    try:
        # Create a new user with readWrite role for the specified database
        client[db_name].command("createUser", new_username,
                                pwd=new_password,
                                roles=[{"role": "readWrite", "db": db_name}])
        print(f"User '{new_username}' created with readWrite access to database '{db_name}'.")
    except Exception as e:
        print(f"Error occurred while creating user: {e}")
    finally:
        client.close()

# Example usage: Create a user 'ebz' with password '123123' for database 'phonon_dos_tcd'
create_database_and_user('atomate2_scx', 'scx', 'scx_123123')