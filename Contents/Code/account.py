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


def authenticate(amazon_url):
    params = {
        "action": "sign-in",
        "protocol": "https",
        "sessionId": get_session_id(amazon_url),
        "email": Prefs["username"],
        "password": Prefs["password"]
    }

    HTTP.Request(amazon_url + "/gp/flex/sign-in/select.html", values=params)

    Dict["amazoninstantvideo_logged_in"] = False
    for cookie in HTTP.CookiesForURL(amazon_url).split(";"):
        if "x-main" in cookie:
            Dict["amazoninstantvideo_logged_in"] = True

    Dict.Save()

    return logged_in()


def logged_in():
    return Dict["amazoninstantvideo_logged_in"]


def get_session_id(amazon_url):
    cookie_url = amazon_url + "/gp/sign-in.html"
    HTTP.Request(cookie_url).content

    for cookie in HTTP.CookiesForURL(cookie_url).split(";"):
        cookie = cookie.split("=", 1)

        if cookie[0].strip() == "session-id":
            return cookie[1].strip()
