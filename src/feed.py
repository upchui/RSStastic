import feedparser
import time
import json
import os
from bs4 import BeautifulSoup
import logging
import subprocess

# Konfiguriere das Logging-System
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Lese Umgebungsvariablen
feed_url = os.getenv('FEED_URL')
seen_entries_file = os.getenv('SEEN_ENTRIES_FILE', 'seen_entries.json')
meshtastic_host = os.getenv('MESHTASTIC_HOST', '10.14.0.3')
meshtastic_ch_index = os.getenv('MESHTASTIC_CH_INDEX', '0')
demo_mode = os.getenv('DEMOMODE', 'false').lower() == 'true'

def load_seen_entries():
    try:
        with open(seen_entries_file, 'r') as file:
            try:
                seen_entries = json.load(file)
                # Stelle sicher, dass seen_entries ein Dictionary ist
                if not isinstance(seen_entries, dict):
                    logging.warning("Invalid format of seen entries. Initializing as an empty dictionary.")
                    seen_entries = {}
            except json.JSONDecodeError:
                logging.warning("JSON data is empty or malformed. Initializing with an empty dictionary.")
                seen_entries = {}  # Initialisiere als leeres Dictionary
    except FileNotFoundError:
        logging.warning("Seen entries file not found, starting with an empty dictionary.")
        seen_entries = {}  # Initialisiere als leeres Dictionary bei Nichtexistenz der Datei
    return seen_entries


def save_seen_entries(seen_entries):
    with open(seen_entries_file, 'w') as file:
        json.dump(seen_entries, file)
        logging.info(f"Gespeicherte gesehene Einträge: {len(seen_entries)}")

def check_for_new_entries(feed, seen_entries):
    new_entries = []
    feed_parsed = feedparser.parse(feed)
    logging.info(f"Überprüfe Feed: {feed}")

    for entry in feed_parsed.entries:
        entry_id = entry.id if 'id' in entry else entry.link  # Benutze Link als Fallback-ID
        if entry_id not in seen_entries:
            new_entries.append(entry)
            seen_entries[entry_id] = True
            logging.info(f"Neuer Eintrag gefunden: {entry.title}")

    return new_entries

def clean_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    return soup.get_text()

def send_message(original_message, message_number):
    """Sendet eine Nachricht, teilt sie bei Bedarf auf, um die Größenbeschränkung einzuhalten."""
    max_size = 235
    message_prefix_length = len(f"{message_number}: ")

    if len(original_message.encode('utf-8')) + message_prefix_length <= max_size:
        _send_command(f"{message_number}: {original_message}", message_number)
        message_number += 1
    else:
        # Berechne die maximale Länge für den Textteil der Nachricht
        max_text_length = max_size - message_prefix_length
        parts = split_message(original_message, max_text_length)
        for part in parts:
            _send_command(f"{message_number}: {part}", message_number)
            message_number += 1

    return message_number

def _send_command(message, message_number):
    """Führt den Befehl zum Senden einer Nachricht aus, wiederholt bei Fehlschlag, mit einem 1-Sekunden-Cooldown zwischen den Versuchen."""
    success = False
    attempts = 0
    while not success:
        if not demo_mode:
            command = f"meshtastic --host {meshtastic_host} --ch-index {meshtastic_ch_index} --sendtext '{message}'"
            try:
                subprocess.run(command, shell=True, check=True)
                logging.info(f"Nachricht {message_number} erfolgreich gesendet: {message}")
                success = True
            except subprocess.CalledProcessError:
                attempts += 1
                logging.warning(f"Fehler beim Senden der Nachricht {message_number}, Versuch {attempts}. Wiederhole...")
        else:
            logging.info(f"Demomodus aktiviert, Nachricht {message_number} nicht gesendet: {message}")
            success = True  # Im Demomodus behandeln, als wäre die Nachricht erfolgreich gesendet worden.

        if not success or not demo_mode:
            time.sleep(3)  # Warte 3 Sekunden vor dem nächsten Versuch oder nach erfolgreichem Senden


def split_message(message, max_size):
    """Teilt eine Nachricht in Teile, die kleiner oder gleich der maximalen Größe sind."""
    parts = []
    current_part = ""
    for word in message.split():
        if len((current_part + " " + word).encode('utf-8')) <= max_size:
            current_part += " " + word if current_part else word
        else:
            parts.append(current_part)
            current_part = word
    if current_part:  # Füge den letzten Teil hinzu, falls vorhanden
        parts.append(current_part)
    return parts

def process_new_entry(entry):
    logging.info(f"Neuer Eintrag gefunden: {entry.title}")

    # Startet die Nummerierung bei 1
    message_number = 1

    # Sende Titel und Link als erste Nachricht
    message_number = send_message(f"{entry.title} | Mehr Infos: {entry.link}", message_number)

    # Wenn eine Beschreibung vorhanden ist, sende sie in aufgeteilten Nachrichten
    if 'description' in entry:
        clean_description = clean_html(entry.description)
        message_number = send_message(clean_description, message_number)

if feed_url is None:
    logging.error("FEED_URL Umgebungsvariable ist nicht gesetzt.")
else:
    seen_entries = load_seen_entries()

    while True:
        new_entries = check_for_new_entries(feed_url, seen_entries)
        for entry in new_entries:
            process_new_entry(entry)

        save_seen_entries(seen_entries)

        # Warten Sie eine Weile, bevor Sie den Feed erneut prüfen
        time.sleep(600)  # 10 Minuten warten

