import pika
import os
from datetime import datetime
from gconfig import *
#|#|#|#|#|#|#|#|#|#|#|#|#|#
import discord
from discord.ext import commands, tasks
import json
import threading
import asyncio
from asyncio import sleep
#|#|#|#|#|#|#|#|#|#|#|#|#|#

global credentials
global parameters
#|#|#|#|#|#|#|#|#|#|#|#|#|#
global queue
global queue_old
queue = []
queue_old = []
global voice_channel_connection
global is_playing
is_playing = 0
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

def MQ_MESSAGECOUNT(message_queue):
    global credentials
    global parameters
    
    try:
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        method = channel.queue_declare(queue=message_queue, passive=True)
        message_count = method.method.message_count

        for x in range(0, message_count):
            try: 
                method, properties, body = channel.basic_get(queue=message_queue, auto_ack=True)
                #callback(channel, method, properties, body)
            except:
                print("chyba")
            else:
                LOG(bcolors.OKBLUE + "PLAYER | RECEIVED MESSAGE COUNT CALL" + bcolors.ENDC)

        connection.close()
    except:
        return 0
    else:
        return message_count

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

def MQ_POPQUEUE(message_queue, popcount):
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

        for x in range(0, popcount):
            try: 
                method, properties, body = channel.basic_get(queue=message_queue, auto_ack=True)
                #callback(channel, method, properties, body)
            except:
                print("chyba")
            else:
                LOG(bcolors.OKBLUE + "PLAYER | POPPED QUEUE " + message_queue + bcolors.ENDC)

        connection.close()
    except:
        return False
    else:
        return True

######################################################################################################

class MyClient(discord.Client):
    async def on_ready(self):
        zdau.start(self)
        print("hello")

@tasks.loop(seconds=1)
async def zdau(self):
    global voice_id
    global queue
    global queue_old
    global voice_channel_connection
    global is_playing

    MQ_READQUEUE("MQ_DWN_PLR")

    if len(queue) == 0:
        try:
            await voice_channel_connection.disconnect()
        except:
            print("tried to leave but uhh ohhhhhh idk")
        else:
            LOG(bcolors.WARNING + "PLAYER | QUEUE EMPTY LEAVING" + bcolors.ENDC)
            print("queue empty, leaving")
    else:
        if queue != queue_old:
            if is_playing == 0:
                try:
                    voice_channel = self.get_channel(voice_id)
                    voice_channel_connection = await voice_channel.connect()
                except:
                    print(":<")
                else:
                    print(":3")
                    
                try:
                    voice_channel_connection.play(discord.FFmpegPCMAudio(source=(json.loads(queue[0])['output_path'])))
                except:
                    print("couldnt play")
                else:    
                    is_playing = 1
                    LOG(bcolors.OKBLUE + "PLAYER | PLAYING STARTED" + bcolors.ENDC)

                    while voice_channel_connection.is_playing():
                        print("hraju :)")
                        
                        skipcall_value = MQ_MESSAGECOUNT("MQ_SKIP")
                        if skipcall_value != 0:
                            MQ_POPQUEUE("MQ_DWN_PLR", skipcall_value-1)
                            voice_channel_connection.stop()
                        
                        stopcall_value = MQ_MESSAGECOUNT("MQ_STOP")
                        if stopcall_value != 0:
                            MQ_POPQUEUE("MQ_RDR_PRS", MQ_MESSAGECOUNT("MQ_RDR_PRS"))
                            MQ_POPQUEUE("MQ_PRS_DWN", MQ_MESSAGECOUNT("MQ_PRS_DWN"))
                            MQ_POPQUEUE("MQ_DWN_PLR", MQ_MESSAGECOUNT("MQ_DWN_PLR"))
                            voice_channel_connection.stop()

                        await sleep(1)
                    
                    print("yoooo uz nehraju")
                    MQ_POPQUEUE("MQ_DWN_PLR", 1)
                    voice_channel_connection.stop
                    is_playing = 0
        else:
            print("bing chilling before queue change")
            #is_playing = 0

    print("looperinos")
    await asyncio.sleep(1)

client = MyClient(intents=intents)
client.run(token)