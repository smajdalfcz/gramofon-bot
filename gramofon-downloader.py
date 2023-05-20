import pika
import os
from datetime import datetime
from gconfig import *
#|#|#|#|#|#|#|#|#|#|#|#|#|#
import json
from yt_dlp import YoutubeDL
import ffmpeg
import subprocess
from io import StringIO
import sys
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
    
    #|#|#|#|#|#|#|#|#|#|#|#|#|#
    LOG(bcolors.OKGREEN + "MQ | MQ_PRS_DWN MESSAGE RECEIVED" + bcolors.ENDC)
    
    try:
        mq_message_received = json.loads(body.decode())
    except:
        LOG(bcolors.FAIL + "MQ | MQ_PRS_DWN MESSAGE BAD FORMAT" + bcolors.ENDC)
    else:
        ydl_opts = {
            'format': 'bestaudio/best',
            'keepvideo':False,
            'outtmpl':mq_message_received['output_path'],
            'writethumbnail':True,
        }

        # thumbnail output hackery
        sys.stdout = tempstdout = StringIO()
        with YoutubeDL(ydl_opts) as ydl:
            ytdloutput = ydl.download([mq_message_received['source_link']])
        sys.stdout = sys.__stdout__
        ytdloutput = tempstdout.getvalue()

        for line in ytdloutput.split("\n"):
            if "[info] Writing video thumbnail" in line:
                thumbnailpath = line.split(": ")[1]
                mq_message_received['thumbnail_path'] = thumbnailpath
        # thumbnail output hackery

        mq_message_sent = json.dumps(mq_message_received)
        if MQ_SEND("MQ_DWN_PLR", mq_message_sent):
            LOG(bcolors.OKBLUE + "MQ | MQ_DWN_PLR MESSAGE SENT" + bcolors.ENDC)
        else:
            LOG(bcolors.FAIL + "MQ | MQ_DWN_PLR MESSAGE FAILED" + bcolors.ENDC)
        #|#|#|#|#|#|#|#|#|#|#|#|#|#

def MQ_LISTEN(message_queue):
    global credentials
    global parameters
    try:
        connection = pika.BlockingConnection(parameters)

        channel = connection.channel()

        channel.queue_declare(queue=message_queue)

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=message_queue, on_message_callback=MQ_RECEIVE)

        LOG(bcolors.OKGREEN + "MQ | MQ_PRS_DWN LISTENING SESSION STARTED" + bcolors.ENDC)
        channel.start_consuming()
    except:
        return False
    else:
        return True

######################################################################################################

def INIT():
    if MQ_LISTEN("MQ_PRS_DWN"):
        LOG(bcolors.OKGREEN + "MQ | MQ_PRS_DWN LISTENING SESSION ENDED SUCCESFULLY" + bcolors.ENDC)
    else:
        LOG(bcolors.FAIL + "MQ | MQ_PRS_DWN LISTENING SESSION FAILED" + bcolors.ENDC)

INIT()