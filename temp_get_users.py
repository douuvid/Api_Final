import sys
sys.path.append('/Users/davidravin/Desktop/Api_Final')
from database.user_database import UserDatabase

db = UserDatabase()
users = db._execute_query('SELECT id, email, first_name, last_name, phone, cv_path, lm_path FROM users ORDER BY id DESC LIMIT 5', fetch='all')
for user in users:
    print(f"ID: {user['id']}, Email: {user['email']}, Téléphone: {user.get('phone', 'Non renseigné')}, CV: {user.get('cv_path', 'Non renseigné')}")
db.close()
