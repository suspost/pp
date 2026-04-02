import psycopg2
from connect import connect

def create_table():
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS phonebook (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100),
            phone VARCHAR(20)
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

def insert_contact(name, phone):
    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO phonebook (name, phone) VALUES (%s, %s)", (name, phone))
    conn.commit()
    cur.close()
    conn.close()

def get_contacts():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT * FROM phonebook")
    rows = cur.fetchall()
    for row in rows:
        print(row)
    cur.close()
    conn.close()

def update_contact(name, new_phone):
    conn = connect()
    cur = conn.cursor()
    cur.execute("UPDATE phonebook SET phone=%s WHERE name=%s", (new_phone, name))
    conn.commit()
    cur.close()
    conn.close()

def delete_contact(name):
    conn = connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM phonebook WHERE name=%s", (name,))
    conn.commit()
    cur.close()
    conn.close()

if __name__ == "__main__":
    create_table()
    while True:
        print("\n1. Add contact")
        print("2. Show contacts")
        print("3. Update contact")
        print("4. Delete contact")
        print("5. Exit")
        choice = input("Choose: ")

        if choice == "1":
            name = input("Name: ")
            phone = input("Phone: ")
            insert_contact(name, phone)
        elif choice == "2":
            get_contacts()
        elif choice == "3":
            name = input("Name to update: ")
            phone = input("New phone: ")
            update_contact(name, phone)
        elif choice == "4":
            name = input("Name to delete: ")
            delete_contact(name)
        elif choice == "5":
            break
