from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from db_utils import (
    get_table_names, get_table_content, update_cell, delete_row, 
    create_backup, get_backups, get_backup_content, restore_backup, 
    insert_data_into_table, get_last_row_id
)
from users import create_table, add_user, get_user_by_id, get_all_users, update_user, delete_user, get_user_by_login
from config import DATABASES, BACKUP_DATABASES
import requests
import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')

create_table()
app.secret_key = 'your_secret_key12'

add_user('abylai', 'admin')

# Routes
@app.route('/')
def index():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    user = get_user_by_id(session['user_id'])
    return render_template('index.html', role=session['role'], user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        user = get_user_by_login(login)

        if user and user['password'].strip() == password.strip():
            session['logged_in'] = True
            session['user_id'] = user['id']
            session['role'] = user['role']
            if user['role'] == 'admin':
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('index'))
        return 'Invalid credentials'
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
    user = get_user_by_id(session['user_id'])
    users = get_all_users()
    return render_template('admin.html', users=users, user=user)

@app.route('/add_user', methods=['POST'])   
def add_user_route():
    if 'logged_in' not in session or session['role'] != 'admin':
        return jsonify(success=False, message="Unauthorized"), 403
    data = request.get_json()
    login = data['login']
    role = data['role']
    add_user(login, role)
    return jsonify(success=True)

@app.route('/update_user', methods=['POST'])
def update_user_route():
    if 'logged_in' not in session or session['role'] != 'admin':
        return jsonify(success=False, message="Unauthorized"), 403
    data = request.get_json()
    user_id = data['id']
    login = data.get('login')
    role = data.get('role')
    update_user(user_id, login, role)
    return jsonify(success=True)

@app.route('/delete_user', methods=['POST'])
def delete_user_route():
    if 'logged_in' not in session or session['role'] != 'admin':
        return jsonify(success=False, message="Unauthorized"), 403
    data = request.get_json()
    user_id = data['id']
    delete_user(user_id)
    return jsonify(success=True)

@app.route('/get_tables', methods=['POST'])
def get_tables():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    data = request.get_json()
    language = data.get('language')
    database = DATABASES[language]
    tables = get_table_names(database)
    return jsonify(tables)

@app.route('/get_table_content', methods=['POST'])
def get_table_content_route():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
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
    user_id = session['user_id']
    user = get_user_by_id(user_id)  # Fetch the user details
    username = user['login']  # Extract the username from the user details
    create_backup(language, table, username)
    update_cell(database, table, column, row_id, new_value)
    return jsonify(success=True)

@app.route('/delete_row', methods=['POST'])
def delete_row_route():
    if 'logged_in' not in session or session['role'] == 'viewer':
        return jsonify(success=False, message="Unauthorized"), 403
    data = request.get_json()
    language = data.get('language')
    table = data.get('table')
    row_id = data.get('row_id')
    user_id = session['user_id']
    user = get_user_by_id(user_id)  # Fetch the user details
    username = user['login']  # Extract the username from the user details
    create_backup(language, table, username)
    success = delete_row(DATABASES[language], table, row_id)
    return jsonify(success=success)

@app.route('/get_backups', methods=['POST'])
def get_backups_route():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    data = request.get_json()
    language = data.get('language')
    table = data.get('table')
    database = BACKUP_DATABASES[language]
    backups = get_backups(database, table)
    return jsonify(backups)

@app.route('/get_backup_content', methods=['POST'])
def get_backup_content_route():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
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
    restore_backup(language, table, backup)
    return jsonify(success=True)

@app.route('/insert_data', methods=['POST'])
def insert_data_route():
    if 'logged_in' not in session or session['role'] == 'viewer':
        return jsonify(success=False, message="Unauthorized"), 403
    try:
        data = request.get_json()
        language = data.get('language')
        table = data.get('table')
        new_data = data.get('data')
        user_id = session['user_id']
        user = get_user_by_id(user_id)  # Fetch the user details
        username = user['login']  # Extract the username from the user details
        create_backup(language, table, username)
        duplicate_found = insert_data_into_table(DATABASES[language], table, new_data, author=username)
        return jsonify(success=True, duplicate=duplicate_found)
    except Exception as e:
        print(f"Error inserting data: {e}")
        return jsonify(success=False, message=str(e)), 500

@app.route('/get_user_info', methods=['GET'])
def get_user_info():
    if 'logged_in' not in session:
        return jsonify(success=False), 403
    user_id = session['user_id']
    user = get_user_by_id(user_id)
    return jsonify(success=True, user=user)

@app.route('/get_last_row_id', methods=['POST'])
def get_last_row_id_route():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
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

    user_id = session['user_id']
    user = get_user_by_id(user_id)  # Fetch the user details
    username = user['login']  # Extract the username from the user details

    create_backup(language, table, username)

    valid_entries_kz = []
    valid_entries_ru = []
    duplicate_found = False

    for entry in json_data:
        if 'question_kz' in entry and 'answer_kz' in entry:
            valid_entries_kz.append({
                'question': entry['question_kz'],
                'answer': entry['answer_kz'],
                'data_type': entry.get('type', 'manual'),
                'date': entry.get('date', '0000y00m00d_00h00m00s'),
                'link': entry.get('link', 'https://www.bcc.kz/')
            })
        if 'question_ru' in entry and 'answer_ru' in entry:
            valid_entries_ru.append({
                'question': entry['question_ru'],
                'answer': entry['answer_ru'],
                'data_type': entry.get('type', 'manual'),
                'date': entry.get('date', '0000y00m00d_00h00m00s'),
                'link': entry.get('link', 'https://www.bcc.kz/')
            })

    if valid_entries_kz:
        duplicate_found_kz = insert_data_into_table(DATABASES['kazakh'], table, valid_entries_kz)
    if valid_entries_ru:
        duplicate_found_ru = insert_data_into_table(DATABASES['russian'], table, valid_entries_ru)

    duplicate_found = duplicate_found_kz or duplicate_found_ru
    
    return jsonify(success=True, duplicate=duplicate_found)



@app.route('/search', methods=['POST'])
def search_route():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
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
        response.raise_for_status()
        search_results = response.json()

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
