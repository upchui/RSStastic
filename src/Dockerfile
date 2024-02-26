# Verwende ein offizielles Python-Image als Eltern-Image
FROM python:3.9-slim

# Setze das Arbeitsverzeichnis im Container
WORKDIR /usr/src/app

# Kopiere die Python-Abhängigkeiten-Datei in den Container
COPY requirements.txt ./

# Installiere alle notwendigen Pakete aus der requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere den Rest des Quellcodes in den Container
COPY . .

# Setze Umgebungsvariablen
ENV FEED_URL="https://www.bmi.gv.at/rss/bmi_presse.xml"
ENV SEEN_ENTRIES_FILE="/usr/src/app/data/seen_entries.json"
ENV MESHTASTIC_HOST="10.14.0.3"
ENV MESHTASTIC_CH_INDEX="0"

# Deklariere ein Volume für das Verzeichnis /usr/src/app/data
VOLUME ["/usr/src/app/data"]

# Kommando zum Ausführen des Skripts beim Starten des Containers
CMD [ "python", "./feed.py" ]
