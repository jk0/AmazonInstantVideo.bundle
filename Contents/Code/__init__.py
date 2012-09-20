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


NAME = "Amazon Prime Instant Videos"
ICON = "icon-default.png"
ICON_SEARCH = "icon-search.png"
ICON_PREFS = "icon-prefs.png"
ART = "art-default.jpg"

AMAZON_URL = "https://www.amazon.com"
STREAM_URL = "http://www.amazon.com/gp/video/streaming/mini-mode.html?asin="

LIBRARY_URL = AMAZON_URL + "/gp/video/library/%s?show=all"
MOVIES_URL = AMAZON_URL + "/s/ref=PIVHPBB_Categories_MostPopular?rh=n%3A2858905011%2Cp_85%3A2470955011"
TV_URL = AMAZON_URL + "/s/ref=lp_2864549011_nr_p_85_0?rh=n%3A2625373011%2Cn%3A%212644981011%2Cn%3A%212644982011%2Cn%3A2858778011%2Cn%3A2864549011%2Cp_85%3A2470955011"
SEARCH_URL = AMAZON_URL + "/s/ref=sr_nr_p_85_0?rh=i:aps,p_85:1&keywords=%s"


def Start():
    Plugin.AddPrefixHandler("/video/amazonprime", MainMenu, NAME, ICON, ART)
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    ObjectContainer.title1 = NAME
    ObjectContainer.art = R(ART)
    ObjectContainer.view_group = "List"

    DirectoryObject.thumb = R(ICON)


def MainMenu():
    logged_in = account.logged_in()
    if not logged_in:
        logged_in = account.authenticate(AMAZON_URL)

    oc = ObjectContainer()

    if logged_in:
        match_pattern = "//div[contains(@id, \"result_\")]"

        oc.add(DirectoryObject(key=Callback(BrowseMenu, video_type="movies", match_pattern=match_pattern), title="Browse Movies"))
        oc.add(DirectoryObject(key=Callback(BrowseMenu, video_type="tv", match_pattern=match_pattern), title="Browse TV"))
        oc.add(DirectoryObject(key=Callback(LibraryMenu), title="Your Library"))
        oc.add(DirectoryObject(key=Callback(SearchMenu), title="Search", thumb=R(ICON_SEARCH)))

    oc.add(PrefsObject(title=L("Preferences"), thumb=R(ICON_PREFS)))

    return oc


def SearchMenu():
    oc = ObjectContainer()

    oc.add(InputDirectoryObject(key=Callback(Search, video_type="movies"), title="Search Movies", prompt="Search for a Movie", thumb=R(ICON_SEARCH)))
    oc.add(InputDirectoryObject(key=Callback(Search, video_type="tv"), title="Search TV", prompt="Search for a TV show", thumb=R(ICON_SEARCH)))

    return oc


def BrowseMenu(video_type, match_pattern, is_library=False, query=None):
    if query:
        query = query.replace(" ", "%20")
        browse_url = SEARCH_URL % query
    elif is_library:
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
        elif query:
            item_asin = item.attrib["name"].strip()
            item_title = list(item)[1][0][0].text.strip()
            item_image_link = list(item)[0][0][0].attrib["src"].strip()
        else:
            item_asin = item.attrib["name"].strip()
            item_title = list(item)[3][0][0].text.strip()
            item_image_link = list(item)[1][0][0].attrib["src"].strip()

        if video_type == "movies":
            videos.append((item_title, item_asin, item_image_link))
        else:
            seasons.append((item_title, item_asin, item_image_link))

    if query and (len(videos) == 0 and len(seasons) == 0):
        return MessageContainer("No Results", "No results were found for '%s'." % query)

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


def LibraryMenu():
    match_pattern = "//*[@class=\"lib-item\"]"

    oc = ObjectContainer()

    oc.add(DirectoryObject(key=Callback(BrowseMenu, video_type="movies", match_pattern=match_pattern, is_library=True), title="Movies"))
    oc.add(DirectoryObject(key=Callback(BrowseMenu, video_type="tv", match_pattern=match_pattern, is_library=True), title="TV"))

    return oc


def Search(query, video_type):
    return BrowseMenu(video_type=video_type, match_pattern="//div[contains(@id, \"result_\")]", query=query)


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
