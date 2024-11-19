# db_con.py

import sqlite3
import hashlib
import os
import re
import json
from datetime import datetime
import functools
import threading

class DBWrapper:
    def __init__(self, db_path='db/users.db'):
        self.db_path = db_path
        self.connection = None
        self.lock = threading.Lock()
        self._connect()
        self._create_table()
        self._cache = None
        self._cache_lock = threading.Lock()

    def _connect(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.connection = sqlite3.connect(self.db_path, check_same_thread=False)
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
                updates TEXT,
                transactions TEXT
            )
        ''')
        self.connection.commit()

    def update_certificate_type(self, uid, cert_type):
        with self.lock:
            self.cursor.execute('UPDATE users SET certificate_type = ? WHERE uid = ?', (cert_type, uid))
            self.connection.commit()
            self._cache = None  # Invalidate cache

    def add_update(self, uid, update_text):
        with self.lock:
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
            self._cache = None  # Invalidate cache
        
    def get_all_users(self):
        with self._cache_lock:
            if self._cache is None:
                with self.lock:
                    self.cursor.execute('SELECT * FROM users')
                    self._cache = self.cursor.fetchall()
            return self._cache

    def update_user_field(self, uid, field_name, new_value):
        if field_name not in ['name', 'phone_hash', 'email_hash', 'amount_invested', 'date_of_investment', 'resale_value', 'certificate_type']:
            raise ValueError('Invalid field name')
        with self.lock:
            # Use parameterized query to prevent SQL injection
            self.cursor.execute(f'UPDATE users SET {field_name} = ? WHERE uid = ?', (new_value, uid))
            self.connection.commit()
            self._cache = None  # Invalidate cache

    def delete_user(self, uid):
        with self.lock:
            self.cursor.execute('DELETE FROM users WHERE uid = ?', (uid,))
            self.connection.commit()
            self._cache = None  # Invalidate cache

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
        with self.lock:
            if amount_invested % 500 != 0:
                raise ValueError('Amount invested must be in multiples of 500.')
            
            self._validate_email(email)
            phone_hash = self._hash_data(phone_number)
            email_hash = self._hash_data(email) if email else None
            
            self.cursor.execute('''
                INSERT INTO users (uid, name, phone_hash, email_hash, amount_invested, date_of_investment, resale_value, transactions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (uid, name, phone_hash, email_hash, amount_invested, date_of_investment, resale_value, '[]'))
            self.connection.commit()
            self._cache = None  # Invalidate cache

    def update_email(self, uid, new_email):
        with self.lock:
            self._validate_email(new_email)
            email_hash = self._hash_data(new_email) if new_email else None
            self.cursor.execute('UPDATE users SET email_hash = ? WHERE uid = ?', (email_hash, uid))
            self.connection.commit()
            self._cache = None  # Invalidate cache

    def get_user_by_uid(self, uid):
        self.cursor.execute('SELECT * FROM users WHERE uid = ?', (uid,))
        return self.cursor.fetchone()

    def update_investment(self, uid, new_amount_invested, new_resale_value):
        with self.lock:
            self.cursor.execute('''
                UPDATE users SET amount_invested = ?, resale_value = ? WHERE uid = ?
            ''', (new_amount_invested, new_resale_value, uid))
            self.connection.commit()
            self._cache = None  # Invalidate cache

    def add_transaction(self, uid, transaction_type, amount, details):
        with self.lock:
            current_time = datetime.now().isoformat()
            self.cursor.execute('SELECT transactions FROM users WHERE uid = ?', (uid,))
            result = self.cursor.fetchone()
            if result and result[0]:
                transactions = json.loads(result[0])
            else:
                transactions = []

            transactions.append({
                'timestamp': current_time,
                'type': transaction_type,
                'amount': amount,
                'details': details
            })

            self.cursor.execute('UPDATE users SET transactions = ? WHERE uid = ?', 
                                (json.dumps(transactions), uid))
            self.connection.commit()
            self._cache = None  # Invalidate cache

    def get_transactions(self, uid):
        self.cursor.execute('SELECT transactions FROM users WHERE uid = ?', (uid,))
        result = self.cursor.fetchone()
        return json.loads(result[0]) if result and result[0] else []

    def close(self):
        self.connection.close()