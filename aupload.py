import os
import argparse
import requests
import time
import random
import sys

ASANA_PAT = os.environ.get('ASANA_PAT')
PROJECT_ID = os.environ.get('PROJECT_ID')
KV_TOKEN = os.environ.get('KV_TOKEN')

KV_PREFIX = "ASANA"
KV_BASE = "https://kv-waterfall-b86c.hostproxy.workers.dev"
CHUNK_SIZE = 100000000


class AsanaUpload:
  def __init__(self, file):
    self.parent = ''
    self.file = file
    self.filename = file.split('/')[-1]
    self.filesize = os.path.getsize(file)
    self.assetIds = []
    
  def createParent(self, filename):
    url = "https://app.asana.com/api/1.0/tasks"
    headers = {
    'accept': 'application/json',
    'authorization': f'Bearer {ASANA_PAT}',
    'content-type': 'application/json',
    }

    json_data = {
      'data': {
          'name': filename.replace('tt', ''),
          'resource_subtype': 'default_task',
          'approval_status': 'approved',
          'completed': True,
          'projects': [
              PROJECT_ID,
          ],
      },
    }
    response = None
    for i in range(3):
      response = requests.post(
        url, 
        headers=headers, 
        json=json_data
      )
      if response.ok:
        return response.json()["data"]["gid"]
    raise Exception("Error while creating parent", response.status_code, response.text)
    
  def upload(self):
    file = self.file
    self.parent = self.createParent(self.filename)
    with open(file, 'rb') as f:
      chunkNumber = 0
      while True:
          data = f.read(100000000)
          if not data:
            break
          assetId = self.uploadChunk(chunkNumber, data)
          self.assetIds.append(assetId)
          chunkNumber += 1
    kv_key = f"{KV_PREFIX}__{self.filename}"
    value = {
        'file_size': self.filesize,
        'files': self.assetIds,
        'file_name':self.filename
    }
    return self.kvWrite(kv_key, value)

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
    
  
  def uploadChunk(self, chunkNumber, data):
    headers = {
        'accept': 'application/json',
        'authorization': f'Bearer {ASANA_PAT}',
    }
    files = {
        'file': (f'{self.filename}_{chunkNumber}'.replace('tt', ''), data),
        'parent': (None, f'{self.parent}'),
        'resource_subtype': (None, 'asana'),
    }
    for i in range(3):
      print("Uploading", self.filename, chunkNumber)
      response = requests.post(
        'https://app.asana.com/api/1.0/attachments', 
        headers=headers, 
        files=files
      )
      if response.ok:
        json = response.json()
        return json['data']['gid']
      else:
        print("Chunk upload error", response.status_code, response.text)
    raise Exception("Upload failed")
  
def deleteAttachments(taskId):
  url = 'https://app.asana.com/api/1.0/attachments'
  headers = {
        'accept': 'application/json',
        'authorization': f'Bearer {ASANA_PAT}',
  }
  params = {
    'limit': '100',
    'parent': taskId,
  }
  response = requests.get(
    url,
    headers=headers,
    params=params
  )
  attachmentList = response.json()['data']
  attachmentIds = [a['gid'] for a in attachmentList]
  for gid in attachmentIds:
    url = f"https://app.asana.com/api/1.0/attachments/{gid}"
    response = requests.delete(
      url,
      headers=headers
    )
    print(gid, "Delete status", response.status_code)
  
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
      time.sleep(random.randint(1,10))
      uploader = AsanaUpload(args.filename)
      uploader.upload()
