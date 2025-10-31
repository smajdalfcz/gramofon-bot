FROM ubuntu:25.04

RUN apt-get update -y
RUN apt-get update -y
RUN apt-get -y install python3 python3-pip ffmpeg curl gnupg apt-transport-https
RUN python3 -m pip install -U discord youtube-dl pynacl pika ffmpeg pillow yt-dlp --break-system-packages

RUN curl -1sLf "https://keys.openpgp.org/vks/v1/by-fingerprint/0A9AF2115F4687BD29803A206B73A36E6026DFCA" | gpg --dearmor | tee /usr/share/keyrings/com.rabbitmq.team.gpg > /dev/null
RUN curl -1sLf "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0xf77f1eda57ebb1cc" | gpg --dearmor | tee /usr/share/keyrings/net.launchpad.ppa.rabbitmq.erlang.gpg > /dev/null
RUN curl -1sLf "https://packagecloud.io/rabbitmq/rabbitmq-server/gpgkey" | gpg --dearmor | tee /usr/share/keyrings/io.packagecloud.rabbitmq.gpg > /dev/null
RUN touch /etc/apt/sources.list.d/rabbitmq.list
RUN echo "deb [signed-by=/usr/share/keyrings/net.launchpad.ppa.rabbitmq.erlang.gpg] http://ppa.launchpad.net/rabbitmq/rabbitmq-erlang/ubuntu jammy main" >> /etc/apt/sources.list.d/rabbitmq.list
RUN echo "deb-src [signed-by=/usr/share/keyrings/net.launchpad.ppa.rabbitmq.erlang.gpg] http://ppa.launchpad.net/rabbitmq/rabbitmq-erlang/ubuntu jammy main" >> /etc/apt/sources.list.d/rabbitmq.list
RUN echo "deb [signed-by=/usr/share/keyrings/io.packagecloud.rabbitmq.gpg] https://packagecloud.io/rabbitmq/rabbitmq-server/ubuntu/ jammy main" >> /etc/apt/sources.list.d/rabbitmq.list
RUN echo "deb-src [signed-by=/usr/share/keyrings/io.packagecloud.rabbitmq.gpg] https://packagecloud.io/rabbitmq/rabbitmq-server/ubuntu/ jammy main" >> /etc/apt/sources.list.d/rabbitmq.list
RUN apt-get --allow-unauthenticated update -y
RUN apt-get install -y erlang-base erlang-asn1 erlang-crypto erlang-eldap erlang-ftp erlang-inets erlang-mnesia erlang-os-mon erlang-parsetools erlang-public-key erlang-runtime-tools erlang-snmp erlang-ssl erlang-syntax-tools erlang-tftp erlang-tools erlang-xmerl --fix-missing
RUN apt-get install rabbitmq-server -y --fix-missing

ENV RABBITMQ_HOME=/usr/lib/rabbitmq/lib/rabbitmq_server-4.0.5 \
    RABBITMQ_PLUGINS_DIR=/usr/lib/rabbitmq/lib/rabbitmq_server-4.0.5/plugins

RUN mkdir /gramofon && \
    mkdir /gramofon/audio

ADD gconfig.py gramofon/
ADD gramofon-init.py gramofon/
ADD gramofon-reader.py gramofon/
ADD gramofon-parser.py gramofon/
ADD gramofon-downloader.py gramofon/
ADD gramofon-messenger.py gramofon/
ADD gramofon-player.py gramofon/

CMD rabbitmq-plugins enable rabbitmq_management && \
    service rabbitmq-server start && \
    rabbitmqctl add_user thebigrabbit MyS3cur3Passwor_d && \
    rabbitmqctl set_user_tags thebigrabbit administrator && \
    rabbitmqctl delete_user guest && \
    rabbitmqctl delete_vhost / && \
    rabbitmqctl add_vhost gramofon_broker && \
    rabbitmqctl set_permissions -p gramofon_broker thebigrabbit '.*' '.*' '.*' && \
    rabbitmqctl list_users && \
    rabbitmqctl list_permissions -p gramofon_broker && \
    python3 gramofon/gramofon-init.py && \
    sleep infinity
