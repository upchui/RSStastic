import feedparser
import time
import json
import os
from bs4 import BeautifulSoup
import logging
import subprocess

# Configure the logging system
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Read environment variables
feed_url = os.getenv('FEED_URL')
seen_entries_file = os.getenv('SEEN_ENTRIES_FILE', 'seen_entries.json')
meshtastic_host = os.getenv('MESHTASTIC_HOST', '10.14.0.3')
meshtastic_ch_index = os.getenv('MESHTASTIC_CH_INDEX', '0')
send_delay = os.getenv('SEND_DELAY', '10')
demo_mode = os.getenv('DEMOMODE', 'false').lower() == 'true'

def load_seen_entries():
    try:
        with open(seen_entries_file, 'r') as file:
            try:
                seen_entries = json.load(file)
                # Ensure seen_entries is a dictionary
                if not isinstance(seen_entries, dict):
                    logging.warning("Invalid format of seen entries. Initializing as an empty dictionary.")
                    seen_entries = {}
            except json.JSONDecodeError:
                logging.warning("JSON data is empty or malformed. Initializing with an empty dictionary.")
                seen_entries = {}  # Initialize as an empty dictionary
    except FileNotFoundError:
        logging.warning("Seen entries file not found, starting with an empty dictionary.")
        seen_entries = {}  # Initialize as an empty dictionary if file does not exist
    return seen_entries


def save_seen_entries(seen_entries):
    with open(seen_entries_file, 'w') as file:
        json.dump(seen_entries, file)
        logging.info(f"Saved seen entries: {len(seen_entries)}")

def check_for_new_entries(feed, seen_entries):
    new_entries = []
    feed_parsed = feedparser.parse(feed)
    logging.info(f"Checking feed: {feed}")

    for entry in feed_parsed.entries:
        entry_id = entry.id if 'id' in entry else entry.link  # Use link as fallback ID
        if entry_id not in seen_entries:
            new_entries.append(entry)
            seen_entries[entry_id] = True
            logging.info(f"New entry found: {entry.title}")

    return new_entries

def clean_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.get_text()

def send_message(original_message, message_number):
    """Sends a message, splitting it if necessary to comply with size restrictions."""
    max_size = 235
    message_prefix_length = len(f"{message_number}: ")

    if len(original_message.encode('utf-8')) + message_prefix_length <= max_size:
        _send_command(f"{message_number}: {original_message}", message_number)
        message_number += 1
    else:
        # Calculate the maximum length for the text portion of the message
        max_text_length = max_size - message_prefix_length
        parts = split_message(original_message, max_text_length)
        for part in parts:
            _send_command(f"{message_number}: {part}", message_number)
            message_number += 1

    return message_number

def _send_command(message, message_number):
    """Executes the command to send a message, retrying on failure, with a 1-second cooldown between attempts."""
    success = False
    attempts = 0
    while not success:
        if not demo_mode:
            command = f"meshtastic --host {meshtastic_host} --ch-index {meshtastic_ch_index} --sendtext '{message}'"
            try:
                subprocess.run(command, shell=True, check=True)
                logging.info(f"Message {message_number} sent successfully: {message}")
                success = True
            except subprocess.CalledProcessError:
                attempts += 1
                logging.warning(f"Error sending message {message_number}, attempt {attempts}. Retrying...")
        else:
            logging.info(f"Demo mode enabled, message {message_number} not sent: {message}")
            success = True  # In demo mode, treat as if the message was sent successfully.

        if not success or not demo_mode:
            time.sleep(send_delay)  # Wait before retrying or after successful send


def split_message(message, max_size):
    """Splits a message into parts that are equal to or smaller than the maximum size."""
    parts = []
    current_part = ""
    for word in message.split():
        if len((current_part + " " + word).encode('utf-8')) <= max_size:
            current_part += " " + word if current_part else word
        else:
            parts.append(current_part)
            current_part = word
    if current_part:  # Add the last part if it exists
        parts.append(current_part)
    return parts

def process_new_entry(entry):
    logging.info(f"New entry found: {entry.title}")

    # Start numbering at 1
    message_number = 1

    # Send title and link as the first message
    message_number = send_message(f"{entry.title} | More info: {entry.link}", message_number)

    # If a description is available, send it in split messages
    if 'description' in entry:
        clean_description = clean_html(entry.description)
        message_number = send_message(clean_description, message_number)

if feed_url is None:
    logging.error("FEED_URL environment variable is not set.")
else:
    seen_entries = load_seen_entries()

    while True:
        new_entries = check_for_new_entries(feed_url, seen_entries)
        for entry in new_entries:
            process_new_entry(entry)

        save_seen_entries(seen_entries)

        # Wait a while before checking the feed again
        time.sleep(600)  # Wait for 10 minutes
