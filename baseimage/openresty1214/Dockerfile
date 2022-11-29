FROM openresty/openresty:1.21.4.1-0-bullseye

WORKDIR /usr/src/

COPY ./sources.list /usr/etc/

RUN cat /usr/etc/sources.list > /etc/apt/sources.list               \
    && rm -rf /var/lib/apt/lists/* /etc/apt/sources.list.d/*.list   \
    && apt update

