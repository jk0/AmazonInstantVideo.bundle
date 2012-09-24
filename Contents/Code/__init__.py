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

import account
import utils


PLUGIN_TITLE = "Amazon Instant Video"
PLUGIN_ICON_DEFAULT = "icon-default.png"
PLUGIN_ICON_SEARCH = "icon-search.png"
PLUGIN_ICON_PREFS = "icon-prefs.png"
PLUGIN_ICON_NEXT = "icon-next.png"
PLUGIN_ART = "art-default.jpg"

AMAZON_URL = "https://www.amazon.com"
MINI_PLAYER_URL = "http://www.amazon.com/gp/video/streaming/mini-mode.html?asin="

ACCOUNT_URL = AMAZON_URL + "/gp/video/%s/%s?show=all"
MOVIES_URL = AMAZON_URL + "/s/ref=PIVHPBB_Categories_MostPopular?rh=n%3A2858905011%2Cp_85%3A2470955011"
TV_URL = AMAZON_URL + "/s/ref=lp_2864549011_nr_p_85_0?rh=n%3A2864549011%2Cp_85%3A2470955011"
SEARCH_URL = AMAZON_URL + "/s/ref=sr_nr_p_85_0?url=search-alias=instant-video&keywords=%s"

BROWSE_PATTERN = "//div[contains(@id, 'result_')] | //div[@class='lib-item'] | //div[@class='innerItem']"
PAGINATION_PATTERN = "//span[@class='pagnNext']"


def Start():
    ObjectContainer.title1 = PLUGIN_TITLE
    ObjectContainer.art = R(PLUGIN_ART)

    DirectoryObject.thumb = R(PLUGIN_ICON_DEFAULT)
    VideoClipObject.thumb = R(PLUGIN_ICON_DEFAULT)
    InputDirectoryObject.thumb = R(PLUGIN_ICON_SEARCH)
    PrefsObject.thumb = R(PLUGIN_ICON_PREFS)
    NextPageObject.thumb = R(PLUGIN_ICON_NEXT)


@handler("/video/amazoninstantvideo", PLUGIN_TITLE, thumb=PLUGIN_ICON_DEFAULT, art=PLUGIN_ART)
def MainMenu():
    logged_in = account.authenticate()
    is_prime = account.is_prime()

    oc = ObjectContainer()

    if logged_in:
        if is_prime:
            oc.add(DirectoryObject(key=Callback(BrowseMenu, video_type="movies"), title="Browse Movies"))
            oc.add(DirectoryObject(key=Callback(BrowseMenu, video_type="tv"), title="Browse TV"))

        oc.add(DirectoryObject(key=Callback(LibraryMenu), title="Your Library"))

        if is_prime:
            oc.add(DirectoryObject(key=Callback(WatchlistMenu), title="Your Watchlist"))
            oc.add(DirectoryObject(key=Callback(SearchMenu), title="Search", thumb=R(PLUGIN_ICON_SEARCH)))

    oc.add(PrefsObject(title="Preferences"))

    return oc


@route("/video/amazoninstantvideo/searchmenu")
def SearchMenu():
    oc = ObjectContainer()

    oc.add(InputDirectoryObject(key=Callback(Search, video_type="movies"), title="Search Movies", prompt="Search for a Movie"))
    oc.add(InputDirectoryObject(key=Callback(Search, video_type="tv"), title="Search TV", prompt="Search for a TV show"))

    return oc


@route("/video/amazoninstantvideo/browsemenu")
def BrowseMenu(video_type, is_library=False, is_watchlist=False, query=None, pagination_url=None):
    if query:
        if not pagination_url:
            # NOTE(jk0): Only build a query URL if we're performing a new
            # search and not using pagination on a previous search.
            query = query.replace(" ", "%20")
            browse_url = SEARCH_URL % query
    elif is_library:
        browse_url = ACCOUNT_URL % ("library", video_type)
    elif is_watchlist:
        browse_url = ACCOUNT_URL % ("watchlist", video_type)
    elif video_type == "movies":
        browse_url = MOVIES_URL
    else:
        browse_url = TV_URL

    if pagination_url:
        browse_url = AMAZON_URL + pagination_url

    html = HTML.ElementFromURL(browse_url)
    video_list = html.xpath(BROWSE_PATTERN)

    verify_ownership = True if is_library else False

    videos = []
    seasons = []

    for item in video_list:
        if is_library:
            item_asin = item.xpath(".//@asin")[0]
            item_title = item.xpath(".//div[@class='title']/a/text()")[0].strip()
            item_image_link = item.xpath(".//div[@class='img-container']/a/img/@src")[0]
        elif is_watchlist:
            item_asin = item.xpath(".//div[@class='hover-hook']/a/@href")[0].split("/")[3]
            item_title = item.xpath(".//div[@class='hover-hook']/a/img/@alt")[0]
            item_image_link = item.xpath(".//div[@class='hover-hook']/a/img/@src")[0]
        else:
            item_asin = item.xpath(".//@name")[0]
            item_title = item.xpath(".//div[@class='data']/h3/a/text()")[0].strip()
            item_image_link = item.xpath(".//div[@class='image']/a/img/@src")[0]

        if video_type == "movies":
            videos.append((item_title, item_asin, item_image_link))
        else:
            seasons.append((item_title, item_asin, item_image_link))

    oc = ObjectContainer()

    for video in videos:
        video_url = MINI_PLAYER_URL + video[1]

        if video_type == "movies":
            oc.add(GetVideoObject(url=video_url, video_type="movie", title=video[0], thumb_url=video[2]))
        else:
            oc.add(GetVideoObject(url=video_url, video_type="episode", title=video[0], thumb_url=video[2]))

    for season in seasons:
        season_url = AMAZON_URL + "/gp/product/" + season[1]

        thumb = Resource.ContentsOfURLWithFallback(url=season[2], fallback=PLUGIN_ICON_DEFAULT)

        oc.add(DirectoryObject(key=Callback(TVSeason, season_url=season_url, season_thumb_url=season[2], verify_ownership=verify_ownership), title=season[0], thumb=thumb))

    pagination = html.xpath(PAGINATION_PATTERN)
    if len(pagination) > 0:
        pagination_url = pagination[0].xpath("//a[@class='pagnNext']/@href")[0]

        oc.add(NextPageObject(key=Callback(BrowseMenu, video_type=video_type, query=query, pagination_url=pagination_url), title="Next..."))

    if len(oc) == 0:
        return MessageContainer("No Results", "No results were found.")

    return oc


