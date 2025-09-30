# Server Architecture
# The server is responsible for managing all client connections, handling messages, and ensuring concurrent communication.
#
# a) Connection Handling
#
#       - The server listens for incoming client connections on a predefined port.
#       - Each client sends their username upon connecting, allowing the server to track active users.
#       - The server maintains a dictionary of connected clients, mapping usernames to their socket connections.
#
# b) Message Routing
#
#       - The server reads incoming messages and determines whether they are private or group messages.
#       - If a message is private, the server looks up the recipient’s connection and forwards the message.
#       - If a message is for a chat room, the server ensures all members of the room receive the message.
#       - If a message is for creating a chat room, the server appends the chat room name to the list of chat rooms and adds the sender to the list of users for that chat room.
#       - If a message is for joining a chat room, the server updates the list of users for that chat room.
#
# c) Multithreading for Concurrent Clients
#
#       - Each client connection is handled in a separate thread, allowing multiple clients to send and receive messages concurrently.
#       - The server uses a dictionary to track active users and chat rooms, ensuring that messages are routed efficiently.
#
# d) Client Disconnection Handling
#
#       - If a client disconnects, the server:
#
#               i. Removes the client from the active user list.
#               ii. Notifies relevant chat rooms about the user’s departure.
#               iii. Ensures the system continues running smoothly without interruptions.
import socket
import threading
import json

