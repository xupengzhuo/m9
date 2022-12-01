FROM nginx/unit:1.28.0-python3.10

WORKDIR /usr/src/

COPY ./sources.list ./pip.conf /etc

RUN cat /etc/sources.list > /etc/apt/sources.list                   \
    && apt update && apt install -y python3-pip                     \
    && apt remove -y python3-pip                                    \
    && apt autoremove --purge -y                                    \
    && rm -rf /var/lib/apt/lists/* /etc/apt/sources.list.d/*.list

