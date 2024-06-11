import requests

# Set up the login URL and credentials
login_url = 'http://localhost:7691/login'
alter_tables_url = 'http://localhost:7691/alter_tables'
credentials = {'login': 'abylai', 'password': '004973'}

# Create a session to persist cookies
session = requests.Session()

# Perform login
response = session.post(login_url, data=credentials)
if response.status_code == 200:
    print("Login successful")

    # Make the POST request to /alter_tables
    response = session.post(alter_tables_url)
    if response.status_code == 200:
        print("Tables altered successfully")
    else:
        print(f"Failed to alter tables: {response.text}")
else:
    print("Login failed")
