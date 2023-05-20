import pika
import os
from datetime import datetime
from gconfig import *
#|#|#|#|#|#|#|#|#|#|#|#|#|#
import discord
import json
#|#|#|#|#|#|#|#|#|#|#|#|#|#

global credentials
global parameters

credentials = pika.PlainCredentials(username=mq_username, password=mq_password, erase_on_connect=True)
parameters = pika.ConnectionParameters(host='localhost', port=5672, virtual_host=mq_broker, credentials=credentials)

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

def INIT():
    ""
    
#|#|#|#|#|#|#|#|#|#|#|#|#|#
class MyClient(discord.Client):
        async def on_ready(self):
            LOG(bcolors.OKGREEN + "DISCORD | BOT CONNECTED" + bcolors.ENDC)

        async def on_message(self, message):
            global channel_id

            if message.author == client.user:
                return
            else:
                if message.content.startswith('g!skip'):
                    try:
                        await message.delete()
                    except:
                        ""
                    else:
                        ""
                    
                    if len(message.content.split(" ")) > 1:
                        skip_count = int(message.content.split(" ")[1])
                    else:
                        skip_count = 1

                    for i in range(0, skip_count):
                        if MQ_SEND("MQ_SKIP",message):
                            LOG(bcolors.OKBLUE + "READER | SENDING SKIP REQUEST" + bcolors.ENDC)
                        else:
                            LOG(bcolors.FAIL + "EADER | SENDING SKIP REQUEST FAILED" + bcolors.ENDC)
                
                if message.content.startswith('g!stop'):
                    try:
                        await message.delete()
                    except:
                        ""
                    else:
                        ""

                    if MQ_SEND("MQ_STOP",message):
                        LOG(bcolors.OKBLUE + "READER | SENDING STOP REQUEST" + bcolors.ENDC)
                    else:
                        LOG(bcolors.FAIL + "EADER | SENDING STOP REQUEST FAILED" + bcolors.ENDC)
                
                if message.content.startswith('g!play'):
                    try:
                        await message.delete()
                    except:
                        ""
                    else:
                        ""
                    if len(message.content.split(" ")) == 2:
                        LOG(bcolors.OKBLUE + "DISCORD | RECEIVED VALID !PLAY MESSAGE" + bcolors.ENDC)

                        mq_message_array = {}
                        mq_message_array['timestamp'] = GET_TIMESTAMP()
                        mq_message_array['requester'] = str(message.author)
                        mq_message_array['source_link'] = message.content.split(" ")[1]                        
                        mq_message_array['id'] = 'value'
                        mq_message_array['title'] = 'value'
                        mq_message_array['duration'] = '??:??:??'
                        mq_message_array['output_path'] = 'value'
                        mq_message_array['thumbnail_path'] = 'value'

                        mq_message_json = json.dumps(mq_message_array)

                        if MQ_SEND("MQ_RDR_PRS", mq_message_json):
                            LOG(bcolors.OKBLUE + "MQ | MQ_RDR_PRS MESSAGE SENT" + bcolors.ENDC)
                        else:
                            LOG(bcolors.FAIL + "MQ | MQ_RDR_PRS MESSAGE FAILED" + bcolors.ENDC)
                    else:
                        LOG(bcolors.FAIL + "DISCORD | RECEIVED INVALID !PLAY FORMAT" + bcolors.ENDC)
                

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(token)
#|#|#|#|#|#|#|#|#|#|#|#|#|#

INIT()