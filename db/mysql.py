import mysql.connector

def connect_mysql(config):
    try:
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()
        print("Testing MySQL Database connection Successfully.")
        return conn, cursor
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        exit(1)

def check_and_create_table(cursor, table_name, create_table_sql):
    cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
    result = cursor.fetchone()
    if not result:
        print(f"Table '{table_name}' does not exist. Creating table...")
        cursor.execute(create_table_sql)
        print(f"Table '{table_name}' created.")