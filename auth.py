import json
import hashlib

USERS_FILE = "users.json"

def hash_sifre(sifre):
    return hashlib.sha256(sifre.encode()).hexdigest()

def kullanici_var_mi(username):
    try:
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
        return username in users
    except:
        return False

def dogrula(username, sifre):
    try:
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
        hashed = hash_sifre(sifre)
        return users.get(username) == hashed
    except:
        return False

def kayit_ol(username, sifre):
    try:
        with open("users.json", "r") as f:
            users = json.load(f)
    except:
        users = {}

    if username in users:
        return False

    hashed = hashlib.sha256(sifre.encode()).hexdigest()
    users[username] = hashed

    with open("users.json", "w") as f:
        json.dump(users, f, indent=4)

    return True

