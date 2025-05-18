import PySimpleGUI as sg
from layouts import *
import functions

window = None
selectedContact = None
onlineUsers = []
contacts = []

class user:
    def __init__(self, name, key):
        self.name = name
        self.key = key
        self.messages = []
        self.pressed = 0

def clearMessages(user):
    for i in range(len(user.messages)):
        window[user.name + str(i) + str(user.pressed)].update(visible = False)
    user.pressed += 1

def formatMessage(message, user, id):
    print(message)
    m = ''
    if message[0] == selectedContact.name:
        m += "me: "
    else:
        m += f"{selectedContact.name}: "
    m += message[1]
    window.extend_layout(window["-CONVO-"], [[sg.Text(
        m, 
        font=messageFont, 
        background_color="white", 
        colors=("black", "white"), 
        pad = (0, 0),
        key = user.name + str(id) + str(user.pressed)
        )]])
    

def formatMessages():
    for i, message in enumerate(selectedContact.messages):
        formatMessage(message, selectedContact, i)
    window["-CONVO-"].contents_changed()
    window.refresh()

def insertUserColumn(key, user):
    window.extend_layout(window[key], [[sg.Text(
        user.name, 
        font=("Arial", 18), 
        background_color="grey", 
        text_color="black", 
        expand_x = True,
        key = user.key,
        enable_events=True,
        
                )
            ]
            ]
        )

def connThread():
    global contacts, onlineUsers
    while True:
        msg = functions.decryptRecv()
        print(msg)
                
        if msg[0] == 1:
            selectedContact.messages = msg[1]
            formatMessages()
        if msg[0] == 2:
            selectedContact.messages.append(msg[1])
            formatMessage(msg[1], selectedContact, len(selectedContact.messages)-1)
            window["-CONVO-"].contents_changed()

        if msg[0] == 3:
            updatedContacts = [user(name, name + "contact") for name in msg[1]]
            for u in updatedContacts:
                if u.name not in [u.name for u in contacts]:
                    insertUserColumn("-CONTACTS-", u)
            contacts = updatedContacts
        
        if msg[0] == 4:
            color = "red"
            message = ""
            if msg[2] == 2:
                message = "User is already a contact"
            elif msg[2] == 1:
                message = "User not found"
            elif msg[2] == 0:
                message = "Contact made with user: " + msg[1]
                color = "green"
            window["-CONTACTERROR-"].update(message)
            window["-CONTACTERROR-"].update(visible = True, text_color = color)

def run():
    global window, selectedContact
    window = sg.Window("Chat app", mainLayout, size=(800,700), finalize=True)
    window.start_thread(lambda: connThread(), ('-THREAD-', '-THREAD ENDED-'))
    window['-INPUT-'].bind("<Return>", "-ENTER-")
    window['-ADDCONTACT-'].bind("<Return>", "-ENTER-")

    functions.encryptSend([2])
    while True:
        event, values = window.read()
        print(event)
        if event == sg.WIN_CLOSED:
            break
        elif event == "-SEND-" and selectedContact != None or event == "-INPUT-" + "-ENTER-" and selectedContact != None:
            window["-INPUT-"].update("")
            functions.encryptSend([0, selectedContact.name, values['-INPUT-']])
        elif event == "-SUBMIT-" or event == "-ADDCONTACT-" + "-ENTER-":
            cname = values["-ADDCONTACT-"]
            functions.encryptSend([3, cname])
            window["-ADDCONTACT-"].update("")
        for c in contacts + onlineUsers:
            if c.name == event.split("contact")[0]:
                if selectedContact == None or selectedContact.name != c.name:
                    if selectedContact != None:
                        clearMessages(selectedContact)
                    selectedContact = c
                    window["-FRAME-"].update(f"Conversation with {selectedContact.name}")
                    functions.encryptSend([1, selectedContact.name])
    window.close()