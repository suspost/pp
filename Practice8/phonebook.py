import psycopg2

conn = psycopg2.connect(
    dbname="phonebook",
    user="postgres",
    password="your_password",
    host="localhost",
    port="5432"
)

cur = conn.cursor()

# Example calls
cur.execute("SELECT * FROM get_contacts_by_pattern(%s)", ('Ali',))
print(cur.fetchall())

cur.execute("CALL upsert_contact(%s, %s)", ('John', '123456789'))
conn.commit()

cur.execute("CALL delete_contact(%s)", ('John',))
conn.commit()

cur.close()
conn.close()
