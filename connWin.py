import PySimpleGUI as sg
from cryptography.fernet import Fernet
from layouts import *
import functions
import socket
import base64
import textWin
import hashlib

server_ip = "10.0.0.185"
server_port = 8000

conn = False
running = True

functions.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def connThread(win):
    global fernet
    while running:
        try:
            functions.s.connect((server_ip, server_port))
            encKey = functions.keyExchange()
            encKey = base64.b64encode(hashlib.sha256(str(encKey).encode()).digest())
            functions.fernet = Fernet(encKey)
            if functions.decryptRecv() == "welcome":
                win.write_event_value(("-THREAD-", "conn"), "conn")
                print("connection established")
                break
        except:
            continue
    
    while running:
        msg = functions.decryptRecv()
        if msg[1] == "Login Success":
                win.write_event_value(("-THREAD-", "logged in"), "logged in")
        if msg[0] == "status":
            print(msg[1])
            if msg[1] == "Login Success":
                break
            elif msg[1] == "Login Failed":
                feedback = "Wrong username or password"
                color = "red"
            elif msg[1] == "Create User Success":
                feedback = "New account created click Log in to log in"
                color = "green"
            elif msg[1] == "Create User Failed":
                feedback = "Username already taken"
                color = "red"
            win["-FEEDBACK-"].update(feedback)
            win["-FEEDBACK-"].update(visible = True, text_color = color)


window = sg.Window("Chat app", layout, finalize=True)
window['-PASSWORD-'].bind("<Return>", "-ENTER-")
window.start_thread(lambda: connThread(window), ('-THREAD-', '-THREAD ENDED-'))

while running:
    event, values = window.read(timeout=10)

    if not conn:
        window['-IMAGE-'].update_animation(gif, time_between_frames=100)

    if event == sg.WIN_CLOSED:
        break
    elif event[0] == "-THREAD-" and event[1] == "conn":
        conn = True
        window["-CONN-"].update(visible = False)
        window["-LOGIN-"].update(visible = True)
    elif event[0] == "-THREAD-" and event[1] == "logged in":
        window.close()
        textWin.run()
        running = False

    elif event == "-LOGIN_BUTTON-" or event == "-PASSWORD-" + "-ENTER-":
        msg = ["login", values["-USERNAME-"], values["-PASSWORD-"]]
        functions.encryptSend(msg)
    elif event == "-CREATE_ACCOUNT-":
        msg = ["Create User", values["-USERNAME-"], values["-PASSWORD-"]]
        functions.encryptSend(msg)

window.close()
