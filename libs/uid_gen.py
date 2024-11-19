import secrets
import string
import time

class UIDGen:
    """UID Generator class that ensures unique identifiers for users"""
    
    def __init__(self, db_wrapper):
        """
        Initializes the UID generator.

        Args:
            db_wrapper (DBWrapper): Instance of the database wrapper.
        """
        self.char_set = string.ascii_letters + string.digits + "!@#$&_"
        self.db_wrapper = db_wrapper
        self._used_uids = set()  # Cache of used UIDs
        self._load_existing_uids()

    def _load_existing_uids(self):
        """Load all existing UIDs from database into cache"""
        users = self.db_wrapper.get_all_users()
        self._used_uids = {user[0] for user in users}

    def uid_exists(self, uid):
        """Check if UID exists in cache or database"""
        if uid in self._used_uids:
            return True
        # Double check with database
        exists = self.db_wrapper.get_user_by_uid(uid) is not None
        if exists:
            self._used_uids.add(uid)
        return exists

    def generate_uid(self, length=8):
        """
        Generate a unique UID with timestamp component for extra uniqueness.

        Args:
            length (int): The length of the UID.

        Returns:
            str: A unique UID.
        """
        while True:
            # Add timestamp component to ensure uniqueness
            timestamp = str(int(time.time()))[-4:]
            random_part = ''.join(secrets.choice(self.char_set) for _ in range(length-4))
            uid = f"{random_part}{timestamp}"
            
            if not self.uid_exists(uid):
                with self.lock:
                    if not self.uid_exists(uid):
                        self._used_uids.add(uid)
                        return uid

# Coded with ❤️ by a3ro-dev