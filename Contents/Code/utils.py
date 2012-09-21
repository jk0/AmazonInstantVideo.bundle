#   Copyright 2012 Josh Kearney
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import time


def parse_flash_vars(url):
    re_flash = Regex("'flashVars', '(.*?)' \+ new Date\(\)\.getTime\(\)\+ '(.*?)'", Regex.DOTALL)

    page_content = HTTP.Request(url, follow_redirects=False).content

    flash = re_flash.findall(page_content)
    flash = (flash[0][0] + flash[0][1]).split("&")

    # TODO(jk0): Figure out what these are for and if they are really needed.
    flash_vars = {
        "token": "",
        "deviceTypeID": "A13Q6A55DBZB7M",
        "version": "1",
        "firmware": "WIN%2010,0,181,14%20PlugIn",
        "customerID": "",
        "format": "json",
        "deviceID": "",
        "asin": ""
    }

    for var in flash:
        var = var.split("=")
        if var[0] == "token":
            flash_vars[var[0]] = var[1]
        elif var[0] == "customer":
            flash_vars["customerID"] = var[1]
        elif var[0] == "ASIN":
            flash_vars["asin"] = var[1]
        elif var[0] == "pageType":
            flash_vars["pageType"] = var[1]
        elif var[0] == "UBID":
            flash_vars["UBID"] = var[1]
        elif var[0] == "sessionID":
            flash_vars["sessionID"] = var[1]
        elif var[0] == "userAgent":
            flash_vars["userAgent"] = var[1]

    flash_vars["deviceID"] = flash_vars["customerID"] + str(int(time.time() * 1000)) + flash_vars["asin"]

    return flash_vars


def prepare_rtmp_info(flash_vars):
    stream_url = "https://atv-ps.amazon.com/cdp/catalog/GetStreamingUrlSets?format=json&version=%(version)s&asin=%(asin)s&deviceTypeID=%(deviceTypeID)s&xws-fa-ov=false&token=%(token)s&firmware=%(firmware)s&customerID=%(customerID)s&deviceID=%(deviceID)s" % flash_vars

    stream_data = JSON.ObjectFromURL(stream_url)
    stream_json = stream_data["message"]["body"]["urlSets"]["streamingURLInfoSet"][0]["streamingURLInfo"]

    streams = []
    for stream in stream_json:
        if stream["drm"] == "NONE":
            streams.append((int(stream["bitrate"]), stream["url"]))

    # NOTE(jk0): Use the highest bitrate available.
    streams.sort(key=lambda x: x[0], reverse=True)
    rtmp_url = streams[0][1]

    # NOTE(jk0): What?
    clip_stream = rtmp_url.split("ondemand/")[1].split("?")[0].replace(".mp4", "")

    return rtmp_url, clip_stream
