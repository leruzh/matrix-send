#!/usr/bin/python3

import sys
import io
import json
import urllib.parse
import urllib.request
from datetime import datetime
import ssl
from typing import List
import configparser
import argparse
import os

def url_quote(input: str) -> str:
    return urllib.parse.quote_plus(input)

def send_message(endpoint: str, access_token: str, channel_id: str, message: str, timeout: int, messagetype: str) -> bool:
    message_id = datetime.now().strftime("m%s.%f")
    ssl_context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLSv1_2)
    url = "{endpoint}client/r0/rooms/{channel_id}/send/m.room.message/{message_id}?access_token={access_token}".format(
        endpoint=endpoint,
        channel_id=url_quote(channel_id),
        message_id=url_quote(message_id),
        access_token=url_quote(access_token)
    )
    body = json.dumps({"msgtype": messagetype,
                       "format": "org.matrix.custom.html",
                       "body": message,
                       "formatted_body": message}).encode()
#                       }).encode()
    request = urllib.request.Request(url, method='PUT', data=body)
    with urllib.request.urlopen(request, timeout=timeout, context=ssl_context) as body:
        pass
    return body.status == 200

def main(argv: List[str]):
    parser = argparse.ArgumentParser(description="Matrix Sender")
    parser.add_argument("message", type=str, nargs='?', default=None, help='Send this message')
    parser.add_argument("--config", type=str, help='Read given configuration file')
    parser.add_argument("--level", type=str, help='Alert level')
    args = parser.parse_args(argv[1:])

    if not args.config:
        args.config = "{}/.config/matrix-send/config.ini".format(os.environ['HOME'])

    if not os.path.exists(args.config):
        print("Configuration file {} missing!".format(args.config))
        return 10

    if not args.level:
        args.level = "WARNING"

    config = configparser.ConfigParser()
    config.read(args.config)

    default = config['DEFAULT'] # type: str
    endpoint = default['endpoint'] # type: str
    access_token = default['access_token'] # type: str
    channel_id = default['channel_id'] # type: str
    timeout = int(default.get('timeout', "10"))

    if args.message is None:
        stdinutf8 = io.open(sys.stdin.fileno(), 'r', encoding='utf8')
        message = stdinutf8.read()
    else:
        message_tmp = args.message

    alertflag = "@room "

    if args.level == "CRITICAL":
        messagetype = "m.notice"
        message = alertflag + message_tmp
    elif args.level == "DOWN":
        messagetype = "m.text"
        message = alertflag + message_tmp
    elif  args.level == "UP":
        messagetype = "m.emote"
        message = message_tmp
    elif  args.level == "OK":
        messagetype = "m.emote"
        message = message_tmp
    else:
        messagetype = "m.notice"
        message = message_tmp

    if send_message(endpoint=endpoint,
                    access_token=access_token,
                    channel_id=channel_id,
                    message=message,
                    timeout=timeout,messagetype=messagetype):
        return 0
    else:
        return 1

if __name__ == '__main__':
    sys.exit(main(sys.argv))
