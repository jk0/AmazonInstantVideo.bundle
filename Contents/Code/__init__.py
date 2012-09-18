import operator
import time


RE_FLASHVARS = Regex("'flashVars', '(.*?)' \+ new Date\(\)\.getTime\(\)\+ '(.*?)'", Regex.DOTALL)
RE_SWFURL = Regex("avodSwfUrl = '(.*?)'\;")
RE_IDENT_IP = Regex('<fcs><ip>(.+?)</ip></fcs>')

NAME = "Amazon Prime Instant Videos"
ICON = "icon-default.png"
ART = "art-default.jpg"

ASSOC_TAG = "plco09-20"
FIRMWARE = "WIN%2010,0,181,14%20PlugIn"
DEVICEID = "A36VLPLQERSUGW1347221081338B0029Z3EH0"

TV_LIST = "/s/ref=sr_nr_n_1?rh=n%3A2625373011%2Cn%3A%212644981011%2Cn%3A%212644982011%2Cn%3A2858778011%2Cp_85%3A2470955011%2Cn%3A2864549011&bbn=2858778011&ie=UTF8&qid=1334413870&rnid=2858778011"


def Start():
    Plugin.AddPrefixHandler("/video/amazonvod", MainMenu, NAME, ICON, ART)
    Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

    ObjectContainer.title1 = NAME
    ObjectContainer.art = R(ART)
    ObjectContainer.view_group = "List"

    DirectoryObject.thumb = R(ICON)



def MainMenu():
    used_selections = {"genre": False, "network": False}

    oc = ObjectContainer()
    oc.add(DirectoryObject(key=Callback(MovieList), title="Movies"))
    oc.add(DirectoryObject(key=Callback(TVList, url=TV_LIST,
           usedSelections=used_selections), title="TV"))
    oc.add(DirectoryObject(key=Callback(SearchMenu), title="Search"))
    oc.add(DirectoryObject(key=Callback(Library), title="Your Library"))
    oc.add(PrefsObject(title=L("Preferences"), thumb=R(ICON)))

    return oc


def SearchMenu():
    oc = ObjectContainer()
    oc.add(InputDirectoryObject(key=Callback(Search, tvSearch=False),
           title="Search Movies",
           summary="Search Amazon Prime Instant Videos", thumb=R(ICON)))
    oc.add(InputDirectoryObject(key=Callback(Search), title="Search TV Shows",
           summary="Search Amazon Prime Instant TV Shows", thumb=R(ICON)))

    return oc


def Search(query, url=None, tvSearch=True):
    string = "/s/ref=sr_nr_n_0?rh=n%3A2625373011%2Cn%3A%212644981011%2Cn%3A%212644982011%2Cn%3A2858778011%2Ck%3A"
    string += String.Quote(query, usePlus=True)

    if tvSearch:
        string += "%2Cp_85%3A2470955011%2Cn%3A2864549011&bbn=2858778011&keywords="
    else:
        string += "%2Cp_85%3A2470955011%2Cn%3A2858905011&bbn=2858778011&keywords="

    string += String.Quote(query, usePlus=True)

    if tvSearch:
        return ResultsList(None, url=string, onePage=True)
    else:
        return ResultsList(None, url=string, onePage=True, tvList=False)


def Login():
    x = HTTP.Request("https://www.amazon.com/?tag=%s" % ASSOC_TAG,
                     errors="replace")
    x = HTTP.Request("https://www.amazon.com/gp/sign-in.html?tag=%s" %
                     ASSOC_TAG, errors="replace")

    cookies_url = "https://www.amazon.com/gp/sign-in.html?tag=%s" % ASSOC_TAG
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

    x = HTTP.Request("https://www.amazon.com/gp/flex/sign-in/select.html?ie=UTF8&protocol=https&tag=%s" %
                     ASSOC_TAG, values=params, errors="replace",
                     immediate=True).headers


def Library():
    Login()
    oc = ObjectContainer()
    oc.add(DirectoryObject(key=Callback(LibrarySpecific, movies=True),
                           title="Movies"))
    oc.add(DirectoryObject(key=Callback(LibrarySpecific, movies=False),
                           title="TV"))

    return oc


