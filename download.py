import os
import requests

VIDLINK_ADDON_URL = os.environ['VIDLINK_ADDON_URL']
STREMSRC_ADDON_URL = VIDLINK_ADDON_URL.replace('vidlink', 'stremsrc')
TB_API_KEY = os.environ['TB_API_KEY']
IMDB_ID = os.environ['IMDB_ID']

def tryVidlink(imdbId):
    stream_url = ""
    if ":" in imdbId:
        stream_url = "{}/stream/series/{}.json".format(
            VIDLINK_ADDON_URL,
            imdbId
        )
    else:
        stream_url = "{}/stream/movie/{}.json".format(
            VIDLINK_ADDON_URL,
            imdbId
        )
    streams = requests.get(stream_url)
    streams_json = streams.json()['streams']
    if len(streams_json):
        playlist_url = streams_json[0]['url']
        command = (
            f'yt-dlp '
            f'--retry-sleep fragment:2:8:2 '
            f'--retries 20 '
            f'--fragment-retries 100 '
            f'--add-header "Referer: https://vidlink.pro/" '
            f'--add-header "Origin: https://vidlink.pro" '
            f'--concurrent-fragments 8 '
            f'--abort-on-unavailable-fragment '
            f'-o video.mp4 "{playlist_url}"'
        )
        output = os.system(
            command,
        )
        if output != 0:
            raise Exception
        return
    raise Exception("Error")


def trySremsrc(imdbId):
    stream_url = ""
    if ":" in imdbId:
        stream_url = "{}/stream/series/{}.json".format(
            STREMSRC_ADDON_URL,
            imdbId
        )
    else:
        stream_url = "{}/stream/movie/{}.json".format(
            STREMSRC_ADDON_URL,
            imdbId
        )
    streams = requests.get(stream_url)
    streams_json = streams.json()['streams']
    if len(streams_json):
        playlist_url = streams_json[0]['url']
        command = (
            f'yt-dlp '
            f'--retry-sleep fragment:2:8:2 '
            f'--retries 20 '
            f'--fragment-retries 100 '
            f'--add-header "Referer: https://cloudnestra.com/" '
            f'--add-header "Origin: https://cloudnestra.com" '
            f'--concurrent-fragments 8 '
            f'--abort-on-unavailable-fragment '
            f'-o video.mp4 "https://solitary-grass-77bc.hostproxy.workers.dev/{playlist_url}"'
        )
        output = os.system(
            command,
        )
        if output != 0:
            raise Exception
        return
    raise Exception

def tryTorrentio(imdbId):
    stream_url = ""
    if ":" in imdbId:
        stream_url = "https://torrentio.strem.fun/qualityfilter=4k%7Csizefilter=6GB%7Cdebridoptions=nodownloadlinks,nocatalog%7Ctorbox={}/stream/series/{}.json".format(
            TB_API_KEY,
            imdbId
        )
    else:
        stream_url = "https://torrentio.strem.fun/qualityfilter=4k%7Csizefilter=6GB%7Cdebridoptions=nodownloadlinks,nocatalog%7Ctorbox={}/stream/movie/{}.json".format(
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
        if "264" in url or "265" in url or "hevc" in url:
            command = """
                aria2c --allow-overwrite=true -x16 -j16 {} -o video.mp4
            """.format(url)
            output = os.system(command)
            if output != 0:
                raise Exception
            return
    raise Exception

def main():
    try:
        tryTorrentio(IMDB_ID)
        return
    except Exception as e:
        os.system('echo 1---TorrentioFailed')
        print("Torrentio failed", e)
        
    try: 
        tryVidlink(IMDB_ID)
        return
    except Exception as e:
        os.system("echo 3---VidlinkFailed")
        print("Vidlink failed", e)
        
    try:
        trySremsrc(IMDB_ID)
        return
    except Exception as e:
        os.system("echo 2---StremsrcFailed")
        print("Stremsrc failed", e)
        raise
    

# if __name__ == "main":
main()
