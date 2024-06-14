import sqlite3

def replace_link(database_path, table_name, check_list, column_to_check, column_to_replace, replace_value):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    # Convert the check list to a format suitable for SQL IN clause
    check_list_str = ', '.join(f"'{item}'" for item in check_list)

    # Create the SQL query
    sql_query = f"""
    UPDATE {table_name}
    SET {column_to_replace} = ?
    WHERE {column_to_check} IN ({check_list_str})
    """
    
    cursor.execute(sql_query, (replace_value,))
    conn.commit()
    conn.close()

    print(f"{database_path} :: {table_name} column {column_to_replace} replaced to {replace_value}")

database_list = [
    '../databases/cards_faq_ru.db', 
    '../databases/cards_faq_kz.db'
]

card_list = [
    ['BccBlack', 'https://kb.apps.bcc.kz/pages/viewpage.action?pageId=108148595'],
    ['BccPay', 'https://kb.apps.bcc.kz/pages/viewpage.action?pageId=108148661'],
    ['CardCard', 'https://kb.apps.bcc.kz/pages/viewpage.action?pageId=108148624'],
    ['Common', 'https://kb.apps.bcc.kz/pages/viewpage.action?pageId=108148595'],
    ['IronCard', 'https://kb.apps.bcc.kz/pages/viewpage.action?pageId=108149183#expand-012024'],
    ['JuniorBank', 'https://kb.apps.bcc.kz/pages/viewpage.action?pageId=108148697'],
    ['TravelCard', 'https://kb.apps.bcc.kz/pages/viewpage.action?pageId=108148737'],
    ['UlkenKurmet', 'https://kb.apps.bcc.kz/pages/viewpage.action?pageId=108148656']
]

check_list = ['manual', 'history']

for database_path in database_list:
    for table_name, replace_link_value in card_list:
        replace_link(database_path, table_name, check_list, 'data_type', 'link', replace_link_value)