def LibrarySpecific(movies=True):
    if movies:
        url = "https://www.amazon.com/gp/video/library/movie?show=all"
    else:
        url = "https://www.amazon.com/gp/video/library/tv?show=all"

    element = HTML.ElementFromURL(url)

    purchasedList = element.xpath("//*[@class=\"lib-item\"]")
    videos = list()
    seasons = list()

    for i in range(0, len(purchasedList)):
        asin = purchasedList[i].xpath("//@asin")[0]
        imageLink = purchasedList[i].xpath("//div/a/img/@src")[0]
        title = purchasedList[i].xpath("//*[@class=\"title\"]/a/text()")[0]

        if purchasedList[i].xpath("//div/@type")[0] == "movie":
            videos.append((title, asin, imageLink))
        else:
            seasons.append((title, asin, imageLink))

    oc = ObjectContainer()

    for i in range(0, len(videos)):
        url = "http://www.amazon.com/gp/video/streaming/mini-mode.html?asin=" + videos[i][1]
        if movies:
            video = GetVideoObject(url=url, video_type="movie",
                                   title=videos[i][0],thumb=videos[i][0])
            oc.add(video)
        else:
            video = GetVideoObject(url=url, video_type="episode",
                                   title=videos[i][0], thumb=videos[i][0])
            oc.add(video)

    for i in range(0, len(seasons)):
        season_url = "https://www.amazon.com/gp/product/" + seasons[i][1]
        thumb = Resource.ContentsOfURLWithFallback(url=seasons[i][2],
                                                   fallback=ICON)

        oc.add(DirectoryObject(key=Callback(TVIndividualSeason,
                               url=season_url), title=seasons[i][0],
                               thumb=thumb))

    return oc


def MovieList(url=None, usedSelections=None):
    summary = "Search Amazon Prime Instant Videos"
    oc = ObjectContainer()
    oc.add(InputDirectoryObject(key=Callback(Search, tvSearch=False),
                                title="Search Movies",
                                summary=summary, thumb=R(ICON)))

    return oc


def TVList(url=None, usedSelections=None):
    oc = ObjectContainer()

    shownUnorganized = False

    tvPage = HTML.ElementFromURL("http://www.amazon.com" + url)

    links = tvPage.xpath("//div[@id='refinements']//h2[. = 'TV Show']/following-sibling::ul[1 = count(preceding-sibling::h2[1] | ../h2[. = 'TV Show'])]/li/a/@href")

    if (len(links) > 0):
        tvShowsLink = links[len(links) - 1]

        if "sr_sa_p_lbr_tv_series_brow" in tvShowsLink:
            oc.add(DirectoryObject(key=Callback(TVShows, url=tvShowsLink),
                                   title="Shows"))
        else:
            oc.add(DirectoryObject(key=Callback(TVShowsNotNice, url=url),
                                   title="Shows"))
    else:
        oc.add(DirectoryObject(key=Callback(ResultsList, url=url,
                               onePage=True),
                               title="All TV Shows (Unorganized)"))
        shownUnorganized = True

    if not usedSelections['genre']:
        links = tvPage.xpath("//div[@id='refinements']//h2[. = 'Genre']/following-sibling::ul[1 = count(preceding-sibling::h2[1] | ../h2[. = 'Genre'])]/li/a/@href")
        if len(links) > 0:
            genresLink = links[len(links) - 1]

            if "sr_sa_p_n_theme_browse-bin" in genresLink:
                oc.add(DirectoryObject(key=Callback(TVSubCategories,
                                       url=genresLink, category="Genre",
                                       usedSelections=usedSelections),
                                       title="Genres"))
            else:
                oc.add(DirectoryObject(key=Callback(TVNotNiceSubCategories,
                                       url=url, category="Genre",
                                       usedSelections=usedSelections),
                                       title="Genres"))

    if not usedSelections['network']:
        links = tvPage.xpath("//div[@id='refinements']//h2[. = 'Content Provider']/following-sibling::ul[1 = count(preceding-sibling::h2[1] | ../h2[. = 'Content Provider'])]/li/a/@href")
        if len(links) > 0:
            networksLink = links[len(links) - 1]

            if "sr_sa_p_studio" in networksLink:
                oc.add(DirectoryObject(key=Callback(TVSubCategories,
                                       url=networksLink,
                                       category="Content Provider",
                                       usedSelections=usedSelections),
                                       title="Networks"))
            else:
                oc.add(DirectoryObject(key=Callback(TVNotNiceSubCategories,
                                       url=url, category="Content Provider",
                                       usedSelections=usedSelections),
                                       title="Networks"))

    if not shownUnorganized:
        oc.add(DirectoryObject(key=Callback(ResultsList, url=url,
                                            onePage=True),
                               title="All TV Shows (Unorganized)"))

    return oc


