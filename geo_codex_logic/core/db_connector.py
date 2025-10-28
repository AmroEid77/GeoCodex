import psycopg2

class DBConnector:
    """
    A client to handle all interactions with a PostgreSQL/PostGIS database.
    """
    def __init__(self, host, port, dbname, user, password):
        """
        Initializes the connector with database credentials.
        """
        self.conn_params = {
            "host": host,
            "port": port,
            "dbname": dbname,
            "user": user,
            "password": password
        }
        self.connection = None

    def test_connection(self):
        """
        Attempts to connect to the database to verify credentials.
        Returns:
            tuple: (bool, str) indicating success/failure and a message.
        """
        try:
            # Attempt to establish a connection
            self.connection = psycopg2.connect(**self.conn_params)
            
            # If successful, immediately close it as we're just testing.
            self.connection.close()
            
            print("Database connection test successful.")
            return True, "Database connection successful!"

        except psycopg2.OperationalError as e:
            # This catches common errors like wrong host, port, or database name,
            # or if the database server isn't running.
            error_message = f"Connection failed: {e}"
            print(error_message)
            return False, error_message
            
        except psycopg2.Error as e:
            # This catches other errors, like authentication failure (wrong user/pass).
            error_message = f"An error occurred: {e}"
            print(error_message)
            return False, error_message