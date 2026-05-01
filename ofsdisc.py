import os, shlex
import requests
import time

TB_API_KEY = os.environ['TB_API_KEY']
IMDB_ID = os.environ['IMDB_ID']
RW_API_KEY = os.environ['RW_API_KEY']

def tryTorrentio(imdbId):
    stream_url = ""
    if ":" in imdbId:
        stream_url = "https://torrentio.strem.fun/qualityfilter=4k%7Csizefilter=10GB%7Cdebridoptions=nodownloadlinks,nocatalog%7Ctorbox={}/stream/series/{}.json".format(
            TB_API_KEY,
            imdbId
        )
    else:
        stream_url = "https://torrentio.strem.fun/qualityfilter=4k%7Csizefilter=10GB%7Cdebridoptions=nodownloadlinks,nocatalog%7Ctorbox={}/stream/movie/{}.json".format(
            TB_API_KEY,
            imdbId
        )
    streams = requests.get(
        stream_url,
        headers={
            "User-Agent": "Mozilla"
        }
    )
    streams_json = streams.json()['streams']
    for stream in streams_json:
        url = stream['url']
        headers = {"Range": "bytes=0-10", "User-Agent": "Mozilla"}
        response = requests.get(url, headers=headers)
        if not response.ok:
            raise Exception(response.status_code)
        count = 0
        while response.status_code >= 300 and count < 10:
            response = requests.get(url, headers=headers)
            if not response.ok:
                raise Exception(response.status_code)
            url = response.headers.get("Location")
            print(url)
            time.sleep(2)
            count += 1
        payload = {
            "URL": url,
            "Key": imdbId,
        }
        headers = {
            "content-type": "application/octet-stream",
            "x-namespaceid": "1",
            "x-api-key": RW_API_KEY,
        }
        response = requests.post(
          "https://ofs.proxyr.ovh/api/v1/buckets/4/objects/remoteUpload", 
          json=payload, headers=headers
        )
        return
    raise Exception

def main():
    try:
        tryTorrentio(IMDB_ID)
        return
    except Exception as e:
        os.system('echo ---TorrentioFailed')
        print("Torrentio failed", e)
    

# if __name__ == "main":
main()
