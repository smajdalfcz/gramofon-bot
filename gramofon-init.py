import pika
import os
import subprocess
from datetime import datetime
from gconfig import *

#|#|#|#|#|#|#|#|#|#|#|#|#|#
with open(os.devnull, 'w') as fp:
    subprocess.Popen((["python3", "/gramofon/gramofon-reader.py"]), stdout=fp)
    subprocess.Popen((["python3", "/gramofon/gramofon-parser.py"]), stdout=fp)
    subprocess.Popen((["python3", "/gramofon/gramofon-downloader.py"]), stdout=fp)
    subprocess.Popen((["python3", "/gramofon/gramofon-messenger.py"]), stdout=fp)
    subprocess.Popen((["python3", "/gramofon/gramofon-player.py"]), stdout=fp)
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
        print(bcolors.FAIL + "MQ | LOG FAILED" + bcolors.ENDC)

######################################################################################################

def MQ_RECEIVE(ch, method, properties, body):
    ch.basic_ack(delivery_tag=method.delivery_tag)
    #|#|#|#|#|#|#|#|#|#|#|#|#|#
    print(body.decode())
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

        LOG(bcolors.OKGREEN + "MQ | LISTENING STARTED" + bcolors.ENDC)
        channel.start_consuming()
    except:
        return False
    else:
        return True

######################################################################################################

def INIT():
    if MQ_LISTEN("MQ_LOG"):
        LOG(bcolors.OKGREEN + "MQ | MQ_LOG LISTENING SESSION ENDED SUCCESFULLY" + bcolors.ENDC)
    else:
        LOG(bcolors.FAIL + "MQ | MQ_LOG LISTENING SESSION FAILED" + bcolors.ENDC)

INIT()