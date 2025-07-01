import sqlite3

connection = sqlite3.connect('database.db')


with open('schema.sql') as f:
    connection.executescript(f.read())

cur = connection.cursor()

# Password = test

cur.execute("INSERT INTO accounts (username, password, email, role) VALUES (?, ?, ?, ?)",
            ('test', '3202e23f8e7b18d17cc05253c0b26d8c0f7fa031', 'test@test.com', 1)
            )

connection.commit()
connection.close()