@route("/video/amazoninstantvideo/librarymenu")
def LibraryMenu():
    oc = ObjectContainer()

    oc.add(DirectoryObject(key=Callback(BrowseMenu, video_type="movies", is_library=True), title="Movies"))
    oc.add(DirectoryObject(key=Callback(BrowseMenu, video_type="tv", is_library=True), title="TV"))

    return oc


@route("/video/amazoninstantvideo/watchlistmenu")
def WatchlistMenu():
    oc = ObjectContainer()

    oc.add(DirectoryObject(key=Callback(BrowseMenu, video_type="movies", is_watchlist=True), title="Movies"))
    oc.add(DirectoryObject(key=Callback(BrowseMenu, video_type="tv", is_watchlist=True), title="TV"))

    return oc


@route("/video/amazoninstantvideo/search")
def Search(query, video_type):
    return BrowseMenu(video_type=video_type, query=query)


@route("/video/amazoninstantvideo/tvseason")
def TVSeason(season_url, season_thumb_url, verify_ownership):
    html = HTML.ElementFromURL(season_url)
    episode_list = html.xpath("//*[contains(@class, 'episodeRow')]")

    episodes = []

    for episode in episode_list:
        episode_owned = True if episode.xpath(".//td[last()-2]/text()")[0].strip() == "Owned" else False

        # NOTE(jk0): Not sure why this was converted to a string?
        if verify_ownership == "False" or episode_owned:
            episode_asin = episode.xpath(".//@asin")[0]
            episode_title = episode.xpath(".//td[@title]/div/text()")[0].strip()
            episode_summary = episode.xpath(".//td/div[contains(@style, 'overflow-y')]/text()")[0].strip()

            episodes.append((episode_asin, episode_title, episode_summary))

    oc = ObjectContainer()

    for episode in episodes:
        episode_url = MINI_PLAYER_URL + episode[0]

        oc.add(GetVideoObject(url=episode_url, video_type="episode", title=episode[1], summary=episode[2], thumb_url=season_thumb_url))

    return oc


@route("/video/amazoninstantvideo/getvideoobject")
def GetVideoObject(url, video_type, title=None, summary=None, thumb_url=None):
    thumb = Resource.ContentsOfURLWithFallback(url=thumb_url, fallback=PLUGIN_ICON_DEFAULT)

    if video_type == "episode":
        return EpisodeObject(key=Callback(VideoDetails, url=url), rating_key=url, items=video_items(url), title=title, summary=summary, thumb=thumb)
    else:
        return MovieObject(key=Callback(VideoDetails, url=url), rating_key=url, items=video_items(url), title=title, summary=summary, thumb=thumb)


@route("/video/amazoninstantvideo/videodetails")
def VideoDetails(url):
    oc = ObjectContainer()

    oc.add(VideoClipObject(key=Callback(VideoDetails, url=url), rating_key=url, items=video_items(url)))

    return oc


@route("/video/amazoninstantvideo/playvideo")
@indirect
def PlayVideo(url):
    try:
        flash_vars = utils.parse_flash_vars(url)
        rtmp_url, clip_stream = utils.prepare_rtmp_info(flash_vars)
    except KeyError:
        return MessageContainer("Error", "Unable to load video.")

    return IndirectResponse(VideoClipObject, key=RTMPVideoURL(url=rtmp_url, clip=clip_stream))


def video_items(url):
    return [
        MediaObject(
            parts=[
                PartObject(key=Callback(PlayVideo, url=url))
            ]
        )
    ]
