import pika
import os
from datetime import datetime
from gconfig import *
#|#|#|#|#|#|#|#|#|#|#|#|#|#
import discord
import hashlib
from os import path
from discord.ext import commands, tasks
import json
import threading
import asyncio
import time
#|#|#|#|#|#|#|#|#|#|#|#|#|#

global credentials
global parameters
#|#|#|#|#|#|#|#|#|#|#|#|#|#
global queue
global queue_old
queue = []
queue_old = []
global last_message
last_message = ""
#|#|#|#|#|#|#|#|#|#|#|#|#|#

credentials = pika.PlainCredentials(username=mq_username, password=mq_password, erase_on_connect=True)
parameters = pika.ConnectionParameters(host='localhost', port=5672, virtual_host=mq_broker, credentials=credentials)

#|#|#|#|#|#|#|#|#|#|#|#|#|#
intents = discord.Intents.default()
intents.message_content = True
#|#|#|#|#|#|#|#|#|#|#|#|#|#

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def GET_TIMESTAMP():
    now = datetime.now() # current date and time
    date_time = now.strftime("%m/%d/%Y %H:%M:%S")
    return date_time

def MQ_SEND(message_queue, mq_message_body):
    global credentials
    global parameters

    mq_message_body = str(mq_message_body)
    message_queue = str(message_queue)
    try:
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        channel.queue_declare(queue=message_queue)

        channel.basic_publish(exchange='', routing_key=message_queue, body=mq_message_body)
    except:
        return False
    else:
        connection.close()
        return True

def LOG(mq_message_body):
    mq_message_body = str(mq_message_body)

    mq_message_body = GET_TIMESTAMP() + ";" + os.path.basename(__file__) + ";" + mq_message_body

    if MQ_SEND("MQ_LOG", mq_message_body):
        print(bcolors.OKBLUE + "MQ | LOG SENT" + bcolors.ENDC)
    else:
        print(bcolors.FAIL + "MQ | MESSAGE FAILED" + bcolors.ENDC)

######################################################################################################

def MQ_RECEIVE(ch, method, properties, body):
    ch.basic_ack(delivery_tag=method.delivery_tag)
    LOG(bcolors.OKBLUE + "MQ | MESSAGE RECEIVED" + bcolors.ENDC)

def MQ_LISTEN(message_queue):
    global credentials
    global parameters
    try:
        connection = pika.BlockingConnection(parameters)

        channel = connection.channel()

        channel.queue_declare(queue=message_queue)

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=message_queue, on_message_callback=MQ_RECEIVE)

        LOG(bcolors.OKGREEN + "MQ | LISTENING STARTED" + bcolors.ENDC)
        channel.start_consuming()
    except:
        return False
    else:
        return True

######################################################################################################

#|#|#|#|#|#|#|#|#|#|#|#|#|#
def MQ_READQUEUE(message_queue):
    global credentials
    global parameters
    
    global queue
    global queue_old
    
    try:
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        method = channel.queue_declare(queue=message_queue, passive=True)
        message_count = method.method.message_count
        print(message_count)

        queue_old = queue
        queue = []

        for x in range(0, message_count):
            try:    
                result = channel.basic_get(queue=message_queue)
            except:
                print("chyba")
            else:
                queue.append(result[2].decode())

        connection.close()
    except:
        return False
    else:
        return True
#|#|#|#|#|#|#|#|#|#|#|#|#|#

class MyClient(discord.Client):
        async def on_ready(self):
            messenger.start(self)
            print("hello")

@tasks.loop(seconds=1)
async def messenger(self):
    global channel_id
    global queue
    global queue_old
    global last_message    

    MQ_READQUEUE("MQ_DWN_PLR")

    text_channel = self.get_channel(channel_id)

    if len(queue) == 0:
        try:
            await last_message.delete()
        except:
            ""
        else:
            ""
    else:
        if queue != queue_old:
            element_counter = 0
            parser_queue = ""
            for element in queue:
                json_element = json.loads(element)
                
                if element_counter == 0:
                    if path.exists(json_element['thumbnail_path']):
                        image = discord.File(json_element['thumbnail_path'], filename="thumbnail.png")
                    else:
                        LOG(bcolors.WARNING + "MESSENGER | THUMBNAIL NOT FOUND" + bcolors.ENDC)
                        image = discord.File('./audio/render/default.png', filename="thumbnail.png")
                    
                    parser_playing = json_element['requester'] + "\n" + "[" + str(time.strftime("%H:%M:%S", time.gmtime(int(json_element['duration'])))) + "] " + json_element['title']
                    element_counter += 1
                else:
                    parser_queue += "\n\n" + json_element['requester'] + "\n" + "[" + str(time.strftime("%H:%M:%S", time.gmtime(int(json_element['duration'])))) + "] " + json_element['title']

            embedVar = discord.Embed(color=0xffd364)
                
            embedVar.add_field(name="PLAYING", value=parser_playing, inline=False)
            if len(queue) > 1:
                embedVar.add_field(name="QUEUE [" + str(len(queue)-1) + "]", value=parser_queue, inline=False)

            embedVar.set_image(url="attachment://thumbnail.png")

            try:
                await last_message.delete()
            except:
                ""
            else:
                ""
            
            #teststring = ""
            #teststring+= "┏━━━━━━━━━━━ PLAYLIST ━━━━━━━━━━━┓"
            #teststring+= "\n\n"
            #teststring+= "smajdalfcz#3273\n"
            #teststring+= "bbno$ & Y2K - lalala"
            #teststring+= "\n\n"
            #teststring+= "smajdalfcz#3273\n"
            #teststring+= "bbno$ & Y2K - lalala"
            #teststring+= "\n\n"
            #teststring+= "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"
            #embedVar.add_field(name="PLAYING", value=teststring, inline=False)

            LOG(bcolors.OKBLUE + "MESSENGER | POSTING EMBED" + bcolors.ENDC)
            last_message = await text_channel.send(file=image,embed=embedVar)

        else:
            print("bing chilling before queue change")

    print("looperinos")
    await asyncio.sleep(1)

client = MyClient(intents=intents)
client.run(token)