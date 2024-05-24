from flask import Flask, render_template, request, jsonify
import sqlite3
import datetime

app = Flask(__name__)

# Function to get table names from a database
def get_table_names(database):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    conn.close()
    return [table[0] for table in tables]

# Function to get table content
def get_table_content(database, table):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table};")
    content = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    conn.close()
    return columns, content

# Function to update cell content
def update_cell(database, table, column, row_id, new_value):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"UPDATE {table} SET {column} = ? WHERE rowid = ?", (new_value, row_id))
    conn.commit()
    conn.close()

# Function to delete row
def delete_row(database, table, row_id):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table} WHERE rowid = ?", (row_id,))
    conn.commit()
    conn.close()

# Function to create a backup
def create_backup(language, table):
    source_db = 'cards_faq_kz.db' if language == 'kazakh' else 'cards_faq_ru.db'
    backup_db = 'cards_faq_kz_backup.db' if language == 'kazakh' else 'cards_faq_ru_backup.db'
    backup_table = f"{table}_backup_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    conn = sqlite3.connect(backup_db)
    cursor = conn.cursor()
    cursor.execute(f"ATTACH DATABASE '{source_db}' AS source_db")
    cursor.execute(f"CREATE TABLE {backup_table} AS SELECT * FROM source_db.{table}")
    conn.commit()
    conn.close()

# Function to get backups
def get_backups(database, table):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '{table}_backup_%' ORDER BY name DESC;")
    backups = cursor.fetchall()
    conn.close()
    return [backup[0] for backup in backups]

# Function to get content of a backup
def get_backup_content(database, backup):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {backup};")
    content = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    conn.close()
    return columns, content

# Function to restore from a backup
def restore_backup(language, table, backup):
    source_db = 'cards_faq_kz.db' if language == 'kazakh' else 'cards_faq_ru.db'
    backup_db = 'cards_faq_kz_backup.db' if language == 'kazakh' else 'cards_faq_ru_backup.db'
    
    conn = sqlite3.connect(source_db)
    cursor = conn.cursor()
    cursor.execute(f"DROP TABLE IF EXISTS {table}")
    cursor.execute(f"ATTACH DATABASE '{backup_db}' AS backup_db")
    cursor.execute(f"CREATE TABLE {table} AS SELECT * FROM backup_db.{backup}")
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_tables', methods=['POST'])
def get_tables():
    data = request.get_json()
    language = data.get('language')
    database = 'cards_faq_kz.db' if language == 'kazakh' else 'cards_faq_ru.db'
    tables = get_table_names(database)
    return jsonify(tables)

@app.route('/get_table_content', methods=['POST'])
def get_table_content_route():
    data = request.get_json()
    language = data.get('language')
    table = data.get('table')
    database = 'cards_faq_kz.db' if language == 'kazakh' else 'cards_faq_ru.db'
    columns, content = get_table_content(database, table)
    return jsonify({'columns': columns, 'content': content})

@app.route('/update_cell', methods=['POST'])
def update_cell_route():
    data = request.get_json()
    language = data.get('language')
    table = data.get('table')
    column = data.get('column')
    row_id = data.get('row_id')
    new_value = data.get('new_value')
    database = 'cards_faq_kz.db' if language == 'kazakh' else 'cards_faq_ru.db'
    create_backup(language, table)  # Create backup before updating
    update_cell(database, table, column, row_id, new_value)
    return jsonify(success=True)

@app.route('/delete_row', methods=['POST'])
def delete_row_route():
    data = request.get_json()
    language = data.get('language')
    table = data.get('table')
    row_id = data.get('row_id')
    database = 'cards_faq_kz.db' if language == 'kazakh' else 'cards_faq_ru.db'
    create_backup(language, table)  # Create backup before deleting
    delete_row(database, table, row_id)
    return jsonify(success=True)

@app.route('/search_by_question_id', methods=['POST'])
def search_by_question_id():
    data = request.get_json()
    language = data.get('language')
    table = data.get('table')
    search = data.get('search')
    database = 'cards_faq_kz.db' if language == 'kazakh' else 'cards_faq_ru.db'
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    query = f"SELECT * FROM {table} WHERE question_id LIKE ?"
    cursor.execute(query, (search + '%',))
    content = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    conn.close()
    return jsonify({'columns': columns, 'content': content})

@app.route('/get_backups', methods=['POST'])
def get_backups_route():
    data = request.get_json()
    language = data.get('language')
    table = data.get('table')
    database = 'cards_faq_kz_backup.db' if language == 'kazakh' else 'cards_faq_ru_backup.db'
    backups = get_backups(database, table)
    return jsonify(backups)

@app.route('/get_backup_content', methods=['POST'])
def get_backup_content_route():
    data = request.get_json()
    language = data.get('language')
    table = data.get('table')
    backup = data.get('backup')
    database = 'cards_faq_kz_backup.db' if language == 'kazakh' else 'cards_faq_ru_backup.db'
    columns, content = get_backup_content(database, backup)
    return jsonify({'columns': columns, 'content': content})

@app.route('/restore_backup', methods=['POST'])
def restore_backup_route():
    data = request.get_json()
    language = data.get('language')
    table = data.get('table')
    backup = data.get('backup')
    restore_backup(language, table, backup)
    return jsonify(success=True)

if __name__ == '__main__':
    app.run(debug=True)
