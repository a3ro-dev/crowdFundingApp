import sqlite3
import hashlib
import os
import re
import json
from datetime import datetime

class DBWrapper:
    def __init__(self, db_path='db/users.db'):
        self.db_path = db_path
        self.connection = None
        self._connect()
        self._create_table()

    def _connect(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()

    def _create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                uid TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                phone_hash TEXT NOT NULL,
                email_hash TEXT,
                amount_invested INTEGER NOT NULL,
                date_of_investment TEXT NOT NULL,
                resale_value REAL,
                certificate_type TEXT,
                updates TEXT
            )
        ''')
        self.connection.commit()

    def update_certificate_type(self, uid, cert_type):
        self.cursor.execute('UPDATE users SET certificate_type = ? WHERE uid = ?', (cert_type, uid))
        self.connection.commit()

    def add_update(self, uid, update_text):
        current_time = datetime.now().isoformat()
        self.cursor.execute('SELECT updates FROM users WHERE uid = ?', (uid,))
        result = self.cursor.fetchone()
        
        if result and result[0]:
            updates = json.loads(result[0])
        else:
            updates = []
            
        updates.append({
            'timestamp': current_time,
            'update': update_text
        })
        
        self.cursor.execute('UPDATE users SET updates = ? WHERE uid = ?', 
                          (json.dumps(updates), uid))
        self.connection.commit()

    def get_updates(self, uid):
        self.cursor.execute('SELECT updates FROM users WHERE uid = ?', (uid,))
        result = self.cursor.fetchone()
        return json.loads(result[0]) if result and result[0] else []

    def _hash_data(self, data):
        return hashlib.sha256(str(data).encode('utf-8')).hexdigest()

    def _validate_email(self, email):
        if email:
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, email):
                raise ValueError('Invalid email format')
        return True

    def add_user(self, uid, name, phone_number, amount_invested, date_of_investment, email=None, resale_value=None):
        if amount_invested % 500 != 0:
            raise ValueError('Amount invested must be in multiples of 500.')
        
        self._validate_email(email)
        phone_hash = self._hash_data(phone_number)
        email_hash = self._hash_data(email) if email else None
        
        self.cursor.execute('''
            INSERT INTO users (uid, name, phone_hash, email_hash, amount_invested, date_of_investment, resale_value)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (uid, name, phone_hash, email_hash, amount_invested, date_of_investment, resale_value))
        self.connection.commit()

    def update_email(self, uid, new_email):
        self._validate_email(new_email)
        email_hash = self._hash_data(new_email) if new_email else None
        self.cursor.execute('UPDATE users SET email_hash = ? WHERE uid = ?', (email_hash, uid))
        self.connection.commit()

    def get_user_by_uid(self, uid):
        self.cursor.execute('SELECT * FROM users WHERE uid = ?', (uid,))
        return self.cursor.fetchone()

    def update_resale_value(self, uid, resale_value):
        self.cursor.execute('UPDATE users SET resale_value = ? WHERE uid = ?', (resale_value, uid))
        self.connection.commit()

    def close(self):
        self.connection.close()