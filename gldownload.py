import os, shlex
import requests

VIDLINK_ADDON_URL = os.environ['VIDLINK_ADDON_URL']
STREMSRC_ADDON_URL = VIDLINK_ADDON_URL.replace('vidlink', 'stremsrc')
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
        response = requests.get(url, allow_redirects=False)
        redirect_url = response.headers.get('Location')
        payload = {
            "URL": redirect_url,
            "Key": imdbId
        }
        headers = {
            "content-type": "application/octet-stream",
            "x-namespaceid": "1",
            "x-api-key": RW_API_KEY,
        }
        response = requests.put(
            "https://ofs.proxyr.ovh/api/v1/buckets/4/objects/remoteUpload", 
            json=payload, headers=headers
        )
        print(response.text)
        if not response.ok:
            raise Exception(response.text)
        return
    raise Exception

def main():
    try:
        tryTorrentio(IMDB_ID)
        return
    except Exception as e:
        os.system('echo ---TorrentioFailed')
        print("Torrentio failed", e)
        raise
    

# if __name__ == "main":
main()
