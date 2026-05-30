import sqlite3

def query():
    conn = sqlite3.connect('data/store_intel.db')
    cursor = conn.cursor()
    print("Database Events:")
    for row in cursor.execute("SELECT camera_id, event_type, COUNT(*) FROM events GROUP BY camera_id, event_type"):
        print(f"  {row[0]} - {row[1]}: {row[2]}")

    print("\nSample CAM5 events:")
    for row in cursor.execute("SELECT * FROM events WHERE camera_id='CAM5' LIMIT 10"):
        print(f"  {row}")

if __name__ == "__main__":
    query()
