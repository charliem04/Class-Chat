# Client Architecture
# Each client operates as a standalone application that connects to the server and facilitates bidirectional communication.
#
# a) Connection to the Server
#
#       - The client establishes a TCP connection with the server.
#       - It registers itself with a unique username.
#
# b) Message Handling
#
#       - The client must be able to send messages asynchronously while also listening for incoming messages.
#       - This is achieved using threads:
#
#               i. One thread for sending messages (reads user input and sends it to the server).
#               ii. One thread for receiving messages (continuously listens for messages from the server and displays them).
#
# c) Support for Private and Group Chats
#
#       - Users can send messages in four formats:
#
#               i. Private chat: /private <username> <message> → Sent to a single recipient.
#               ii. Group chat: /group <room_name> <message> → Sent to all users in a chat room.
#               iii. Creating a Group: /create <room_name> → Creates a new group <room_name>.
#               iv. Joining an Existing Group: /join <room_name> → Joins group <room_name>.
#
# d) Handling Server Responses
#
#       - The client processes messages received from the server and displays them accordingly.
#       - If the server returns an error (e.g., recipient not found), the client should notify the user.

import json
import socket
import threading

########################################################################################
def message_to_json(status, sender, receiver, message):
    """
        Converts a chat message into a JSON-formatted string.

        Parameters:
            status (str): "private" for direct messages, "group" for chat rooms.
            sender (str): The username of the sender.
            receiver (str): The recipient (a username for private chat, a group name for group chat).
            message (str): The message content.

        Returns:
            str: JSON-formatted string representing the message.
    """

    msg_data = {
        "status": status,     # "private" for one-to-one chat, "group" for chat room messages.
        "sender": sender,     # The username of the client sending the message.
        "receiver": receiver, # The intended recipient of the message (username for private chat, group name for chat rooms).
        "text": message       # The actual message content.
    }
    return json.dumps(msg_data)
########################################################################################

########################################################################################
def receive_messages(client_socket):
    """
    Continuously listens for incoming messages from the server and displays them.

    Parameters:
        client_socket (socket): The socket connected to the chat server.

    Behavior:
        - Receives JSON messages from the server.
        - Parses messages and prints them in different formats for group and private messages.
        - Handles connection loss by breaking the loop.
    """

    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break

            data = json.loads(message)

            if data['status'] == "group":
                print(f"[GROUP: {data['receiver']} | FROM: {data['sender']}] {data['text']}")
            elif data['status'] == "private":
                print(f"[FROM: {data['sender']}] {data['text']}")
            else:
                print(f"[{data['sender']}] {data['text']}")

        except:
            print("Connection lost")
            break
########################################################################################

########################################################################################
def start_client():
    """
    Initializes and runs the chat client.

    Behavior:
        1. Creates a TCP socket and connects to the server.
        2. Takes user input for a username and sends it to the server.
        3. Starts a thread to receive incoming messages.
        4. Listens for user input commands, formats them as JSON, and sends them to the server.
        5. Supports commands:
            - /private <username> <message> → Sends a private message.
            - /group <room_name> <message> → Sends a group chat message.
            - /create <room_name> → Creates a new group.
            - /join <room_name> → Joins an existing group.
            - /exit → Disconnects the client.
            - /help → Displays a list of commands.
        6. Closes the connection on /exit.
    """
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    print("-------------------------------------------------------------------------------")
    print("                Welcome to the ClassChat Client-Server Program!                ")
    print("-------------------------------------------------------------------------------")
    username = input("Enter your username: ")
    print("-------------------------------------------------------------------------------")

    client.sendall(username.encode('utf-8'))

    receive_thread = threading.Thread(target=receive_messages, args=(client,))
    receive_thread.start()

    print("Type /help to see the list of possible commands.")

    while True:

        message = input("")

        if message.lower() == "/exit":
            client.close()
            break

        command = message.split(" ",2)

        if command[0]=="/private" and len(command) == 3:
            msg_json = message_to_json("private", username, command[1], command[2])
        elif command[0]=="/group" and len(command) == 3:
            msg_json = message_to_json("group", username, command[1], command[2])
        elif command[0]=="/create" and len(command) == 2:
            msg_json = message_to_json("create", username, command[1], "")
        elif command[0]=="/join" and len(command) == 2:
            msg_json = message_to_json("join", username, command[1], "")
        elif command[0]=="/help" and len(command) == 1:
            print_command_list()
            continue
        else:
            print("Invalid Command.\n")
            continue

        client.sendall(msg_json.encode('utf-8'))
########################################################################################

########################################################################################
def print_command_list():
    print("-------------------------------------------------------------------------------")
    print("                         The List of Possible Commands                         ")
    print("-------------------------------------------------------------------------------")
    print("1. Private chat: /private <username> <message> → Sent to a single recipient.")
    print("2. Group chat: /group <room_name> <message> → Sent to all users in a chat room.")
    print("3. Creating a Group: /create <room_name> → Creates a new group <room_name>.")
    print("4. Joining an Existing Group: /join <room_name> → Joins group <room_name>.")
    print("5. Exiting the Server: /exit will disconnect the current user from the server.")
    print("-------------------------------------------------------------------------------")
########################################################################################

HOST = "127.0.0.1"
PORT = 5000

start_client()