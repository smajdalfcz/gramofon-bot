import pika
import os
from datetime import datetime
from gconfig import *
#|#|#|#|#|#|#|#|#|#|#|#|#|#
import json
from yt_dlp import YoutubeDL
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

#|#|#|#|#|#|#|#|#|#|#|#|#|#
def is_supported(url):
    with YoutubeDL() as ydl:
        try:
            info_dict = ydl.extract_info(url, download=False)
        except:
            return False
        else:
            return True
#|#|#|#|#|#|#|#|#|#|#|#|#|#

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
    LOG(bcolors.OKGREEN + "MQ | MQ_RDR_PRS MESSAGE RECEIVED" + bcolors.ENDC)
    
    try:
        mq_message_received = json.loads(body.decode())
    except:
        LOG(bcolors.FAIL + "MQ | MQ_RDR_PRS MESSAGE BAD FORMAT" + bcolors.ENDC)
    else:
        if "playlist?list=" in mq_message_received['source_link']:
            LOG(bcolors.OKBLUE + "PARSER | LINK IS YOUTUBE PLAYLIST" + bcolors.ENDC)

            with YoutubeDL() as ydl:
                info_dict = ydl.extract_info(mq_message_received['source_link'], download=False)
            
            if "entries" in info_dict:
                for entry in info_dict['entries']:
                    mq_message_received['source_link'] = str(entry['webpage_url'])
                    mq_message_received['id'] = str(entry['id'])
                    mq_message_received['title'] = str(entry['title'])
                    mq_message_received['duration'] = str(entry['duration'])
                    mq_message_received['output_path'] = "./audio/" + str(entry['id']) + ".mp3"
                    #mq_message_received['thumbnail_path'] = "./thumbnails/" + str(entry['title']) + ".jpg"
                    mq_message_sent = json.dumps(mq_message_received)
            
                    if MQ_SEND("MQ_PRS_DWN", mq_message_sent):
                        LOG(bcolors.OKBLUE + "MQ | MQ_PRS_DWN MESSAGE SENT" + bcolors.ENDC)
                    else:
                        LOG(bcolors.FAIL + "MQ | MQ_PRS_DWN MESSAGE FAILED" + bcolors.ENDC)

        elif ("&list=" in mq_message_received['source_link'] and "&list=" in mq_message_received['source_link']) or is_supported(mq_message_received['source_link']):
            LOG(bcolors.OKBLUE + "PARSER | LINK IS YTDL SUPPORTED" + bcolors.ENDC)
            
            # kdyz nekdo posle link na video ktery ma v sobe i link na playlist
            if ("&list=" in mq_message_received['source_link'] and "&list=" in mq_message_received['source_link']):
                sanitized_extractor = mq_message_received['source_link'].split("&list=")[0]
            else:
                sanitized_extractor = mq_message_received['source_link']

            with YoutubeDL() as ydl:
                info_dict = ydl.extract_info(sanitized_extractor, download=False)
            
            #print("sadasdasd ---------- " + sanitized_extractor)

            mq_message_received['source_link'] = sanitized_extractor
            mq_message_received['id'] = str(info_dict.get("id", None))
            mq_message_received['title'] = str(info_dict.get("title", None))
            mq_message_received['duration'] = str(info_dict.get("duration", None))
            mq_message_received['output_path'] = "./audio/" + str(info_dict.get("id", None)) + ".mp3"
            mq_message_sent = json.dumps(mq_message_received)
            
            if MQ_SEND("MQ_PRS_DWN", mq_message_sent):
                LOG(bcolors.OKBLUE + "MQ | MQ_PRS_DWN MESSAGE SENT" + bcolors.ENDC)
            else:
                LOG(bcolors.FAIL + "MQ | MQ_PRS_DWN MESSAGE FAILED" + bcolors.ENDC)
        else:
            LOG(bcolors.FAIL + "PARSER | LINK IS NOT YTDL SUPPORTED" + bcolors.ENDC)

def MQ_LISTEN(message_queue):
    global credentials
    global parameters
    try:
        connection = pika.BlockingConnection(parameters)

        channel = connection.channel()

        channel.queue_declare(queue=message_queue)

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=message_queue, on_message_callback=MQ_RECEIVE)

        LOG(bcolors.OKGREEN + "MQ | MQ_RDR_PRS LISTENING SESSION STARTED" + bcolors.ENDC)
        channel.start_consuming()
    except:
        return False
    else:
        return True

######################################################################################################

def INIT():
    if MQ_LISTEN("MQ_RDR_PRS"):
        LOG(bcolors.OKGREEN + "MQ | MQ_RDR_PRS LISTENING SESSION ENDED SUCCESFULLY" + bcolors.ENDC)
    else:
        LOG(bcolors.FAIL + "MQ | MQ_RDR_PRS LISTENING SESSION FAILED" + bcolors.ENDC)

INIT()