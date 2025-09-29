import os
import argparse
import json
import requests


SLACK_BOT_TOKEN = os.environ['SLACK_BOT_TOKEN']
SLACK_CHANNEL_ID = os.environ['SLACK_CHANNEL_ID']
KV_TOKEN = os.environ['KV_TOKEN']
CHUNK_SIZE = 1000000000
KV_PREFIX = "SLACK"
KV_BASE = "https://kv-waterfall-b86c.hostproxy.workers.dev"

class SlackUpload:
  def __init__(self, file):
    self.file = file
    self.filename = file.split('/')[-1]
    self.uploadedChunks = []
    self.filesize = os.path.getsize(file)
  
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
        return response.text
    raise Exception("KV Write failed", response.status_code, response.text)
    
  def generateUploadUrl(self, chunkName, chunk):
    url = "https://slack.com/api/files.getUploadURLExternal"
    data = {
      'token':(None, SLACK_BOT_TOKEN),
      'length': (None, len(chunk)),
      'filename': (None, chunkName)
    }
    response = requests.post(url, files=data)
    if not response.json()['ok']:
      raise Exception(response.text)
    return response.json()

  def uploadChunk(self, url, chunkName, chunk):
    files = {
      'file':(chunkName, chunk)
    }
    response = requests.post(
      url,
      files=files
    )
    if not response.ok:
      raise Exception(response.text)
    return response

  def finalizeUpload(self):
    url = "https://slack.com/api/files.completeUploadExternal"

    payload = {
        "token": (None, SLACK_BOT_TOKEN),
        "files": (None, json.dumps(self.uploadedChunks)),
        "channel_id": (None, SLACK_CHANNEL_ID),
        "initial_comment": self.filename
    }

    response = requests.post(url, files=payload)
    if not response.json()['ok']:
      raise Exception(response.text)
    return response.json()
  
  def upload(self):
    with open(self.file, 'rb') as f:
      for i in range(1000):
        chunk = f.read(CHUNK_SIZE)
        if not len(chunk):
          break
        chunkName = f"{self.filename}_{i}"
        chunkDetails = self.generateUploadUrl(
          chunkName,
          chunk
        )
        chunkId = chunkDetails['file_id']
        uploadUrl = chunkDetails['upload_url']
        self.uploadChunk(
          uploadUrl,
          chunkName,
          chunk
        )
        print(i, chunkName)
        self.uploadedChunks.append(
          {"id":chunkId, "title":chunkName}
        )
    self.finalizeUpload()
    metadata = {
      'file_size': self.filesize,
      'files': self.uploadedChunks
    }
    self.kvWrite(
      f'SLACK__{self.filename}',
      metadata
    )
  
if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('filename')
  args = parser.parse_args()
  uploader = SlackUpload(args.filename)
  uploader.upload()
