import socket
from multiprocessing import Process, Pipe
import sqlite3
import pickle
import hashlib
import base64
import hashlib
import random
from math import gcd as bltin_gcd
from cryptography.fernet import Fernet, InvalidToken

p = 397

def get_db(return_conn = False):
    conn = sqlite3.connect("database.db")
    if not return_conn: 
        return conn.cursor()
    else: 
        return conn.cursor(), conn

def primRoots(modulo):
    required_set = {num for num in range(1, modulo) if bltin_gcd(num, modulo) }
    return [g for g in range(1, modulo) if required_set == {pow(g, powers, modulo)
            for powers in range(1, modulo)}]

g = random.choice(primRoots(p))
    
def keyExchange(s):
    privateKey = random.randint(0, 2**4)
    s.send(pickle.dumps([p, g]))
    A = pickle.loads(s.recv(1024))
    s.send(pickle.dumps(g**privateKey % p))
    return A**privateKey % p

class client:
    def __init__(self, socket, process, pipe):
        self.socket = socket
        self.logged_in = False
        self.name = None
        self.process = process
        self.pipe = pipe
        self.fernet = None

def encryptSend(socket, fernet, msg):
    socket.send(fernet.encrypt(pickle.dumps(msg)))

def decryptRecv(socket, fernet):
    return pickle.loads(fernet.decrypt(socket.recv(1024)))

def updateContacts(socket, fernet, name):
    cur = get_db()
    resp = cur.execute("SELECT * FROM CONTACTS WHERE USER1 = ? UNION SELECT * FROM CONTACTS WHERE USER2 = ?", (name, name)).fetchall()

    contacts = []
    for i in resp:
        for j in i:
            if j != name:
                contacts.append(j)

    encryptSend(socket, fernet, [3, contacts])
    
def startClient(clientSocket, pipe):
    # Set up symmetric key with client
    encKey = keyExchange(clientSocket)
    encKey = base64.b64encode(hashlib.sha256(str(encKey).encode()).digest()) # at hashe og derefter konvertere det til b64 key fra key exchange giver det præcist rette format til fernet encryption key
    fernet = Fernet(encKey)
    pipe.send([3, fernet])

    # Tell the client that it has been connected to the server
    encryptSend(clientSocket, fernet, "welcome")

    logged_in = False

    while not logged_in:
        try:
            msg = decryptRecv(clientSocket, fernet)
        except ConnectionResetError: # These errors occur when client has disconnected
            logged_in = False
            break
        except InvalidToken:
            logged_in = False
            break
        

        if msg[0] == "login":
            cur = get_db()
            resp = cur.execute("SELECT * FROM User WHERE Username = ?", (msg[1],)).fetchone()
            hashedPw = hashlib.sha256(msg[2].encode()).hexdigest()
            if resp != None and resp[1] == hashedPw:
                print(msg[1], "logged in")
                name = msg[1]
                pipe.send([0, msg[1]])
                encryptSend(clientSocket, fernet, ["status", "Login Success"])
                logged_in = True
            else:
                encryptSend(clientSocket, fernet, ["status", "Login Failed"])

        if msg[0] == "Create User":
            cur, conn = get_db(return_conn=True)
            if cur.execute("SELECT * FROM User WHERE Username = ?", (msg[1],)).fetchone() == None:
                hashedPw = hashlib.sha256(msg[2].encode()).hexdigest()
                resp = cur.execute("INSERT INTO USER VALUES(?, ?)", (msg[1], hashedPw))
                conn.commit()
                encryptSend(clientSocket, fernet, ["status", "Create User Success"])
            else:
                encryptSend(clientSocket, fernet, ["status", "Create User Failed"])
        
    while logged_in:
        try:
            msg = decryptRecv(clientSocket, fernet)
        except ConnectionResetError: # These errors occur when client has disconnected
            break
        except InvalidToken:
            break
        
        if msg[0] == 0:
            cur, conn = get_db(return_conn=True)
            cur.execute("INSERT INTO MESSAGE (USER_NAME, RECEIVER_NAME, CONTENT) VALUES(?, ?, ?)", (name, msg[1], msg[2]))
            conn.commit()
            resp = cur.execute("SELECT * FROM MESSAGE WHERE ID=?", (cur.lastrowid,)).fetchone()
            print(resp)
            pipe.send([4, [resp[2], resp[3], resp[4]]])
        elif msg[0] == 1:
            contact = msg[1]
            cur = get_db()
            resp = cur.execute("SELECT * FROM MESSAGE WHERE USER_NAME = ? AND RECEIVER_NAME = ? UNION SELECT * FROM MESSAGE WHERE USER_NAME = ? AND RECEIVER_NAME = ? ORDER BY timestamp DESC", (contact, name, name, contact)).fetchall()

            msgs = [[m[1],m[3], m[4]] for m in resp[:5]]
            msgs.reverse()
            encryptSend(
                clientSocket, fernet, [1, msgs]
            )
        elif msg[0] == 2:
            updateContacts(clientSocket, fernet, name)

        elif msg[0] == 3:
            cname = msg[1]
            print(name, "wanted to add", cname)
            cur, conn = get_db(return_conn=True)
            resp = cur.execute("SELECT * FROM USER WHERE USERNAME = ?", (cname, )).fetchone()
            if resp != None:
                if cur.execute("SELECT * FROM CONTACTS WHERE USER1 = ? AND USER2 = ? UNION SELECT * FROM CONTACTS WHERE USER1 = ? AND USER2 = ?", (name, cname, cname, name)).fetchone() == None:
                    encryptSend(clientSocket, fernet, [4, cname, 0])
                    cur.execute("INSERT INTO CONTACTS (USER1, USER2) VALUES (?, ?)", (cname, name))
                    conn.commit()
                    updateContacts(clientSocket, fernet, name)
                else:
                    encryptSend(clientSocket, fernet, [4, cname, 2])
            else:
                encryptSend(clientSocket, fernet, [4, cname, 1])
        print(msg)
    pipe.send([1])
                
