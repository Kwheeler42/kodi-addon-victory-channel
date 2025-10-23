# Module: main
# Author: Kenneth Wheeler
# Created on: 08.10.2022
# License: MIT
import sys
import json
from urllib.parse import urlencode, parse_qsl
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon

# Get the plugin url in plugin:// notation.
_URL = sys.argv[0]
# Get the plugin handle as an integer number.
_HANDLE = int(sys.argv[1])

# Addon settings
ADDON = xbmcaddon.Addon()
DEFAULT_API_URL = "https://rt1o4zk4ub.execute-api.us-west-2.amazonaws.com/prod/kodi/content"
API_URL = ADDON.getSetting("api_url") or DEFAULT_API_URL
try:
    REQUEST_TIMEOUT = int(ADDON.getSetting("request_timeout") or 10)
except ValueError:
    REQUEST_TIMEOUT = 10
ENABLE_DEBUG = (ADDON.getSetting("enable_debug") or "false").lower() == "true"

def _log(msg):
    if ENABLE_DEBUG:
        xbmc.log(f"[VictoryChannel] {msg}", xbmc.LOGINFO)

def _http_get_json(url, timeout=10):
    try:
        req = Request(url, headers={"User-Agent": "Kodi-VictoryChannel/0.1"})
        with urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            return json.loads(raw.decode("utf-8"))
    except (HTTPError, URLError, json.JSONDecodeError) as e:
        _log(f"HTTP JSON failed: {e} url={url}")
        return {}

# Safe fetch of API payload
aws_link = _http_get_json(API_URL, REQUEST_TIMEOUT)
data_items = aws_link.get("data", [])
_log(f"Fetched items: {len(data_items)}")

# Build category metadata once
CATEGORIES = {}
_seen_program_ids = set()
for item in data_items:
    title = item.get("program_title")
    program_id = (item.get("program_id") or "").split("_", 1)[0]
    if not title:
        continue
    if program_id in _seen_program_ids:
        continue
    _seen_program_ids.add(program_id)
    CATEGORIES[title] = {
        "thumb": item.get("thumbnail", ""),
        "genre": item.get("description", ""),
    }

def pull_hls(url):
    res = _http_get_json(url, REQUEST_TIMEOUT)
    try:
        return res["data"]["media"][0]["url"]
    except Exception as e:
        _log(f"HLS resolve failed: {e}")
        return None

def get_url(**kwargs):
    return "{}?{}".format(_URL, urlencode(kwargs))

def get_categories():
    return CATEGORIES.keys()

def get_videos(category):
    videos = []
    content_ids = set()

    for item in data_items:
        if item.get("program_title") != category:
            continue
        cid = item.get("content_id")
        if not cid or cid in content_ids:
            continue
        content_ids.add(cid)

        name = item.get("date", "") or item.get("title", "") or "Video"
        thumb = item.get("thumbnail", "")
        genre = item.get("description", "")
        path = item.get("path")

        stream_link = pull_hls(path) if path else None
        if not stream_link:
            continue

        videos.append({
            "name": name,
            "thumb": thumb,
            "video": stream_link,
            "genre": genre,
        })

    return videos

def list_categories():
    xbmcplugin.setPluginCategory(_HANDLE, "Victory Channel")
    xbmcplugin.setContent(_HANDLE, "videos")

    for category in get_categories():
        meta = CATEGORIES[category]
        list_item = xbmcgui.ListItem(label=category)
        list_item.setArt({
            "thumb": meta["thumb"],
            "icon": meta["thumb"],
            "fanart": meta["thumb"],
        })
        list_item.setInfo("video", {
            "title": category,
            "genre": meta["genre"],
            "mediatype": "video",
        })
        url = get_url(action="listing", category=category)
        xbmcplugin.addDirectoryItem(_HANDLE, url, list_item, isFolder=True)

    xbmcplugin.addSortMethod(_HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(_HANDLE)

def list_videos(category):
    xbmcplugin.setPluginCategory(_HANDLE, category)
    xbmcplugin.setContent(_HANDLE, "videos")

    videos = get_videos(category)
    for video in videos:
        list_item = xbmcgui.ListItem(label=video["name"])
        list_item.setInfo("video", {
            "title": video["name"],
            "genre": video["genre"],
            "mediatype": "video",
        })
        list_item.setArt({
            "thumb": video["thumb"],
            "icon": video["thumb"],
            "fanart": video["thumb"],
        })
        list_item.setProperty("IsPlayable", "true")
        url = get_url(action="play", video=video["video"])
        xbmcplugin.addDirectoryItem(_HANDLE, url, list_item, isFolder=False)

    xbmcplugin.addSortMethod(_HANDLE, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(_HANDLE)

def play_video(path):
    play_item = xbmcgui.ListItem(path=path)
    xbmcplugin.setResolvedUrl(_HANDLE, True, listitem=play_item)

def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if params:
        action = params.get("action")
        if action == "listing":
            list_videos(params["category"])
        elif action == "play":
            play_video(params["video"])
        else:
            raise ValueError(f"Invalid paramstring: {paramstring}!")
    else:
        list_categories()

if __name__ == "__main__":
    router(sys.argv[2][1:])