def TVSubCategories(url=None, category=None, usedSelections=None):
    if category == "Content Provider":
        usedSelections["network"] = True

    if category == "Genre":
        usedSelections["genre"] = True

    tvGenrePage = HTML.ElementFromURL("http://www.amazon.com" + url)

    listOfGenresLinks = tvGenrePage.xpath("//*[@class='c3_ref refList']//a/@href")
    listOfGenres = tvGenrePage.xpath("//*[@class='c3_ref refList']//a")
    listOfGenresNames = listOfGenres[0].xpath("//*[@class='refinementLink']/text()")

    oc = ObjectContainer()
    for i in range(0, len(listOfGenresLinks)):
        oc.add(DirectoryObject(key=Callback(TVList,
                               usedSelections=usedSelections,
                               url=listOfGenresLinks[i]),
                               title=listOfGenresNames[i]))

    return oc


def TVNotNiceSubCategories(url=None, category=None, usedSelections=None):
    if category == "Content Provider":
        usedSelections["network"] = True

    if category == "Genre":
        usedSelections["genre"] = True

    tvGenrePage = HTML.ElementFromURL("http://www.amazon.com" + url)

    genreList = tvGenrePage.xpath("//div[@id='refinements']//h2[. = '" + category + "']/following-sibling::ul[1 = count(preceding-sibling::h2[1] | ../h2[. = '" + category + "'])]//*[@class='refinementLink']/text()")

    genreLinks = tvGenrePage.xpath("//div[@id='refinements']//h2[. = '" + category + "']/following-sibling::ul[1 = count(preceding-sibling::h2[1] | ../h2[. = '" + category + "'])]/li/a/@href")

    pairs = list()

    for i in range(0, len(genreList)):
        pairs.append((genreList[i], genreLinks[i]))

    sortedPairs = sorted(pairs, key=operator.itemgetter(0))

    oc = ObjectContainer()
    for i in range(0, len(genreList)):
        oc.add(DirectoryObject(key=Callback(TVList,
                               usedSelection=usedSelection,
                               url=sortedPairs[i][1]),
                               title=sortedPairs[i][0]))

    return oc


def TVShows(url=None):
    tvShowPage = HTML.ElementFromURL("http://www.amazon.com" + url)

    listOfShowsLinks = tvShowPage.xpath("//*[@class='c3_ref refList']//a/@href")
    listOfShows = tvShowPage.xpath("//*[@class='c3_ref refList']//a")

    oc = ObjectContainer()

    if len(listOfShows) > 0:
        listOfShowsNames = listOfShows[0].xpath("//*[@class='refinementLink']/text()")

        for i in range(0, len(listOfShowsLinks)):
            oc.add(DirectoryObject(key=Callback(ResultsList,
                                   url=listOfShowsLinks[i], sort=True),
                                   title=listOfShowsNames[i]))

    return oc


def TVShowsNotNice(url=None):
    tvGenrePage = HTML.ElementFromURL("http://www.amazon.com" + url)

    showList = tvGenrePage.xpath("//div[@id='refinements']//h2[. = '" + "TV Show" + "']/following-sibling::ul[1 = count(preceding-sibling::h2[1] | ../h2[. = '" + "TV Show" + "'])]//*[@class='refinementLink']/text()")

    showLinks = tvGenrePage.xpath("//div[@id='refinements']//h2[. = '" + "TV Show" + "']/following-sibling::ul[1 = count(preceding-sibling::h2[1] | ../h2[. = '" + "TV Show" + "'])]/li/a/@href")

    pairs = list()
    for i in range(0, len(showList)):
        pairs.append((showList[i], showLinks[i]))

    sortedPairs = sorted(pairs, key=operator.itemgetter(0))

    oc = ObjectContainer()
    for i in range(0, len(showList)):
        oc.add(DirectoryObject(key=Callback(TVList, url=sortedPairs[i][1]),
                               title=sortedPairs[i][0]))

    return oc


