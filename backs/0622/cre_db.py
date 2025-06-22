from pymongo import MongoClient
from urllib.parse import quote_plus

def create_database_and_user(db_name, new_username, new_password):
    admin_username = quote_plus("xxx")
    admin_password = quote_plus("xxx")  # Encode special characters in the password

    admin_uri = f"mongodb://{admin_username}:{admin_password}@xxxxxxx/admin"
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

# Example usage: Create a user 'xxx' with password 'xxx' for database 'xxx'
create_database_and_user('xxx', 'xxx', 'xxx')
