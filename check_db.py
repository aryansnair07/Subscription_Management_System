
import sqlite3

conn = sqlite3.connect("subscriptions.db")
tables = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
).fetchall()

print("Tables found in database:")
for table in tables:
    print(table[0])

conn.close()