def ResultsList(url=None, onePage=False, tvList=True, sort=False):
    oc = ObjectContainer()

    seasonsPage = HTML.ElementFromURL("http://www.amazon.com" + url)
    seasons = list()

    newURL = ""

    if (len(seasonsPage.xpath('//*[@class="pagnNext"]')) > 0) and not onePage:
        nextLoopQuit = False
    else:
        nextLoopQuit = True

    while True:
        if len(seasonsPage.xpath("//*[@id='atfResults' or @id='btfResults']")) > 0:
            listOfSeasons = seasonsPage.xpath("//*[@id='atfResults' or @id='btfResults']")[0]
            listOfSeasonsNames = listOfSeasons.xpath('//*[@class="title"]/a/text()')
            listOfSeasonsLinks = listOfSeasons.xpath('//*[@class="title"]/a/@href')
            listOfSeasonsImages = listOfSeasons.xpath('//*[@class="image"]/a/img/@src')

            Log(listOfSeasonsLinks[0].partition("/ref=sr_")[0].rpartition("/dp/")[2])

            for i in range(0, len(listOfSeasonsNames)):
                seasons.append((
                    listOfSeasonsNames[i],
                    listOfSeasonsLinks[i],
                    listOfSeasonsImages[i],
                    listOfSeasonsLinks[i].partition("/ref=sr_")[0].rpartition(
                        "/dp/")[2]))

            try:
                newURL = seasonsPage.xpath("//*[@id=\"pagnNextLink\"]")[0].xpath("@href")[0]
            except:
                break

            if nextLoopQuit:
                break

            seasonsPage = HTML.ElementFromURL("http://www.amazon.com" + newURL)
            if (len(seasonsPage.xpath("//*[@class=\"pagnNext\"]")) > 0):
                nextLoopQuit = False
            else:
                nextLoopQuit = True
        else:
            return ObjectContainer(header=NAME, message="Sorry, no results.")

    sortedSeasonPairs = seasons

    if sort:
        sortedSeasonPairs = sorted(seasons, key=operator.itemgetter(0))

    if tvList:
        for i in range(0, len(sortedSeasonPairs)):
            thumb = Resource.ContentsOfURLWithFallback(
                url=sortedSeasonPairs[i][2],
                fallback=ICON)
            oc.add(DirectoryObject(key=Callback(TVIndividualSeason,
                                   url=sortedSeasonPairs[i][1]),
                                   title=sortedSeasonPairs[i][0],
                                   thumb=thumb))
    else:
        for i in range(0, len(sortedSeasonPairs)):
            url = "http://www.amazon.com/gp/video/streaming/mini-mode.html?asin=" + sortedSeasonPairs[i][3]
            thumb = Resource.ContentsOfURLWithFallback(url=sortedSeasonPairs[i][2], fallback=ICON)
            video = GetVideoObject(url=url, video_type="episode",
                                   title=sortedSeasonPairs[i][0],
                                   thumb=sortedSeasonPairs[i][2])
            oc.add(video)

    if onePage and len(newURL) > 0:
        oc.add(DirectoryObject(key=Callback(ResultsList, url=newURL,
                               onePage=True), title="Next Page"))

    return oc


def TVIndividualSeason(url=None):
    episodesPage = HTML.ElementFromURL(url)

    listOfEpisodesTable = episodesPage.xpath('//*[@class="episodeRow" or @class="episodeRow current"]')

    listOfEpisodesTitles = list()
    listOfEpisodesASIN = list()
    listOfEpisodesSummaries = list()

    for i in range(0, len(listOfEpisodesTable)):
        listOfEpisodesTitles.append(listOfEpisodesTable[i].xpath("td/div/text()")[0])
        listOfEpisodesASIN.append(listOfEpisodesTable[i].xpath("@asin")[0])
        listOfEpisodesSummaries.append(listOfEpisodesTable[i].xpath("td/div/text()")[1])

    oc = ObjectContainer()
    for i in range(0, len(listOfEpisodesTable)):
        url = "http://www.amazon.com/gp/video/streaming/mini-mode.html?asin=" + listOfEpisodesASIN[i]
        video = GetVideoObject(url=url, video_type="episode",
                               title=listOfEpisodesTitles[i],
                               summary=listOfEpisodesSummaries[i])
        oc.add(video)

    return oc


