import sqlite3
import datetime
import random
import string
import re
from config import DATABASES, BACKUP_DATABASES

# Utility Functions
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

# Database Functions
def get_table_names(database):
    conn = connect_db(database)
    cursor = execute_query(conn, "SELECT name FROM sqlite_master WHERE type='table';")
    tables = fetch_all(cursor)
    close_db(conn)
    return [table[0] for table in tables]

def get_table_content(database, table):
    conn = connect_db(database)
    cursor = execute_query(conn, f"SELECT * FROM {table};")
    content = fetch_all(cursor)
    columns = [description[0] for description in cursor.description]
    close_db(conn)
    return columns, content

def update_cell(database, table, column, row_id, new_value):
    conn = connect_db(database)
    execute_query(conn, f"UPDATE {table} SET {column} = ? WHERE id = ?", (new_value, row_id))
    conn.commit()
    close_db(conn)

def delete_row(database, table, row_id):
    conn = connect_db(database)
    cursor = execute_query(conn, f"DELETE FROM {table} WHERE id = ?", (row_id,))
    deleted = cursor.rowcount
    conn.commit()
    close_db(conn)
    return deleted > 0

def create_backup(language, table, username):
    source_db = DATABASES[language]
    backup_db = BACKUP_DATABASES[language]
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_table = f"{table}_{username}_{timestamp}"
    
    conn = connect_db(backup_db)
    try:
        execute_query(conn, f"ATTACH DATABASE '{source_db}' AS source_db")

        print("SOURCE DB: ", source_db)
        print("BACKUP_DB: ", backup_db)

        # Check if the backup table already exists
        cursor = execute_query(conn, "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (backup_table,))
        if cursor.fetchone():
            print(f"Backup table `{backup_table}` already exists. Skipping backup creation.")
            return

        execute_query(conn, f"CREATE TABLE `{backup_table}` AS SELECT * FROM source_db.`{table}`")
        conn.commit()
    except Exception as e:
        print(f"Error creating backup: {e}")
        raise e
    finally:
        close_db(conn)


def get_backups(database, table):
    conn = connect_db(database)
    cursor = execute_query(conn, "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?", (f"{table}_%",))
    backups = fetch_all(cursor)
    close_db(conn)

    # Filter backups to match the format productname_username_ymd_hms
    backup_pattern = re.compile(rf"^{table}_[a-zA-Z0-9]+_\d{{8}}_\d{{6}}$")
    valid_backups = [backup[0] for backup in backups if backup_pattern.match(backup[0])]

    return valid_backups

def get_backup_content(database, backup):
    conn = connect_db(database)
    cursor = execute_query(conn, f"SELECT * FROM {backup};")
    content = fetch_all(cursor)
    columns = [description[0] for description in cursor.description]
    close_db(conn)
    return columns, content

def restore_backup(language, table, backup):
    source_db = DATABASES[language]
    backup_db = BACKUP_DATABASES[language]
    
    conn = connect_db(source_db)
    execute_query(conn, f"DROP TABLE IF EXISTS {table}")
    execute_query(conn, f"ATTACH DATABASE '{backup_db}' AS backup_db")
    execute_query(conn, f"CREATE TABLE {table} AS SELECT * FROM backup_db.{backup}")
    conn.commit()
    close_db(conn)

def generate_message_id(k_len=20):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=k_len))

def insert_data_into_table(database, table_name, data, author='base'):
    try:
        conn = connect_db(database)
        cursor = conn.cursor()
        check_query = f'SELECT EXISTS(SELECT 1 FROM `{table_name}` WHERE question = ? LIMIT 1)'
        insert_query = f'INSERT INTO `{table_name}` (id, question, answer, question_id, data_type, date, link) VALUES (?, ?, ?, ?, ?, ?, ?)'

        duplicate_found = False

        cursor.execute(f'SELECT MAX(id) FROM `{table_name}`')
        last_id = cursor.fetchone()[0] or 0

        for entry in data:
            question = entry.get('question')
            answer = entry.get('answer')
            question_id = generate_message_id()
            data_type = entry.get('data_type', 'manual')
            date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            link = entry.get('link', 'https://www.bcc.kz/') if not entry.get('link') else entry.get('link')
            if len(link) == 0:
                link = 'https://www.bcc.kz/'
                
            cursor.execute(check_query, (question,))
            exists = cursor.fetchone()[0]

            if not exists:
                cursor.execute(insert_query, (last_id + 1, question, answer, question_id, data_type, date, link))
                last_id += 1
            else:
                duplicate_found = True
                print(f"Question already exists: {question}")

        conn.commit()
        close_db(conn)
        return duplicate_found
    except Exception as e:
        print(f"Error inserting data into table: {e}")
        raise e

def get_last_row_id(database, table_name):
    conn = connect_db(database)
    cursor = execute_query(conn, f'SELECT MAX(id) FROM {table_name}')
    last_row_id = cursor.fetchone()[0]
    close_db(conn)
    return last_row_id
