
# Gramofon bot

An unreliable discord bot which let's you and your friends (sometimes) listen to music in a discord voice room. I do not recommend making any changes into the spaghetti "code", otherwise horrible things will happen.

# Setup

- define your server stuff in gconfig.py
- build the docker image
- pray

# Usage

- g!play [url]
- g!skip
- g!stop

# How the magic works

- several components communicate with each other through RabbitMQ
- audio is extracted by yt-dl
- there's a card in chat with your audio queue and stuff