def GetVideoObject(url, video_type, title="", summary="", thumb=None):
    thumb = Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)

    items = [
        MediaObject(
            parts=[PartObject(key=Callback(PlayVideo, url=url, bitrate=2500))],
            bitrate=2500
        ),
        MediaObject(
            parts=[PartObject(key=Callback(PlayVideo, url=url, bitrate=1328))],
            bitrate=1328
        ),
        MediaObject(
            parts=[PartObject(key=Callback(PlayVideo, url=url, bitrate=996))],
            bitrate=996
        ),
        MediaObject(
            parts=[PartObject(key=Callback(PlayVideo, url=url, bitrate=664))],
            bitrate=664
        ),
        MediaObject(
            parts=[PartObject(key=Callback(PlayVideo, url=url, bitrate=348))],
            bitrate=348
        )
    ]

    if video_type == "episode":
        return EpisodeObject(key=url, rating_key=url, title=title,
                             summary=summary, thumb=thumb)
    else:
        return MovieObject(key=url, rating_key=url, title=title,
                           summary=summary, thumb=thumb)


@indirect
def PlayVideo(url, bitrate):
    swfUrl, values, owned, cookies = GetFlashVars(url)
    values['deviceID'] = values['customerID'] + str(int(time.time() * 1000)) + values['asin']
    streamUrl =  STREAM_URL % (values['asin'], values['deviceTypeID'], values['token'], FIRMWARE, values['customerID'], DEVICEID)
    stream_data = JSON.ObjectFromURL(streamUrl, headers={'Cookie':cookies})
    streams = stream_data['message']['body']['urlSets']['streamingURLInfoSet'][0]['streamingURLInfo']
    rtmp_url = streams[-1]['url']

    protocolSplit = rtmp_url.split("://")
    pathSplit   = protocolSplit[1].split("/")
    hostname    = pathSplit[0]
    appName     = protocolSplit[1].split(hostname + "/")[1].split('/')[0]    
    streamAuth  = rtmp_url.split(appName+'/')[1].split('?')
    stream      = streamAuth[0].replace('.mp4','')
    Log(stream)
    auth        = streamAuth[1]
    identurl = 'http://'+hostname+'/fcs/ident'
    ident = HTTP.Request(identurl).content
    ip = RE_IDENT_IP.findall(ident)[0]
    basertmp = 'rtmpe://'+ip+':1935/'+appName+'?_fcs_vhost='+hostname+'&ovpfv=2.1.4&'+auth
    Log(basertmp)
    finalUrl = basertmp
    #finalUrl += " playpath=" + stream 
    #finalUrl += " pageurl=" + url
    #finalUrl += " swfurl=" + swfUrl + " swfvfy=true"

    return IndirectResponse(VideoClipObject, key=RTMPVideoURL(url=basertmp, clip=stream, swf_url=swfUrl))
    #return IndirectResponse(VideoClipObject, key=RTMPVideoURL(url=finalUrl))
