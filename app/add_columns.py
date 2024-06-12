import sqlite3
from config import DATABASES, BACKUP_DATABASES

def connect_db(database):
    return sqlite3.connect(database)

def execute_query(conn, query, params=()):
    cursor = conn.cursor()
    cursor.execute(query, params)
    return cursor

def fetch_all(cursor):
    return cursor.fetchall()

def close_db(conn):
    conn.close()

def get_table_names(database):
    conn = connect_db(database)
    cursor = execute_query(conn, "SELECT name FROM sqlite_master WHERE type='table';")
    tables = fetch_all(cursor)
    close_db(conn)
    return [table[0] for table in tables]

def update_date_column(database, table_name, old_default, new_default):
    conn = connect_db(database)
    cursor = conn.cursor()
    try:
        cursor.execute(f"UPDATE `{table_name}` SET `date` = ? WHERE `date` = ?", (new_default, old_default))
        conn.commit()
    except sqlite3.OperationalError as e:
        print(f"Error updating table `{table_name}` in `{database}`: {e}")
    finally:
        close_db(conn)

def update_date_column_all_tables(database, old_default, new_default):
    tables = get_table_names(database)
    for table in tables:
        if table != 'sqlite_sequence':
            update_date_column(database, table, old_default, new_default)

def main():
    old_default = '0000y00m00d_00h00m00s'
    new_default = '2024-05-01 00:00:00'

    # Update main databases
    for db_key in DATABASES:
        database = DATABASES[db_key]
        print(f"Updating date column in database: {database}")
        update_date_column_all_tables(database, old_default, new_default)

    # Update backup databases
    for db_key in BACKUP_DATABASES:
        backup_database = BACKUP_DATABASES[db_key]
        print(f"Updating date column in backup database: {backup_database}")
        update_date_column_all_tables(backup_database, old_default, new_default)

if __name__ == "__main__":
    main()
