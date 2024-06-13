import sqlite3

def remove_columns(database_path, table_name, columns_to_remove):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # Get the existing columns
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns_info = cursor.fetchall()
    existing_columns = [info[1] for info in columns_info]

    # Filter columns to retain
    columns_to_keep = [col for col in existing_columns if col not in columns_to_remove]

    if not columns_to_keep:
        print("No columns left in the table after removing specified columns.")
        return

    # Create a temporary table
    temp_table_name = f"{table_name}_temp"
    columns_to_keep_str = ", ".join(columns_to_keep)
    cursor.execute(f"CREATE TABLE {temp_table_name} AS SELECT {columns_to_keep_str} FROM {table_name}")

    # Drop the original table
    cursor.execute(f"DROP TABLE {table_name}")

    # Rename the temporary table to the original table name
    cursor.execute(f"ALTER TABLE {temp_table_name} RENAME TO {table_name}")

    conn.commit()
    conn.close()
    print(f"Columns {columns_to_remove} have been removed from {table_name} table.")

# Usage
database_path = 'c:\\Users\\User\\Desktop\\BCC\\search-site\\databases\\users_data.db'  # Update this with your actual database path
table_name = 'users'
columns_to_remove = ['date', 'link']  # Update this with the actual columns you want to remove

remove_columns(database_path, table_name, columns_to_remove)