'''
    try:
        rtmpurls, streamSessionID, cdn, title = GETSTREAMS(getstream)
    except:
        return PLAYTRAILER_RESOLVE()
    if cdn == 'limelight':
        xbmcgui.Dialog().ok('Limelight CDN','Limelight uses swfverfiy2. Playback may fail.')
    if rtmpurls <> False:
        basertmp, ip = PLAY(rtmpurls,swfUrl=swfUrl,title=title)
    if streamSessionID <> False:
        epoch = str(int(time.mktime(time.gmtime()))*1000)
        USurl =  'https://atv-ps.amazon.com/cdp/usage/UpdateStream'
        USurl += '?device_type_id='+values['deviceTypeID']
        USurl += '&deviceTypeID='+values['deviceTypeID']
        USurl += '&streaming_session_id='+streamSessionID
        USurl += '&operating_system='
        USurl += '&timecode=45.003'
        USurl += '&flash_version=WIN%2010,3,181,14%20PlugIn'
        USurl += '&asin='+values['asin']
        USurl += '&token='+values['token']
        USurl += '&browser='+urllib.quote_plus(values['userAgent'])
        USurl += '&server_id='+ip
        USurl += '&client_version='+swfUrl.split('/')[-1]
        USurl += '&unique_browser_id='+values['UBID']
        USurl += '&device_id='+values['deviceID']
        USurl += '&format=json'
        USurl += '&version=1'
        USurl += '&page_type='+values['pageType']
        USurl += '&start_state=Video'
        USurl += '&amazon_session_id='+values['sessionID']
        USurl += '&event=STOP'
        USurl += '&firmware=WIN%2010,3,181,14%20PlugIn'
        USurl += '&customerID='+values['customerID']
        USurl += '&deviceID='+values['deviceID']
        USurl += '&source_system=http://www.amazon.com'
        USurl += '&http_referer=ecx.images-amazon.com'
        USurl += '&event_timestamp='+epoch
        USurl += '&encrypted_customer_id='+values['customerID']
        print common.getURL(USurl,'atv-ps.amazon.com',useCookie=True)

        epoch = str(int(time.mktime(time.gmtime()))*1000)
        surl =  'https://atv-ps.amazon.com/cdp/usage/ReportStopStreamEvent'
        surl += '?deviceID='+values['deviceID']
        surl += '&source_system=http://www.amazon.com'
        surl += '&format=json'
        surl += '&event_timestamp='+epoch
        surl += '&encrypted_customer_id='+values['customerID']
        surl += '&http_referer=ecx.images-amazon.com'
        surl += '&device_type_id='+values['deviceTypeID']
        surl += '&download_bandwidth=9926.295518207282'
        surl += '&device_id='+values['deviceTypeID']
        surl += '&from_mode=purchased'
        surl += '&operating_system='
        surl += '&version=1'
        surl += '&flash_version=LNX%2010,3,181,14%20PlugIn'
        surl += '&url='+urllib.quote_plus(basertmp)
        surl += '&streaming_session_id='+streamSessionID
        surl += '&browser='+urllib.quote_plus(values['userAgent'])
        surl += '&server_id='+ip
        surl += '&client_version='+swfUrl.split('/')[-1]
        surl += '&unique_browser_id='+values['UBID']
        surl += '&amazon_session_id='+values['sessionID']
        surl += '&page_type='+values['pageType']
        surl += '&start_state=Video'
        surl += '&token='+values['token']
        surl += '&to_timecode=3883'
        surl += '&streaming_bit_rate=348'
        surl += '&new_streaming_bit_rate=2500'
        surl += '&asin='+values['asin']
        surl += '&deviceTypeID='+values['deviceTypeID']
        surl += '&firmware=WIN%2010,3,181,14%20PlugIn'
        surl += '&customerID='+values['customerID']
        print common.getURL(surl,'atv-ps.amazon.com',useCookie=True)
        if values['pageType'] == 'movie':
            import movies as moviesDB
            moviesDB.watchMoviedb(values['asin'])
        if values['pageType'] == 'tv':
            import tv as tvDB
            tvDB.watchEpisodedb(values['asin'])
        return
'''


