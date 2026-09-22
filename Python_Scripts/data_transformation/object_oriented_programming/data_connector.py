from pandas import DataFrame
from sqlalchemy import inspect, create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
import sqlalchemy 
import yaml 

"""
data_connector.py

Handles the creation of database connections and the loading
of data into the target database.
"""


class DataConnector:
    """
    Responsible for establishing database connections and
    loading data into the database.
    """

    def read_database_credentials(self, config_file: yaml):
            """
            Method to read database_credentials from a yaml file

            Parameters:
            config_file
            The file pathway to the yaml file

            Returns:
            database_credentials : dict
            A dictionary of the database credentials from yaml file

            """

            try:
                with open(config_file) as file:
                    database_credentials = yaml.safe_load(file)
                # Return the yaml file as a dictionary
                return database_credentials
            # If the file is not found, raise an exception
            except FileNotFoundError:
                raise FileNotFoundError("Config file not found")
            # If the config file is not in a YAML format, raise an exception
            except yaml.YAMLError:
                raise yaml.YAMLError("Invalid YAML format.")

    def create_connection_string(
        self, creds : dict, connect_to_database=False, new_db_name=None
    ):
        """
        Method to create the connection_string needed to connect to a postgresql database

        Parameters:
        config_file_name:
        The pathway to the config_file used to create the string

        connect_to_database: bool
        Flag indicating whether to connect to a specific database within the server (default: False)

        new_db_name: str
        The name of the new database to connect to if connect_to_database is True (default: None)

        Returns:
        Connection string : str
        A string used to connect to the database

        """

        connection_string = f"{creds['DATABASE_TYPE']}+{creds['DATABASE_ENGINE']}://{creds['RDS_USER']}:{creds['RDS_PASSWORD']}@{creds['RDS_HOST']}:{creds['RDS_PORT']}"

        if connect_to_database:
            if not new_db_name:
                raise ValueError("New database name not provided")
            connection_string += f"/{new_db_name}"

        return connection_string

    def initialise_database_connection(
        self,
        connection_string : str,
        isolation_level="AUTOCOMMIT"
    ):
        """
        Method to establish a connection to the database

        Parameters:
        connection_string : str
        The connection string, which represents the database to connect to.
ß
        Returns:
        database_engine: engine
        A database engine object

        isolation_level : str = AUTOCOMMIT

        The level of isolation for the database transaction.
        By default, this is set to AUTOCOMMIT


        """
        try:
            database_engine = create_engine(
                connection_string, isolation_level=isolation_level
            )

            database_engine.connect()
            print("connection successful")
            return database_engine
        except OperationalError:

            print("Error Connecting to the Database")
            raise OperationalError

    def list_db_tables(self, engine : Engine):
        """
        Method to list the tables within a database

        Parameters:
        engine : Engine 
        The database Engine object which is used to interact with the source or target database

        """
        try:
            # Use the inspect method of sqlalchemy to get an inspector element
            inspector = inspect(engine)

            # Get the table names using the get_table_names method
            table_names = inspector.get_table_names()
          
            # print the table names to the console
            print(table_names)

            # Return the list of table names as an output 
            return table_names
        
        # Raise an Exception if there are any issues with listing the tables.   
        except Exception as e:
            print("Error occurred while listing tables: %s", str(e))
            raise Exception

    def load_to_db(self, df : DataFrame,  engine : Engine, table_name : str, table_condition : str, schema_name : str , dtypes=None):
        if dtypes is not None:
            try: 
                df.to_sql(table_name, engine, if_exists=table_condition, index=False, schema=schema_name, dtype=dtypes)
            except OperationalError as e: 
                print(f"Failed to upload {table_name} to the database")
                raise e
        else: 
            try: 
                df.to_sql(table_name, engine, if_exists=table_condition, index=False)
            except OperationalError as e: 
                print(f"Failed to upload {table_name} to the database")
                raise e 
            

if __name__ == "__main__":
    con = DataConnector()
    credentials = con.read_database_credentials('db_creds_local.yaml')
    print(credentials)
    con_string = con.create_connection_string(credentials, connect_to_database=True, new_db_name='api_data')
    print(con_string)
    db_engine = con.initialise_database_connection(con_string)
    print(db_engine)