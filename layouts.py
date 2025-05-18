import PySimpleGUI as sg
import json

messageFont = ("Arial", 11)
json_file = open("./assets.json")
assets = json.load(json_file)
json_file.close()
sg.theme("darkblack")

gif = assets['gifs']['connection_loading'].encode()

# Texting window
sidebar = [
    [sg.Column(
        background_color='white',
        expand_y = True,
        layout=[
           [sg.Text("Contacts", font=("Arial", 20), colors=("black", "white"))],
            [sg.HorizontalLine()],
            [sg.Column(
                background_color = 'white',
                expand_y = True,
                expand_x = True,
                layout = [
                    
                ],
                key="-CONTACTS-"
            )],
            [sg.Text("Add new contact", font=("Arial", 18), colors=("black", "white"))],
            [sg.HorizontalLine()],
            [sg.Text("", visible=False, text_color="red", key = "-CONTACTERROR-", background_color="white")],
            [sg.Input(key = "-ADDCONTACT-"), sg.Button(
                    button_text="Submit",
                    key = "-SUBMIT-"
                )]
        ]
    )]
]


mainLayout = [
    [
        sg.Column(sidebar, expand_y=True),
        sg.Column(
            layout=[
                [sg.Frame("Messages", 
                expand_y=True,
                expand_x = True,
                key= "-FRAME-",
                layout=[
                    [sg.Column(
                        background_color = "White",
                        key="-CONVO-",
                        scrollable = True,
                        vertical_scroll_only = True,
                        expand_x = True,
                        expand_y = True,
                        layout=[
                            
                        ]
                    )
                    ]
                ]
                )],
                [sg.Input(expand_x=True, key = "-INPUT-"), sg.Button(
                    button_text="Send",
                    key = "-SEND-",
                )],
            ],
            expand_x=True,
            expand_y=True

        ),
        
    ]
]

# Connect / Login window
loginLayout = [
    [sg.Text("Username")],
    [sg.Input(key = "-USERNAME-")],
    [sg.Text("Password")],
    [sg.Input(key = "-PASSWORD-",password_char="*")],
    [sg.Text(text="Wrong username or password", text_color="red", visible=False, key= "-FEEDBACK-")],
    [sg.Button(button_text="Log in", key = "-LOGIN_BUTTON-"), sg.Button(button_text="Create user", key = "-CREATE_ACCOUNT-")]
]

connectionLayout = [
    [
        sg.Image(data = gif, enable_events = True, key = "-IMAGE-")
    ],
    [
        sg.Push(), sg.Text("Connecting to server..."), sg.Push()
    ]
]

layout = [
    [sg.Column(connectionLayout, key = "-CONN-", visible=True), sg.Column(loginLayout, key = "-LOGIN-", visible=False)]
]