def GetFlashVars(url):
    Login()
    cookies = HTTP.CookiesForURL(url)
    cookies = cookies + " x-main=\"MZsjMdQ1GEH@1rVszcqrPHY4Gh91Wl@v\";"
    showpage = HTTP.Request(url, headers={"Cookie": cookies}, follow_redirects=False).content
    flashVars = RE_FLASHVARS.findall(showpage)
    flashVars =(flashVars[0][0] + flashVars[0][1]).split("&")
    swfUrl = RE_SWFURL.findall(showpage)[0]
    values = {
        "token": "",
        "deviceTypeID": "A13Q6A55DBZB7M",
        "version": "1",
        "firmware": "1",
        "customerID": "",
        "format": "json",
        "deviceID": "",
        "asin": ""
    }

    if "<div class=\"avod-post-purchase\">" in showpage:
        owned=True
    else:
        owned=False

    for item in flashVars:
        item = item.split("=")
        if item[0] == "token":
            values[item[0]] = item[1]
        elif item[0] == "customer":
            values["customerID"] = item[1]
        elif item[0] == "ASIN":
            values["asin"] = item[1]
        elif item[0] == "pageType":
            values["pageType"] = item[1]        
        elif item[0] == "UBID":
            values["UBID"] = item[1]
        elif item[0] == "sessionID":
            values["sessionID"] = item[1]
        elif item[0] == "userAgent":
            values["userAgent"] = item[1]
        return swfUrl, values, owned, cookies


def GetStreams(url):
        return


