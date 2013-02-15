#   Copyright 2012-2013 Josh Kearney
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


common = SharedCodeService.common
c = SharedCodeService.constants


def Start():
    ObjectContainer.title1 = c.PLUGIN_TITLE


@handler("/video/amazoninstantvideo", c.PLUGIN_TITLE)
def MainMenu():
    logged_in = account.logged_in()
    if not logged_in:
        logged_in = account.authenticate()

    is_prime = account.is_prime()

    oc = ObjectContainer()

    if logged_in:
        if is_prime:
            oc.add(DirectoryObject(key=Callback(BrowseMenu, browse_type="movie"), title="Browse Movies"))
            oc.add(DirectoryObject(key=Callback(BrowseMenu, browse_type="tv"), title="Browse TV Shows"))

        oc.add(DirectoryObject(key=Callback(BrowseMenu, is_library=True), title="Your Library"))

        if is_prime:
            oc.add(DirectoryObject(key=Callback(BrowseMenu, is_watchlist=True), title="Your Watchlist"))
            oc.add(SearchDirectoryObject(title="Search", prompt="Search for a Movie or TV Show"))

    oc.add(PrefsObject(title="Preferences"))

    return oc


@route("/video/amazoninstantvideo/browsemenu", is_library=bool, is_watchlist=bool)
def BrowseMenu(is_library=False, is_watchlist=False, browse_type=None, pagination_url=None):
    if is_library:
        title = "Your Library"
        browse_url = c.LIBRARY_URL
    elif is_watchlist:
        title = "Your Watchlist"
        browse_url = c.WATCHLIST_URL
    elif browse_type == "movie":
        title = "Browse Movies"
        browse_url = c.MOVIES_URL
    else:
        title = "Browse TV Shows"
        browse_url = c.TV_URL

    if pagination_url:
        browse_url = c.AMAZON_URL + pagination_url

    page = HTML.ElementFromURL(browse_url)
    items = page.xpath(c.BROWSE_PATTERN)

    oc = ObjectContainer(title2=title)

    for item in items:
        try:
            asin, title, thumb = common.parse_item(item)
        except IndexError:
            continue

        if browse_type == "tv" or common.is_season(title):
            oc.add(SeasonObject(key=Callback(TVSeason, asin=asin, title=title, is_library=is_library), rating_key=asin, title=title, thumb=thumb))
        else:
            oc.add(MovieObject(url=c.PRODUCT_URL % asin, source_title=c.PLUGIN_TITLE, title=title, thumb=thumb))

    pagination_url = page.xpath(c.PAGINATION_PATTERN)
    if len(pagination_url) > 0:
        oc.add(NextPageObject(key=Callback(BrowseMenu, browse_type=browse_type, pagination_url=pagination_url[0]), title="Next..."))

    if len(oc) == 0:
        return ObjectContainer(header="No Results", message="No results were found.")

    return oc


@route("/video/amazoninstantvideo/tvseason", is_library=bool)
def TVSeason(asin, title, is_library):
    page = HTML.ElementFromURL(c.PRODUCT_URL % asin)
    episodes = page.xpath(c.EPISODE_BROWSE_PATTERN)
    thumb = common.generate_thumb(page)

    oc = ObjectContainer(title2=title)

    for episode in episodes:
        if not is_library or common.is_owned(episode):
            try:
                asin, title, summary = common.parse_episode(episode)
            except IndexError:
                continue

            oc.add(EpisodeObject(url=c.PRODUCT_URL % asin, source_title=c.PLUGIN_TITLE, title=title, summary=summary, thumb=thumb))

    return oc
