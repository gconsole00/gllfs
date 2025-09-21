import os
import argparse
import requests

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
          'name': filename,
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
    kv_key = f"{KV_PREFIX}__{self.filename}"
    if self.kvRead(kv_key):
      raise Exception(f"ALREADY EXISTS {kv_key}")
    value = {
        'file_size': self.filesize,
        'files': self.assetIds,
        'file_name':self.filename
    }
    self.kvWrite(kv_key, value)
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

  def kvRead(self, key):
    key = key.replace(':', '-')
    url = f'{KV_BASE}/key/{key}'
    for i in range(3):
      response = requests.get(
        url,
      )
      if response.ok:
        return data
    return

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
        'file': (f'{self.filename}_{chunkNumber}', data),
        'parent': (None, f'{self.parent}'),
        'resource_subtype': (None, 'asana'),
        'name': (None, f'{self.filename}_{chunkNumber}')
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
  
if __name__ == '__main__':
  parser = argparse.ArgumentParser(
    prog='AsanaUpload',
    description='',
    epilog=''
  )
  parser.add_argument('filename')
  args = parser.parse_args()
  uploader = AsanaUpload(args.filename)
  uploader.upload()