########################################################################################
def message_to_json(status, sender, receiver, message):
    """
    Converts a chat message into a JSON-formatted string.

    Parameters:
        status (str): "private" for direct messages, "group" for chat rooms, "system" for system messages.
        sender (str): The username of the sender.
        receiver (str): The recipient (a username for private chat, a group name for group chat, or "ALL" for broadcasts).
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
def handle_client(client_socket):
    """
    Handles communication with a connected client.

    Parameters:
        client_socket (socket): The socket connected to the client.
        username (str): The username of the connected client.

    Behavior:
        - Stores the client connection.
        - Continuously listens for incoming messages.
        - Parses JSON messages and processes them accordingly.
        - Removes the client from the active list upon disconnection.
        - Broadcasts a system message when the user leaves.
    """
    username = client_socket.recv(1024).decode('utf-8')

    print(f"[NEW CONNECTION] {username} connected.\n")

    with lock:
        clients[username] = client_socket  # Store client socket

    print(f"[ACTIVE CONNECTIONS] {len(clients)}\n")

    try:
        while True:
            message = client_socket.recv(1024).decode('utf-8')
            if not message:
                break  # Client disconnected

            data = json.loads(message)
            process_message(data, username)

    except (ConnectionResetError, BrokenPipeError):
        print(f"[DISCONNECT] {username} has disconnected.\n")

    finally:
        with lock:
            if username in clients:
                del clients[username]
        client_socket.close()
        broadcast_system_message(f"{username} has left the chat.")
########################################################################################

########################################################################################
def process_message(data, sender):
    """
    Processes commands and messages based on the JSON format.

    Parameters:
        data (dict): The parsed JSON message containing status, receiver, and text.
        sender (str): The username of the sender.

    Behavior:
        - Routes the message to the appropriate function based on its status.
        - Handles private messages, group messages, group creation, and group joining.
    """

    status = data["status"] # private or group
    receiver = data["receiver"] # group name or username
    text = data["text"] # the message

    if status == "private":
        send_private_message(sender, receiver, text)
    elif status == "group":
        send_group_message(sender, receiver, text)
    elif status == "create":
        create_group(sender, receiver)  # Receiver is the group name
    elif status == "join":
        join_group(sender, receiver)  # Receiver is the group name
########################################################################################

########################################################################################
def send_private_message(sender, receiver, text):
    """
    Sends a private message to a specific user.

    Parameters:
        sender (str): The username of the sender.
        receiver (str): The username of the recipient.
        text (str): The message content.

    Behavior:
        - Sends the message to the recipient if they are online.
        - Notifies the sender if the recipient is not found.
    """

    with lock:
        if receiver in clients:
            msg_json = message_to_json("private", sender, receiver, text)
            clients[receiver].sendall(msg_json.encode('utf-8'))
        else:
            send_system_message(sender, f"User {receiver} not found.")
########################################################################################

########################################################################################
def send_group_message(sender, group_name, text):
    """
    Sends a message to all members of a group.

    Parameters:
        sender (str): The username of the sender.
        group_name (str): The name of the group.
        text (str): The message content.

    Behavior:
        - Sends the message to all group members, including the sender.
        - Notifies the sender if the group does not exist, or they are not a member.
    """

    with lock:
        if group_name in groups and sender in groups[group_name]:
            msg_json = message_to_json("group", sender, group_name, text)
            for user in groups[group_name]:
                if user != sender and user in clients:
                    clients[user].sendall(msg_json.encode('utf-8'))
        else:
            send_system_message(sender, f"Group {group_name} does not exist or you are not a member.")
########################################################################################

########################################################################################
def create_group(sender, group_name):
    """
    Creates a new group.

    Parameters:
        sender (str): The username of the creator.
        group_name (str): The name of the group.

    Behavior:
        - Creates a new group and adds the sender as the first member.
        - Notifies the sender if the group already exists.
    """

    with lock:
        if group_name not in groups:
            groups[group_name] = [sender]
            send_system_message(sender, f"Group {group_name} created successfully.")
        else:
            send_system_message(sender, f"Group {group_name} already exists.")
########################################################################################

########################################################################################
def join_group(sender, group_name):
    """
    Adds a user to an existing group.

    Parameters:
        sender (str): The username of the user joining the group.
        group_name (str): The name of the group.

    Behavior:
        - Adds the sender to the group if it exists.
        - Notifies the sender if the group does not exist, or they are already a member.
    """

    with lock:
        if group_name in groups:
            if sender not in groups[group_name]:
                groups[group_name].append(sender)
                send_system_message(sender, f"You have joined group {group_name}.")
            else:
                send_system_message(sender, f"You are already in group {group_name}.")
        else:
            send_system_message(sender, f"Group {group_name} does not exist.")
########################################################################################

########################################################################################
def send_system_message(user, message):
    """
    Sends a system notification to a specific user.

    Parameters:
        user (str): The username of the recipient.
        message (str): The system message content.

    Behavior:
        - Sends a message from "SERVER" to the specified user.
        - Does nothing if the user is not online.
    """

    if user in clients:
        msg_json = message_to_json("system", "SERVER", user, message)
        clients[user].sendall(msg_json.encode('utf-8'))
########################################################################################

########################################################################################
def broadcast_system_message(message):
    """
    Broadcasts a system message to all connected users.

    Parameters:
        message (str): The system message content.

    Behavior:
        - Sends the message from "SERVER" to all connected clients.
    """

    msg_json = message_to_json("system", "SERVER", "ALL", message)
    with lock:
        for client in clients.values():
            client.sendall(msg_json.encode('utf-8'))
########################################################################################

########################################################################################
def receive():
    """
    Accepts incoming client connections and starts a new thread for each client.

    Behavior:
        - Waits for a new client to connect.
        - Retrieves the client's username.
        - Starts a thread to handle client communication.
        - Displays the number of active connections.
    """

    while True:
        client_socket, addr = server.accept()

        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        client_thread.start()

########################################################################################

HOST = "127.0.0.1"
PORT = 5000

# Dictionary to store clients: {username: socket}
clients = {}

# Dictionary to store groups {group_name: set(usernames)}
groups = {}

# Used to manage concurrent access to the clients dictionary
lock = threading.Lock()

# Server setup
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST,PORT))
server.listen(50)
print(f"[LISTENING] Server is running on [HOST:{HOST}|PORT:{PORT}]\n")

receive()