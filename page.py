from flask import Flask, render_template, request, jsonify
import sqlite3
import datetime
import json
import requests

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

# Function to insert data into table
def insert_data_into_table(database, table_name, data):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    check_query = f'SELECT EXISTS(SELECT 1 FROM {table_name} WHERE question = ? LIMIT 1)'
    insert_query = f'INSERT INTO {table_name} (question, answer, question_id, data_type) VALUES (?, ?, ?, ?)'

    duplicate_found = False
    for entry in data:
        question = entry.get('question')
        answer = entry.get('answer')
        question_id = entry.get('question_id', '111')
        data_type = entry.get('data_type', 'manual')

        cursor.execute(check_query, (question,))
        exists = cursor.fetchone()[0]

        if not exists:
            cursor.execute(insert_query, (question, answer, question_id, data_type))
        else:
            duplicate_found = True
            print(f"Question already exists: {question}")

    conn.commit()
    conn.close()

    return duplicate_found

# Function to get last row id
def get_last_row_id(database, table_name):
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    cursor.execute(f'SELECT MAX(rowid) FROM {table_name}')
    last_row_id = cursor.fetchone()[0]
    conn.close()
    return last_row_id

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

@app.route('/insert_data', methods=['POST'])
def insert_data_route():
    data = request.get_json()
    language = data.get('language')
    table = data.get('table')
    new_data = data.get('data')
    database = 'cards_faq_kz.db' if language == 'kazakh' else 'cards_faq_ru.db'
    create_backup(language, table)  # Create backup before inserting
    duplicate_found = insert_data_into_table(database, table, new_data)
    return jsonify(success=True, duplicate=duplicate_found)

@app.route('/get_last_row_id', methods=['POST'])
def get_last_row_id_route():
    data = request.get_json()
    language = data.get('language')
    table = data.get('table')
    database = 'cards_faq_kz.db' if language == 'kazakh' else 'cards_faq_ru.db'
    last_row_id = get_last_row_id(database, table)
    return jsonify(last_row_id=last_row_id)

@app.route('/insert_json', methods=['POST'])
def insert_json_route():
    data = request.get_json()
    language = data.get('language')
    table = data.get('table')
    json_data = data.get('data')
    database = 'cards_faq_kz.db' if language == 'kazakh' else 'cards_faq_ru.db'
    create_backup(language, table)  # Create backup before inserting

    valid_entries = []
    duplicate_found = False
    for entry in json_data:
        if 'question_ru' in entry and 'answer_ru' in entry:
            valid_entries.append({
                'question': entry['question_ru'],
                'answer': entry['answer_ru'],
                'data_type': entry.get('type', 'manual')
            })
        elif 'question_kz' in entry and 'answer_kz' in entry:
            valid_entries.append({
                'question': entry['question_kz'],
                'answer': entry['answer_kz'],
                'data_type': entry.get('type', 'manual')
            })

    if valid_entries:
        duplicate_found = insert_data_into_table(database, table, valid_entries)
    
    return jsonify(success=True, duplicate=duplicate_found)

@app.route('/search', methods=['POST'])
def search_route():
    data = request.get_json()
    query = data.get('query')
    table_type = data.get('table_type')
    
    if not query:
        return jsonify(success=False, results=[])
    
    url = 'http://10.15.132.126:6789/post'
    search_data = {
        "query": query,
        "table_type": table_type
    }
    
    try:
        response = requests.post(url, json=search_data)
        response.raise_for_status()  # Check if the request was successful
        search_results = response.json()  # Parse the JSON response

        if search_results:
            return jsonify(success=True, results=search_results)
        else:
            return jsonify(success=False, results=[])
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return jsonify(success=False, results=[])
    except ValueError:
        print("Response was not valid JSON")
        return jsonify(success=False, results=[])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=7691)
