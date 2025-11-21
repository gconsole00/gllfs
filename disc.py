import requests
import threading
import os
import json
from time import sleep
from random import randint
import random

bot_token = os.environ.get(
    'DISCORD_BOT_TOKEN'
)
bot_token_1 = os.environ.get(
    'DISCORD_BOT_TOKEN_1'
)
bot_token_2 = os.environ.get(
    'DISCORD_BOT_TOKEN_2'
)
bot_token_3 = os.environ.get(
    'DISCORD_BOT_TOKEN_3'
)
channel_id = os.environ.get(
    'DISCORD_CHANNEL_ID'
)
file_name = os.environ.get('FILE_NAME', '')
file_name = file_name.replace(':', '-')
kv_token = os.environ.get('KV_TOKEN')

bot_tokens = [
    bot_token, 
    bot_token_1, 
    bot_token_2,
    bot_token_3,
]

bot_tokens = [x for x in bot_tokens if x]

def getUrlDict(cache, files_arr):
    mid = ''
    for i in range(40):
        headers = {
            'Authorization': f"Bot {random.choice(bot_tokens)}"
        }
        try:
            files={
                f'file[{idx}]':open(files_arr[idx], 'rb') for idx in range(len(files_arr))
            }
            files['content'] = (None, file_name or '')
            response = requests.post(
                f'https://discord.com/api/v10/channels/{channel_id}/messages',
                headers=headers,
                files=files
            )
            if response.status_code < 300:
                mid = response.json()['id']
                break
            else:
                print(response.status_code, 'sleeping')
                sleep(randint(1, 10))
        except Exception as e:
            print("Exception", e)
            sleep(randint(1, 10))
    if not mid:
        raise Exception
    for f in files_arr:
        cache[f] = f'{mid}__{f}'
    print('parts', len(cache))

def upload():
    cache = {}
    threads = []
    files = sorted([x for x in os.listdir() if 'blob-' in x])
    for i in range(0, len(files), 10):
        t = threading.Thread(target=getUrlDict, args=(cache, files[i:i+10]))
        threads.append(t)
        if len(threads) == 20:
            [t.start() for t in threads]
            [t.join() for t in threads]
            threads = []
    [t.start() for t in threads]
    [t.join() for t in threads]
    if len(cache) != len(files):
        raise Exception("File count mismatch")
    else:
        print("LENGTHS MATCH", len(cache), len(files))
    file_meta = {
        'file_size': os.path.getsize('blob'),
        'files': cache,
        'file_name':file_name
    }
    headers = {
        'Authorization': f'Bearer {kv_token}',
    }

    data = {"value": file_meta}

    response = requests.post(
        f'https://kv-waterfall-b86c.hostproxy.workers.dev/key/{file_name}',
        headers=headers,
        json=data,
    )
    if len(cache) < 6:
        raise Exception
    
    return cache

cache = upload()

