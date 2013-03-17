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

common = SharedCodeService.common
c = SharedCodeService.constants


def authenticate():
    common.authenticate()
    return logged_in()


def logged_in():
    try:
        cookies = HTTP.CookiesForURL(c.AMAZON_URL).split(";")
    except AttributeError:
        return False

    for cookie in cookies:
        if "x-main" in cookie:
            return True

    return False


def is_prime():
    # NOTE(jk0): We don't really need to authenticate again here, but are just
    # using this as a helper to get a copy of the current prime pattern match
    # to avoid a race condition.
    page = common.authenticate()
    return len(page.xpath(c.IS_ACCOUNT_PRIME_PATTERN)) > 0
