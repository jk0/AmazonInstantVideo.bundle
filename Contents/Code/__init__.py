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

NAME = "Amazon Prime Instant Videos"
ICON = "icon-default.png"
ART = "art-default.jpg"

AMAZON_URL = "https://www.amazon.com"
STREAM_URL = "http://www.amazon.com/gp/video/streaming/mini-mode.html?asin="
ASSOC_TAG = "plco09-20"


def Start():
    Plugin.AddPrefixHandler("/video/amazonprime", MainMenu, NAME, ICON, ART)
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    ObjectContainer.title1 = NAME
    ObjectContainer.art = R(ART)
    ObjectContainer.view_group = "List"

    DirectoryObject.thumb = R(ICON)


def MainMenu():
    oc = ObjectContainer()

    oc.add(DirectoryObject(key=Callback(Library), title="Your Library"))
    oc.add(PrefsObject(title=L("Preferences"), thumb=R(ICON)))

    return oc


def Login():
    x = HTTP.Request(AMAZON_URL + "/?tag=%s" % ASSOC_TAG, errors="replace")
    x = HTTP.Request(AMAZON_URL + "/gp/sign-in.html?tag=%s" % ASSOC_TAG, errors="replace")

    cookies_url = AMAZON_URL + "/gp/sign-in.html?tag=%s" % ASSOC_TAG
    cookies = HTTP.CookiesForURL(cookies_url)

    params = {
        "path": "/gp/homepage.html",
        "useRedirectOnSuccess": "1",
        "protocol": "https",
        "sessionId": None,
        "action": "sign-in",
        "password": Prefs["password"],
        "email": Prefs["username"],
        "x": '62',
        "y": '11'
    }

    x = HTTP.Request(AMAZON_URL + "/gp/flex/sign-in/select.html?ie=UTF8&protocol=https&tag=%s" % ASSOC_TAG, values=params, errors="replace", immediate=True).headers


def Library():
    Login()

    oc = ObjectContainer()

    oc.add(DirectoryObject(key=Callback(LibrarySpecific, movies=True), title="Movies"))
    oc.add(DirectoryObject(key=Callback(LibrarySpecific, movies=False), title="TV"))

    return oc


def LibrarySpecific(movies=True):
    video_type = "movie" if movies else "tv"
    url = AMAZON_URL + "/gp/video/library/%s?show=all" % video_type

    html = HTML.ElementFromURL(url)
    purchased = html.xpath("//*[@class=\"lib-item\"]")

    videos = []
    seasons = []

    for item in purchased:
        item_asin = item.attrib["asin"].strip()
        item_type = item.attrib["type"].strip()
        item_title = list(item)[1][0].text.strip()
        item_image_link = list(item)[0][0][0].attrib["src"].strip()

        if item_type == "movie":
            videos.append((item_title, item_asin, item_image_link))
        else:
            seasons.append((item_title, item_asin, item_image_link))

    oc = ObjectContainer()

    for video in videos:
        video_url = STREAM_URL + video[1]

        if movies:
            oc.add(GetVideoObject(url=video_url, video_type="movie", title=video[0], thumb_url=video[2]))
        else:
            oc.add(GetVideoObject(url=video_url, video_type="episode", title=video[0], thumb_url=video[2]))

    for season in seasons:
        season_url = AMAZON_URL + "/gp/product/" + season[1]

        thumb = Resource.ContentsOfURLWithFallback(url=season[2], fallback=ICON)

        oc.add(DirectoryObject(key=Callback(TVSeason, season_url=season_url, season_thumb_url=season[2]), title=season[0], thumb=thumb))

    return oc


def TVSeason(season_url, season_thumb_url):
    html = HTML.ElementFromURL(season_url)
    episodes = html.xpath("//*[@class=\"episodeRow\" or @class=\"episodeRow current\"]")

    owned_episodes = []

    for episode in episodes:
        owned = True if list(episode)[7].text.lower() == "owned" else False

        if owned:
            episode_asin = episode.xpath("@asin")[0].strip()
            episode_title = episode.xpath("td/div/text()")[0].strip()
            episode_summary = episode.xpath("td/div/text()")[1].strip()

            owned_episodes.append((episode_asin, episode_title, episode_summary))

    oc = ObjectContainer()

    for owned_episode in owned_episodes:
        owned_episode_url = STREAM_URL + owned_episode[0]
        oc.add(GetVideoObject(url=owned_episode_url, video_type="episode", title=owned_episode[1], summary=owned_episode[2], thumb_url=season_thumb_url))

    return oc


def GetVideoObject(url, video_type, title=None, summary=None, thumb_url=None):
    thumb = Resource.ContentsOfURLWithFallback(url=thumb_url, fallback=ICON)

    if video_type == "episode":
        return EpisodeObject(key=WebVideoURL(url), rating_key=url, title=title, summary=summary, thumb=thumb)
    else:
        return MovieObject(key=WebVideoURL(url), rating_key=url, title=title, summary=summary, thumb=thumb)
