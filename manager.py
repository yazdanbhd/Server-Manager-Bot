import os
import paramiko
import telegram
import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Replace with your own Telegram bot token
TOKEN = "YOUR_TOKEN"

# Initialize the SSH client
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# Connect to the server using provided credentials
state = None


def start(update, context):
    global state
    state = "CREDENTIALS"
    update.message.reply_text(
        "Please enter server credentials in the following format:\nserver_ip port username password")


def credentials(update, context):
    global state
    if state != "CREDENTIALS":
        return
    try:
        # Parse the server credentials
        credentials = update.message.text.split()
        if len(credentials) != 4:
            update.message.reply_text(
                "Invalid number of credentials provided. Please enter server credentials in the following format:\nserver_ip port username password")
            return
        SERVER = credentials[0]
        PORT = int(credentials[1])
        USERNAME = credentials[2]
        PASSWORD = credentials[3]

        # Connect to the server
        client.connect(SERVER, port=PORT, username=USERNAME, password=PASSWORD)
        update.message.reply_text("Connected to server!")
        state = "CONNECTED"
    except Exception as e:
        update.message.reply_text("Error connecting to server: " + str(e))

logging.basicConfig(filename="bot.log", level=logging.INFO)


def cmd(update, context):
    global state
    if state != "CONNECTED":
        update.message.reply_text("Please connect to a server first using the /start command.")
        return
    command = " ".join(context.args)
    try:
        stdin, stdout, stderr = client.exec_command(command)
        stdout.channel.recv_exit_status()  # wait for command to complete
        output = stdout.read().decode("utf-8")
        update.message.reply_text(output)
        logging.info(f"Command: {command} was executed successfully")
    except Exception as e:
        update.message.reply_text("Error executing command: " + str(e))
        logging.error(f"Error executing command: {command}. Error: {e}")

def stop(update, context):
    global state
    state = None
    update.message.reply_text("Closing connection to server.")
    client.close()


def help(update, context):
    update.message.reply_text(
        "Available commands:\n/start - Connect to a server\n/cmd [command] - Execute command on the server\n\n/stop - Close the connection to the server\n/help - Display this message")


# Create the Updater and pass it your bot's token.
updater = Updater(TOKEN, use_context=True)
updater.dispatcher.add_handler(CommandHandler("start", start))
updater.dispatcher.add_handler(CommandHandler("cmd", cmd))
updater.dispatcher.add_handler(CommandHandler("stop", stop))
updater.dispatcher.add_handler(CommandHandler("help", help))
updater.dispatcher.add_handler(MessageHandler(Filters.text, credentials))

# Start the bot
updater.start_polling()
updater.idle()
