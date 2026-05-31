import sqlite3
conn = sqlite3.connect('data/store_intel.db')
cursor = conn.cursor()
print(cursor.execute("SELECT metadata_json FROM events WHERE event_type='EXIT' LIMIT 2").fetchall())
