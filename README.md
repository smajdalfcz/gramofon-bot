
# Gramofon bot

An unreliable discord bot which (sometimes) let's you and your friends listen to music in a discord voice room. I do not recommend making any changes to the spaghetti "code", otherwise horrible things will happen.

# Setup

- define your server stuff in gconfig.py
- build the docker image
- fire that bad boy up
- pray

# Usage

- g!play [url]
- g!skip
- g!stop

# How the magic works

- several components communicate with each other through RabbitMQ
- audio is extracted by yt-dl
- there's an embed in the chat with your audio queue and stuff
- I have been locked up in this basement for over three years, this is my only way to communicate with you, please save me before they see the commit oh no they're coming help me please help
