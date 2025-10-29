import psycopg2
from qgis.core import QgsMessageLog, Qgis

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

    def get_schema_info(self):
        """
        Connects to the database and retrieves schema information from ALL non-system schemas.
        Returns:
            str: A formatted string describing the database schemas, or an error message.
        """
        log = lambda msg: QgsMessageLog.logMessage(str(msg), 'GeoCodex-DB', Qgis.Info)
        
        schema_representation = ""
        try:
            log("Connecting to fetch schema info from all user schemas...")
            conn = psycopg2.connect(**self.conn_params)
            with conn.cursor() as cur:
                # Step 1: Find all schemas that are not system schemas
                cur.execute("""
                    SELECT schema_name FROM information_schema.schemata
                    WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
                    AND schema_name NOT LIKE 'pg_toast%';
                """)
                schemas = [row[0] for row in cur.fetchall()]
                log(f"Found user schemas: {schemas}")

                # Step 2: For each schema, get its tables and columns
                for schema in schemas:
                    cur.execute("""
                        SELECT table_name, column_name, data_type
                        FROM information_schema.columns
                        WHERE table_schema = %s
                        ORDER BY table_name, ordinal_position;
                    """, (schema,))
                    
                    results = cur.fetchall()
                    if not results:
                        continue

                    schema_representation += f"\n--- Schema: {schema} ---\n"
                    current_table = ""
                    for table, column, dtype in results:
                        if table != current_table:
                            if current_table != "":
                                schema_representation += ")\n"
                            schema_representation += f"Table '{schema}.{table}' has columns: ({column} ({dtype})"
                            current_table = table
                        else:
                            schema_representation += f", {column} ({dtype})"
                    
                    if current_table: # Ensure we close the parenthesis for the last table in the schema
                        schema_representation += ")"

            conn.close()
            log("Schema info fetched successfully.")
            
            # This logic is now correctly placed inside the 'try' block.
            if not schema_representation:
                return "Warning: No tables found in any user schemas."
            return schema_representation

        except Exception as e:
            error_message = f"Failed to get schema info: {e}"
            log(error_message)
            return f"Error: {error_message}"