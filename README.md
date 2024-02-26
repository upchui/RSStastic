
## RSSTastic

## Overview
RSSTastic is a Dockerized application designed to monitor RSS feeds and forward new entries to a Meshtastic network. This application is ideal for users looking to automatically receive updates from their favorite news sites, blogs, or any other content provided through an RSS feed directly to their Meshtastic devices. It features customizable settings for feed URLs, Meshtastic network configurations, and message handling.

## Features
- Monitors an RSS feed for new entries.
- Forwards new entries to a configured Meshtastic network.
- Supports HTML cleaning for message clarity.
- Configurable message splitting and retry attempts for reliable message delivery.
- Demo mode for testing without sending messages over the network.

## Prerequisites
Before you start using RSSTastic, ensure you have the following:
- Docker installed on your host machine.
- A Meshtastic device configured and connected to the same network as your Docker host.

## Installation

1. Create a `docker-compose.yml` file:
  
    version: '3.8'
    services:
      rsstastic:
        image: thealhu/rsstastic:latest
        network_mode: "host"  
        volumes:
          - ./data:/usr/src/app/data
        environment:
          - FEED_URL=https://rss.orf.at/news.xml
          - MESHTASTIC_HOST=10.14.0.3
          - MESHTASTIC_CH_INDEX=2
          - SEND_DELAY=10
          - MAX_RETRY_ATTEMPTS=20
          - DEMOMODE=false
        restart: always

2. Customize the `environment` variables in the `docker-compose.yml` file according to your Meshtastic network and RSS feed URL.

3. Start the service:

   `docker-compose up -d`



## Configuration
The application can be customized through environment variables defined in the `docker-compose.yml` file. Below are the key variables you can configure:

- `FEED_URL`: The URL of the RSS feed to monitor.
- `MESHTASTIC_HOST`: The IP address of your Meshtastic device.
- `MESHTASTIC_CH_INDEX`: The channel index to use on your Meshtastic device.
- `SEND_DELAY`: The delay between message retries.
- `MAX_RETRY_ATTEMPTS`: The maximum number of retry attempts for sending a message.
- `DEMOMODE`: Set to `true` for testing without sending actual messages.

## Usage
After configuration, RSSTastic will automatically check the specified RSS feed for new entries at regular intervals. When a new entry is detected, it will be sent to the configured Meshtastic device, following the message handling settings.

## Contributing
Contributions to RSSTastic are welcome! Please feel free to submit pull requests or create issues for bugs, suggestions, or enhancements.


## Acknowledgments
- Thanks to the Meshtastic project for the communication platform.
- Thanks to all contributors and users of RSSTastic for their support and feedback.


