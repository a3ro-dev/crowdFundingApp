import secrets
import string

class UIDGen:
    def __init__(self, db_wrapper):
        self.char_set = string.ascii_letters + string.digits + "!@#$&_"
        self.db_wrapper = db_wrapper

    def uid_exists(self, uid):
        user = self.db_wrapper.get_user_by_uid(uid)
        return user is not None

    def generate_uid(self, length=6):
        while True:
            uid = ''.join(secrets.choice(self.char_set) for _ in range(length))
            if not self.uid_exists(uid):
                return uid

# # Example usage
# if __name__ == "__main__":
#     db_wrapper = DBWrapper()
#     uid_gen = UIDGen(db_wrapper)
#     new_uid = uid_gen.generate_uid()
#     print(f"Generated UID: {new_uid}")
#     db_wrapper.close()