import requests
import threading
import os
import json
from time import sleep

bot_token = os.environ.get(
    'DISCORD_BOT_TOKEN'
)
headers = {
    'Authorization': f"Bot {bot_token}"
}

def getUrlDict(cache, files_arr):
    mid = ''
    while True:
        try:
            files={
                    f'file[{idx}]':open(files_arr[idx], 'rb') for idx in range(len(files_arr))
            }
            response = requests.post(
                'https://discord.com/api/v10/channels/1409037091026763806/messages',
                headers=headers,
                files=files
            )
            if response.status_code < 300:
                mid = response.json()['id']
                break
            else:
                print(response.status_code, 'sleeping')
                sleep(1)
        except Exception as e:
            print("Exception")
            sleep(1)
    if not mid:
        raise Exception
    for f in files_arr:
        cache[f] = f'{mid}__{f}'
    print('parts', len(cache))

def upload():
    file_name = os.environ.get('FILE_NAME')
    cache = {}
    threads = []
    files = [x for x in os.listdir() if 'blob-' in x]
    for i in range(0, len(files), 10):
        t = threading.Thread(target=getUrlDict, args=(cache, files[i:i+10]))
        threads.append(t)
        if len(threads) == 20:
            [t.start() for t in threads]
            [t.join() for t in threads]
            threads = []
    [t.start() for t in threads]
    [t.join() for t in threads]
    file_meta = {
        'file_size': os.path.getsize('blob'),
        'files': cache,
        'file_name':file_name
    }
    with open(f'file_meta.json', 'w') as f:
        json.dump(file_meta, f) 
    return cache

cache = upload()

