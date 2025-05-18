import random
import pickle
from cryptography.fernet import Fernet

s, fernet = None, None

def keyExchange():
    privateKey = random.randint(0, 2**4)
    p, g = pickle.loads(s.recv(1024))
    s.send(pickle.dumps(g**privateKey % p))
    B = pickle.loads(s.recv(1024))
    return B**privateKey % p

def decryptRecv():
    return pickle.loads(fernet.decrypt(s.recv(1024)))

def encryptSend(msg):
    s.send(fernet.encrypt(pickle.dumps(msg)))