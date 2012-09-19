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

ASSOC_TAG = "plco09-20"

AMAZON_URL = "https://www.amazon.com"
STREAM_URL = "http://www.amazon.com/gp/video/streaming/mini-mode.html?asin="

LIBRARY_URL = AMAZON_URL + "/gp/video/library/%s?show=all"
MOVIES_URL = AMAZON_URL + "/s/ref=PIVHPBB_Categories_MostPopular?rh=n%3A2858905011%2Cp_85%3A2470955011"
TV_URL = AMAZON_URL + "/s/ref=lp_2864549011_nr_p_85_0?rh=n%3A2625373011%2Cn%3A%212644981011%2Cn%3A%212644982011%2Cn%3A2858778011%2Cn%3A2864549011%2Cp_85%3A2470955011"


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


def Start():
    Plugin.AddPrefixHandler("/video/amazonprime", MainMenu, NAME, ICON, ART)
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    ObjectContainer.title1 = NAME
    ObjectContainer.art = R(ART)
    ObjectContainer.view_group = "List"

    DirectoryObject.thumb = R(ICON)


def MainMenu():
    Login()

    oc = ObjectContainer()

    oc.add(DirectoryObject(key=Callback(Browse, video_type="movies", match_pattern="//div[contains(@id, \"result_\")]"), title="Browse Movies"))
    oc.add(DirectoryObject(key=Callback(Browse, video_type="tv", match_pattern="//div[contains(@id, \"result_\")]"), title="Browse TV"))
    oc.add(DirectoryObject(key=Callback(Library), title="Your Library"))
    oc.add(PrefsObject(title=L("Preferences"), thumb=R(ICON)))

    return oc


def Library():
    oc = ObjectContainer()

    oc.add(DirectoryObject(key=Callback(Browse, video_type="movies", match_pattern="//*[@class=\"lib-item\"]", is_library=True), title="Movies"))
    oc.add(DirectoryObject(key=Callback(Browse, video_type="tv", match_pattern="//*[@class=\"lib-item\"]", is_library=True), title="TV"))

    return oc


def Browse(video_type, match_pattern, is_library=False):
    if is_library:
        browse_url = LIBRARY_URL % video_type
    elif video_type == "movies":
        browse_url = MOVIES_URL
    else:
        browse_url = TV_URL

    html = HTML.ElementFromURL(browse_url)
    video_list = html.xpath(match_pattern)

    verify_ownership = True if is_library else False

    videos = []
    seasons = []

    # NOTE(jk0): Determine whether or not we're looking at movies or TV shows
    # which contain multiple episodes.
    for item in video_list:
        # TODO(jk0): Clean up this parsing mess.
        if is_library:
            item_asin = item.attrib["asin"].strip()
            item_title = list(item)[1][0].text.strip()
            item_image_link = list(item)[0][0][0].attrib["src"].strip()
        else:
            item_asin = item.attrib["name"].strip()
            item_title = list(item)[2][0][0].text.strip()
            item_image_link = list(item)[1][0][0].attrib["src"].strip()

        if video_type == "movies":
            videos.append((item_title, item_asin, item_image_link))
        else:
            seasons.append((item_title, item_asin, item_image_link))

    oc = ObjectContainer()

    # NOTE(jk0): Determine whether or not we're watching a movie or a TV show
    # since they require different video object types.
    for video in videos:
        video_url = STREAM_URL + video[1]

        if video_type == "movies":
            oc.add(GetVideoObject(url=video_url, video_type="movie", title=video[0], thumb_url=video[2]))
        else:
            oc.add(GetVideoObject(url=video_url, video_type="episode", title=video[0], thumb_url=video[2]))

    # NOTE(jk0): TV shows contain multiple episodes, so handle them
    # appropriately.
    for season in seasons:
        season_url = AMAZON_URL + "/gp/product/" + season[1]

        thumb = Resource.ContentsOfURLWithFallback(url=season[2], fallback=ICON)

        oc.add(DirectoryObject(key=Callback(TVSeason, season_url=season_url, season_thumb_url=season[2], verify_ownership=verify_ownership), title=season[0], thumb=thumb))

    return oc


def TVSeason(season_url, season_thumb_url, verify_ownership):
    html = HTML.ElementFromURL(season_url)
    episode_list = html.xpath("//*[@class=\"episodeRow\" or @class=\"episodeRow current\"]")

    episodes = []

    for episode in episode_list:
        if not verify_ownership or list(episode)[7].text == "Owned":
            # TODO(jk0): Clean up this parsing mess.
            episode_asin = episode.xpath("@asin")[0].strip()
            episode_title = episode.xpath("td/div/text()")[0].strip()
            episode_summary = episode.xpath("td/div/text()")[1].strip()

            episodes.append((episode_asin, episode_title, episode_summary))

    oc = ObjectContainer()

    for episode in episodes:
        episode_url = STREAM_URL + episode[0]

        oc.add(GetVideoObject(url=episode_url, video_type="episode", title=episode[1], summary=episode[2], thumb_url=season_thumb_url))

    return oc


def GetVideoObject(url, video_type, title=None, summary=None, thumb_url=None):
    thumb = Resource.ContentsOfURLWithFallback(url=thumb_url, fallback=ICON)

    if video_type == "episode":
        return EpisodeObject(key=WebVideoURL(url), rating_key=url, title=title, summary=summary, thumb=thumb)
    else:
        return MovieObject(key=WebVideoURL(url), rating_key=url, title=title, summary=summary, thumb=thumb)
