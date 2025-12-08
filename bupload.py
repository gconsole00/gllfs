import os
import sys
import math
import time
import json
import dotenv
import requests
import argparse
import threading
import concurrent.futures
from bin2png import data_to_png_data, png_data_to_data
dotenv.load_dotenv()


CLIENT_ID = os.environ['BLOGGER_CLIENT_ID']
CLIENT_SECRET = os.environ['BLOGGER_CLIENT_SECRET']
REFRESH_TOKEN = os.environ['BLOGGER_REFRESH_TOKEN']
ALBUM_ID = os.environ['BLOGGER_ALBUM_ID']

REFRESH_TOKEN_EP = "https://oauth2.googleapis.com/token"
CHUNK_SIZE = 90000000

KV_BASE = "https://kv-waterfall-b86c.hostproxy.workers.dev"
KV_PREFIX = "BLOGGER"
KV_TOKEN = os.environ['KV_TOKEN']

lock = threading.Lock()
MAX_WORKERS = 8
LEN_DELIMITER = "__len__"



class Blogger:
  def __init__(self, file):
    self.file = file
    self.filesize = os.path.getsize(file)
    self.filename = file.split('/')[-1]
    self.accessToken = ""
    self.imageUrls = {}
    self.refreshAccessToken()
  
  def refreshAccessToken(self):
    data = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'refresh_token',
        'refresh_token': REFRESH_TOKEN,
    }
    response = None
    for i in range(3):
      response = requests.post(REFRESH_TOKEN_EP, data=data)
      if response.ok:
        break
    self.accessToken = response.json()['access_token']
  
  def getUploadUrl(self, size, chunkNumber):
    url = "https://docs.google.com/upload/blogger/photos/resumable"

    querystring = {"authuser":"0","opi":"98421741"}

    payload = {
      "protocolVersion":"0.8","createSessionRequest":{
        "fields":[
          {"external":{"name":"file","filename":f"{self.filename}_{chunkNumber}","put":{},"size":size}},
          {"inlined":{"name":"title","content":f"{self.filename}_{chunkNumber}","contentType":"text/plain"}},
          {"inlined":{"name":"addtime","content":"1762648211506","contentType":"text/plain"}},
          {"inlined":{"name":"onepick_version","content":"v2","contentType":"text/plain"}},
          {"inlined":{"name":"onepick_host_id","content":"10","contentType":"text/plain"}},
          {"inlined":{"name":"onepick_host_usecase","content":"RichEditor","contentType":"text/plain"}},
          {"inlined":{"name":"album_mode","content":"album","contentType":"text/plain"}},
          {"inlined":{"name":"album_id","content":f"{ALBUM_ID}","contentType":"text/plain"}},
          {"inlined":{"name":"silo_id","content":"3","contentType":"text/plain"}}
          ]
        }
      }
    response = None
    for i in range(30):
      headers = {
          "x-client-pctx": "CgcSBWjtl_cu",
          "x-goog-upload-command": "start",
          "x-goog-upload-header-content-length": f"{size}",
          "x-goog-upload-header-content-type": "image/png",
          "x-goog-upload-protocol": "resumable",
          "authorization": f"Bearer {self.accessToken}",
          "content-type": "application/x-www-form-urlencoded"
      }
      response = requests.post(url, data=json.dumps(payload), headers=headers, params=querystring)
      if response.ok and not 'AUTH_REQUIRED' in response.text:
        return response.headers['x-goog-upload-url']
      else:
        print("Error:getUploadUrl", response.status_code, response.text, flush=True)
        self.refreshAccessToken()
    raise Exception()
  
  def uploadChunk(self, chunkNumber):
    with open(self.file, 'rb') as f:
      f.seek(chunkNumber * CHUNK_SIZE)
      rawData = f.read(CHUNK_SIZE)
      ogLen = len(rawData)
      data = data_to_png_data(rawData)
      for i in range(30):
        print("Uploading chunk", chunkNumber, "attempt", i, flush=True)
        try:
          uploadUrl = self.getUploadUrl(len(data), chunkNumber)
          headers = {
              'accept': '*/*',
              'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
              'cache-control': 'no-cache',
              'content-type': 'image/png',
              'origin': 'https://docs.google.com',
              'pragma': 'no-cache',
              'priority': 'u=1, i',
              'referer': 'https://docs.google.com/',
              'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
              'x-client-pctx': 'CgcSBWjtl_cu',
              'x-goog-upload-command': 'upload, finalize',
              'x-goog-upload-offset': '0',
          }
          response = requests.post(uploadUrl, headers=headers, data=data)
          if response.ok:
            imageUrl = response.json()[
              'sessionStatus'][
                'additionalInfo'][
                  'uploader_service.GoogleRupioAdditionalInfo'][
                    'completionInfo'][
                      'customerSpecificInfo'][
                        'url']
            components = imageUrl.split('/')
            baseUrl = '/'.join(components[:-1])
            url = f'{baseUrl}/s0/{components[-1]}{LEN_DELIMITER}{ogLen}'
            lock.acquire()
            self.imageUrls[chunkNumber] = url
            lock.release()
            return url
          else:
            print(
              f"Error:uploadChunk attempt {i}", chunkNumber, response.status_code, response.text,
              flush=True
            )
            raise Exception()
        except Exception as e:
          print(e, flush=True)
          time.sleep(1)

  def kvWrite(self, key, value):
    key = key.replace(':', '-')
    url = f'{KV_BASE}/key/{key}'
    headers = {
      'Authorization': f'Bearer {KV_TOKEN}',
    }
    data = {"value": value}
    response = None
    for i in range(3):
      response = requests.post(
        url,
        headers=headers,
        json=data,
      )
      if response.ok:
        print("KV write success", flush=True)
        return response.text
    raise Exception("KV Write failed", response.status_code, response.text)

  def kvRead(self, key):
    key = key.replace(':', '-')
    url = f'{KV_BASE}/key/{key}'
    print(url, flush=True)
    response = None
    for i in range(3):
      response = requests.get(
        url,
      )
      if response.ok:
        return response.text
    raise Exception("KV Read failed", response.status_code, response.text)
  
  def upload(self):
    expectedChunks = math.ceil(self.filesize/CHUNK_SIZE)
    futures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor: 
      for chunkNumber in range(expectedChunks):
        future = executor.submit(self.uploadChunk, chunkNumber)
        futures.append(future)
      completed = 0
      for future in concurrent.futures.as_completed(futures):
        completed += 1
        print("Completed", completed, "of", expectedChunks, flush=True)
        
    kv_key = "{}__{}".format(
      KV_PREFIX, self.filename
    )
    value = {
        'file_size': self.filesize,
        'files': [self.imageUrls[x] for x in range(len(self.imageUrls))],
        'file_name':self.filename,
        'chunksize': CHUNK_SIZE,
    }
    if len(value['files']) != expectedChunks:
      raise Exception("Expected and actual chunks dont match", len(value['files']), "!=", expectedChunks)
    else:
      print("Expected and actual chunk count match", len(value['files']), "==", expectedChunks, flush=True)
    self.kvWrite(kv_key, value)
  
  def download(self):
    kv_key = "{}__{}".format(
      KV_PREFIX, self.filename
    )
    fileData = json.loads(self.kvRead(kv_key))
    with open(self.filename, 'ab') as f:
      for url in fileData['files']:
        url, ogLength = url.split(LEN_DELIMITER)
        data = requests.get(url).content
        f.write(png_data_to_data(data, int(ogLength)))


if __name__ == '__main__':
  parser = argparse.ArgumentParser(
    prog='AsanaUpload',
    description='',
    epilog=''
  )
  if len(sys.argv) > 1:
    parser.add_argument('filename')
    args = parser.parse_args()
    if args.filename:
      uploader = Blogger(args.filename)
      uploader.upload()