'''
def PLAYVIDEO():
    if not os.path.isfile(common.COOKIEFILE):
        common.mechanizeLogin()
    #try:
    swfUrl, values, owned = GETFLASHVARS(common.args.url)
    #if not owned:
    #    return PLAYTRAILER_RESOLVE()
    values['deviceID'] = values['customerID'] + str(int(time.time() * 1000)) + values['asin']
    getstream  = 'https://atv-ps.amazon.com/cdp/catalog/GetStreamingUrlSets'
    #getstream  = 'https://atv-ext.amazon.com/cdp/cdp/catalog/GetStreamingUrlSets'
    getstream += '?asin='+values['asin']
    getstream += '&deviceTypeID='+values['deviceTypeID']
    getstream += '&firmware=WIN%2010,0,181,14%20PlugIn'
    getstream += '&customerID='+values['customerID']
    getstream += '&deviceID='+values['deviceID']
    getstream += '&token='+values['token']
    getstream += '&xws-fa-ov=false'
    getstream += '&format=json'
    getstream += '&version=1'
    try:
        rtmpurls, streamSessionID, cdn, title = GETSTREAMS(getstream)
    except:
        return PLAYTRAILER_RESOLVE()
    if cdn == 'limelight':
        xbmcgui.Dialog().ok('Limelight CDN','Limelight uses swfverfiy2. Playback may fail.')
    if rtmpurls <> False:
        basertmp, ip = PLAY(rtmpurls,swfUrl=swfUrl,title=title)
    if streamSessionID <> False:
        epoch = str(int(time.mktime(time.gmtime()))*1000)
        USurl =  'https://atv-ps.amazon.com/cdp/usage/UpdateStream'
        USurl += '?device_type_id='+values['deviceTypeID']
        USurl += '&deviceTypeID='+values['deviceTypeID']
        USurl += '&streaming_session_id='+streamSessionID
        USurl += '&operating_system='
        USurl += '&timecode=45.003'
        USurl += '&flash_version=WIN%2010,3,181,14%20PlugIn'
        USurl += '&asin='+values['asin']
        USurl += '&token='+values['token']
        USurl += '&browser='+urllib.quote_plus(values['userAgent'])
        USurl += '&server_id='+ip
        USurl += '&client_version='+swfUrl.split('/')[-1]
        USurl += '&unique_browser_id='+values['UBID']
        USurl += '&device_id='+values['deviceID']
        USurl += '&format=json'
        USurl += '&version=1'
        USurl += '&page_type='+values['pageType']
        USurl += '&start_state=Video'
        USurl += '&amazon_session_id='+values['sessionID']
        USurl += '&event=STOP'
        USurl += '&firmware=WIN%2010,3,181,14%20PlugIn'
        USurl += '&customerID='+values['customerID']
        USurl += '&deviceID='+values['deviceID']
        USurl += '&source_system=http://www.amazon.com'
        USurl += '&http_referer=ecx.images-amazon.com'
        USurl += '&event_timestamp='+epoch
        USurl += '&encrypted_customer_id='+values['customerID']
        print common.getURL(USurl,'atv-ps.amazon.com',useCookie=True)

        epoch = str(int(time.mktime(time.gmtime()))*1000)
        surl =  'https://atv-ps.amazon.com/cdp/usage/ReportStopStreamEvent'
        surl += '?deviceID='+values['deviceID']
        surl += '&source_system=http://www.amazon.com'
        surl += '&format=json'
        surl += '&event_timestamp='+epoch
        surl += '&encrypted_customer_id='+values['customerID']
        surl += '&http_referer=ecx.images-amazon.com'
        surl += '&device_type_id='+values['deviceTypeID']
        surl += '&download_bandwidth=9926.295518207282'
        surl += '&device_id='+values['deviceTypeID']
        surl += '&from_mode=purchased'
        surl += '&operating_system='
        surl += '&version=1'
        surl += '&flash_version=LNX%2010,3,181,14%20PlugIn'
        surl += '&url='+urllib.quote_plus(basertmp)
        surl += '&streaming_session_id='+streamSessionID
        surl += '&browser='+urllib.quote_plus(values['userAgent'])
        surl += '&server_id='+ip
        surl += '&client_version='+swfUrl.split('/')[-1]
        surl += '&unique_browser_id='+values['UBID']
        surl += '&amazon_session_id='+values['sessionID']
        surl += '&page_type='+values['pageType']
        surl += '&start_state=Video'
        surl += '&token='+values['token']
        surl += '&to_timecode=3883'
        surl += '&streaming_bit_rate=348'
        surl += '&new_streaming_bit_rate=2500'
        surl += '&asin='+values['asin']
        surl += '&deviceTypeID='+values['deviceTypeID']
        surl += '&firmware=WIN%2010,3,181,14%20PlugIn'
        surl += '&customerID='+values['customerID']
        print common.getURL(surl,'atv-ps.amazon.com',useCookie=True)
        if values['pageType'] == 'movie':
            import movies as moviesDB
            moviesDB.watchMoviedb(values['asin'])
        if values['pageType'] == 'tv':
            import tv as tvDB
            tvDB.watchEpisodedb(values['asin'])


def PLAY(rtmpurls,swfUrl,Trailer=False,resolve=True,title=False):
    print rtmpurls
    quality = [0,2500,1328,996,664,348]
    lbitrate = quality[int(common.addon.getSetting("bitrate"))]
    mbitrate = 0
    streams = []
    for data in rtmpurls:
        url = data['url']
        bitrate = int(data['bitrate'])
        if lbitrate == 0:
            streams.append([bitrate,url])
        elif bitrate >= mbitrate and bitrate <= lbitrate:
            mbitrate = bitrate
            rtmpurl = url
    if lbitrate == 0:
        quality=xbmcgui.Dialog().select('Please select a quality level:', [str(stream[0])+'kbps' for stream in streams])
        if quality!=-1:
            rtmpurl = streams[quality][1]
    protocolSplit = rtmpurl.split("://")
    pathSplit   = protocolSplit[1].split("/")
    hostname    = pathSplit[0]
    appName     = protocolSplit[1].split(hostname + "/")[1].split('/')[0]
    streamAuth  = rtmpurl.split(appName+'/')[1].split('?')
    stream      = streamAuth[0].replace('.mp4','')
    auth        = streamAuth[1]
    identurl = 'http://'+hostname+'/fcs/ident'
    ident = common.getURL(identurl)
    ip = re.compile('<fcs><ip>(.+?)</ip></fcs>').findall(ident)[0]
    basertmp = 'rtmpe://'+ip+':1935/'+appName+'?_fcs_vhost='+hostname+'&ovpfv=2.1.4&'+auth
    finalUrl = basertmp
    finalUrl += " playpath=" + stream
    finalUrl += " pageurl=" + common.args.url
    finalUrl += " swfurl=" + swfUrl + " swfvfy=true"
    if Trailer and not resolve:
        finalname = Trailer+' Trailer'
        item = xbmcgui.ListItem(finalname,path=finalUrl)
        item.setInfo( type="Video", infoLabels={ "Title": finalname})
        item.setProperty('IsPlayable', 'true')
        xbmc.Player().play(finalUrl,item)
    else:
        item = xbmcgui.ListItem(path=finalUrl)
        #item.setInfo( type="Video", infoLabels={ "Title": title})
        xbmcplugin.setResolvedUrl(pluginhandle, True, item)
    return basertmp, ip
'''
