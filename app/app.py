from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from db_utils import (
    get_table_names, get_table_content, update_cell, delete_row, 
    create_backup, get_backups, get_backup_content, restore_backup, 
    insert_data_into_table, get_last_row_id, add_columns_to_tables
)
from users import create_table, add_user, get_user_by_id, get_all_users, update_user, delete_user, get_user_by_login
from config import DATABASES, BACKUP_DATABASES
import requests
import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'your_secret_key12'

@app.route('/')
def index():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', role=session['role'], login=session['login'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        user = get_user_by_login(login)

        if user and user['password'].strip() == password.strip():
            print("LOGGED")
            session['logged_in'] = True
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['login'] = user['login']
            if user['role'] == 'admin':
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('index'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin')
def admin():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    if session['role'] != 'admin':
        return redirect(url_for('index'))
    users = get_all_users()
    return render_template('admin.html', users=users, role=session['role'], login=session['login'])

@app.route('/profile')
def profile():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return render_template('profile.html', login=session['login'], role=session['role'])

@app.route('/add_user', methods=['POST'])
def add_user_route():
    if 'logged_in' not in session or session['role'] != 'admin':
        return jsonify(success=False, message="Unauthorized"), 403
    data = request.get_json()
    login = data['login']
    role = data['role']
    try:
        add_user(login, role)
        return jsonify(success=True, message="User added successfully")
    except Exception as e:
        return jsonify(success=False, message=str(e))

@app.route('/update_user', methods=['POST'])
def update_user_route():
    if 'logged_in' not in session or session['role'] != 'admin':
        return jsonify(success=False, message="Unauthorized"), 403
    data = request.get_json()
    user_id = data['id']
    login = data.get('login')
    role = data.get('role')
    try:
        update_user(user_id, login, role)
        return jsonify(success=True, message="User updated successfully")
    except Exception as e:
        return jsonify(success=False, message=str(e))

@app.route('/delete_user', methods=['POST'])
def delete_user_route():
    if 'logged_in' not in session or session['role'] != 'admin':
        return jsonify(success=False, message="Unauthorized"), 403
    data = request.get_json()
    user_id = data['id']
    try:
        delete_user(user_id)
        return jsonify(success=True, message="User deleted successfully")
    except Exception as e:
        return jsonify(success=False, message=str(e))

@app.route('/get_tables', methods=['POST'])
def get_tables():
    if 'logged_in' not in session:
        return jsonify(success=False, message="Unauthorized"), 403
    data = request.get_json()
    language = data.get('language')
    database = DATABASES[language]
    tables = get_table_names(database)
    return jsonify(tables)

@app.route('/get_table_content', methods=['POST'])
def get_table_content_route():
    if 'logged_in' not in session:
        return jsonify(success=False, message="Unauthorized"), 403
    data = request.get_json()
    language = data.get('language')
    table = data.get('table')
    database = DATABASES[language]
    columns, content = get_table_content(database, table)
    return jsonify({'columns': columns, 'content': content})

@app.route('/update_cell', methods=['POST'])
def update_cell_route():
    if 'logged_in' not in session or session['role'] == 'viewer':
        return jsonify(success=False, message="Unauthorized"), 403
    data = request.get_json()
    language = data.get('language')
    table = data.get('table')
    column = data.get('column')
    row_id = data.get('row_id')
    new_value = data.get('new_value')
    database = DATABASES[language]
    try:
        create_backup(language, table)
        update_cell(database, table, column, row_id, new_value)
        return jsonify(success=True, message="Cell updated successfully")
    except Exception as e:
        return jsonify(success=False, message=str(e))

@app.route('/delete_row', methods=['POST'])
def delete_row_route():
    if 'logged_in' not in session or session['role'] == 'viewer':
        return jsonify(success=False, message="Unauthorized"), 403
    data = request.get_json()
    language = data.get('language')
    table = data.get('table')
    row_id = data.get('row_id')
    database = DATABASES[language]
    try:
        create_backup(language, table)
        success = delete_row(database, table, row_id)
        return jsonify(success=success, message="Row deleted successfully")
    except Exception as e:
        return jsonify(success=False, message=str(e))

@app.route('/get_backups', methods=['POST'])
def get_backups_route():
    if 'logged_in' not in session:
        return jsonify(success=False, message="Unauthorized"), 403
    data = request.get_json()
    language = data.get('language')
    table = data.get('table')
    database = BACKUP_DATABASES[language]
    backups = get_backups(database, table)
    return jsonify(backups)

@app.route('/get_backup_content', methods=['POST'])
def get_backup_content_route():
    if 'logged_in' not in session:
        return jsonify(success=False, message="Unauthorized"), 403
    data = request.get_json()
    language = data.get('language')
    table = data.get('table')
    backup = data.get('backup')
    database = BACKUP_DATABASES[language]
    columns, content = get_backup_content(database, backup)
    return jsonify({'columns': columns, 'content': content})

@app.route('/restore_backup', methods=['POST'])
def restore_backup_route():
    if 'logged_in' not in session or session['role'] == 'viewer':
        return jsonify(success=False, message="Unauthorized"), 403
    data = request.get_json()
    language = data.get('language')
    table = data.get('table')
    backup = data.get('backup')
    try:
        restore_backup(language, table, backup)
        return jsonify(success=True, message="Backup restored successfully")
    except Exception as e:
        return jsonify(success=False, message=str(e))

@app.route('/insert_data', methods=['POST'])
def insert_data_route():
    if 'logged_in' not in session or session['role'] == 'viewer':
        return jsonify(success=False, message="Unauthorized"), 403
    data = request.get_json()
    language = data.get('language')
    table = data.get('table')
    new_data = data.get('data')
    database = DATABASES[language]
    try:
        create_backup(language, table)
        duplicate_found = insert_data_into_table(database, table, new_data)
        return jsonify(success=True, duplicate=duplicate_found, message="Data inserted successfully")
    except Exception as e:
        return jsonify(success=False, message=str(e))

@app.route('/get_last_row_id', methods=['POST'])
def get_last_row_id_route():
    if 'logged_in' not in session:
        return jsonify(success=False, message="Unauthorized"), 403
    data = request.get_json()
    language = data.get('language')
    table = data.get('table')
    database = DATABASES[language]
    last_row_id = get_last_row_id(database, table)
    return jsonify(last_row_id=last_row_id)

@app.route('/insert_json', methods=['POST'])
def insert_json_route():
    if 'logged_in' not in session or session['role'] == 'viewer':
        return jsonify(success=False, message="Unauthorized"), 403
    data = request.get_json()
    language = data.get('language')
    table = data.get('table')
    json_data = data.get('data')
    database = DATABASES[language]
    try:
        create_backup(language, table)
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
        return jsonify(success=True, duplicate=duplicate_found, message="JSON data inserted successfully")
    except Exception as e:
        return jsonify(success=False, message=str(e))

@app.route('/search', methods=['POST'])
def search_route():
    if 'logged_in' not in session:
        return jsonify(success=False, message="Unauthorized"), 403
    data = request.get_json()
    query = data.get('query')
    table_type = data.get('table_type')
    if not query:
        return jsonify(success=False, results=[], message="Empty query")
    url = 'http://10.15.132.126:6789/post'
    search_data = {
        "query": query,
        "table_type": table_type
    }
    try:
        response = requests.post(url, json=search_data)
        response.raise_for_status()
        search_results = response.json()
        if search_results:
            return jsonify(success=True, results=search_results, message="Search completed successfully")
        else:
            return jsonify(success=False, results=[], message="No results found")
    except requests.exceptions.RequestException as e:
        return jsonify(success=False, results=[], message=f"Request failed: {e}")
    except ValueError:
        return jsonify(success=False, results=[], message="Response was not valid JSON")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=7691)
