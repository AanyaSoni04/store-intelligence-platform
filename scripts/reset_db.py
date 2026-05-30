import sqlite3
import datetime
import shutil

backup_name = f'data/store_intel_backup_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
shutil.copy('data/store_intel.db', backup_name)

conn = sqlite3.connect('data/store_intel.db')
conn.execute('DELETE FROM events')
conn.execute('DELETE FROM visitors')
conn.commit()
print(f'Database backed up to {backup_name} and truncated.')