def recvClients(socket, pipe):
    while True:
        socket.listen(0)
        client_socket, client_address = socket.accept()
        print("new client from the address", client_address[0])
        pipe.send([0, client_socket])
                  
 

class server:
    def __init__(self):
        self.ip = "10.0.0.185"
        self.port = 8000
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.ip, self.port))
        self.clients = []
        self.clientPipes = []
        self.processes = []
    
    def run(self):
        clientRecvPipe, childPipe = Pipe(duplex=True)
        self.recvClientsProcess = Process(target= recvClients, args =(self.sock, childPipe))
        self.recvClientsProcess.start()
        self.processes.append(self.recvClientsProcess)

        while True:
            if clientRecvPipe.poll():
                msg = clientRecvPipe.recv()
                if msg[0] == 0: # 0 means new client has connected to the server
                    s = msg[1]
                    clientPipe, childPipe = Pipe()
                    p = Process(target = startClient, args = (s, childPipe))
                    c = client(s, p, clientPipe)
                    self.clients.append(c)
                    p.start()

            for c in self.clients:
                if c.pipe.poll():
                    msg = c.pipe.recv()
                    if msg[0] == 0: # Hvis klient har logget ind
                        c.logged_in = True
                        c.name = msg[1]
                    elif msg[0] == 1: # Hvis klient har lukket forbindelsen
                        c.closed = True
                        c.socket.close()
                        c.process.terminate()
                        print(c.name, "disconnected")
                        self.clients.remove(c) # could give some issues
                    elif msg[0] == 3: # Når key exchange er sket bliver fernet sendt til main process
                        c.fernet = msg[1]
                    elif msg[0] == 4: # Når klient sender en besked bliver det sendt til begge parter af main process
                        send = msg.copy()
                        send[0] = 2
                        send[1][0] = msg[1][0]
                        for i in self.clients:
                            if i.name == msg[1][0]:
                                encryptSend(i.socket, i.fernet, send)
                        encryptSend(c.socket, c.fernet, send)
                        print(send, "message sent")

    def shutdown(self):
        self.recvClientsProcess.terminate()
        for c in self.clients:
            c.socket.close()
            c.process.terminate()
        self.sock.close()

if __name__ == "__main__":
    s = server()
    try:
        s.run()
    except KeyboardInterrupt:
        print("SHUTTING DOWN")
        s.shutdown()
        