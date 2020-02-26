from bs4 import BeautifulSoup
import requests
import re
from datetime import datetime
import sys
from urllib.parse import unquote

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def parseFile(filename):
    with open(filename) as fp:
        return BeautifulSoup(fp, features="html5lib")

def parseURL(url):
    s = requests.get(url, {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:72.0) Gecko/20100101 Firefox/72.0'})
    return BeautifulSoup(s.text, features="html5lib")

def formatDate(date):
    return date.strftime("%a, %d %b %Y %H:%M:%S")


def removeTags(tag):
    def aux(tag):
        def auxlist(l):
            return "".join(aux(x) for x in l)
        if tag.name in ["img"]:
            return ""
        elif tag.name in ["div", "span"]:
            return auxlist(tag.children)
        elif tag.name in ["p"]:
            return "<p>" + auxlist(tag.children) + "</p>"
        elif tag.name in ["a"]:
            cancer = "https://l.facebook.com/l.php?u="
            url = tag["href"]
            if url[:len(cancer)] == cancer:
                url = url[len(cancer):]
                hpos = url.find("&h=")
                assert(hpos != -1)
                url = url[:hpos]
                url = unquote(url)
            if url[0] == "/":
                url = "https://facebook.com" + url
                qpos = url.find("?")
                if qpos != -1:
                    url = url[:qpos]
            return "<a href=\"" + url + "\">" + auxlist(tag.children) + "</a>"
        else:
            return str(tag) + "\n"
    res = aux(tag)
    res = res.replace('&', '&amp;')
    res = res.replace('<', '&lt;')
    res = res.replace('>', '&gt;')
    res = res.replace('"', '&quot;')
    res = res.replace("'", '&#39;')
    res = res.replace("<", "&lt;")
    return res

def getPost(url):
    def is_post_post(tag):
        return (tag.has_attr("data-testid") and tag["data-testid"] == "post_message")
    def is_post_date(tag):
        return tag.has_attr("data-utime")
    soup = parseURL(url)
    post_tags = soup.findAll(is_post_post)
    if len(post_tags) == 0:
        eprint("Can't get post for " + url)
        return
    post_tag = post_tags[0]
    date_tags = post_tag.previous_sibling.findAll(is_post_date)
    assert(len(date_tags) >= 1)
    date_tag = date_tags[0]
    unix_epoch = date_tag["data-utime"]
    date = unix_epoch
    print("""
    <item>
        <description>""")
    print(removeTags(post_tag))
    print("""
        </description>
        <pubDate>""" + formatDate(datetime.fromtimestamp(int(date))) + """</pubDate>
        <guid>""" + url + """</guid>
    </item>""")


def getPosts(url, soup):
    def is_feed_id(tag):
        return (tag.name == "input") and \
               (tag.has_attr("name") and tag["name"] == "ft_ent_identifier") and \
               (tag.has_attr("value"))
    for t in soup.findAll(is_feed_id):
        post_url = url + t["value"] + "?_fb_noscript=1"
        getPost(post_url)
        print()

def getTitle(tag):
    titleTag = tag.find_all("title")[0]
    title = titleTag.string
    revTitle = "".join(reversed(title))
    revTitle = revTitle[revTitle.find(" - ")+3:]
    return "".join(reversed(revTitle))

def makeRssFeed(pagename):
    url = "https://www.facebook.com/" + pagename + "/posts/"
    soup = parseURL(url)
    print("""<?xml version="1.0"?>
    <rss version="2.0">
        <channel>
            <title>""" + getTitle(soup) + """</title>
            <link>""" + url + """</link>
            <description>""" + getTitle(soup) + """</description>
            <lastBuildDate>""" + formatDate(datetime.today()) + """</lastBuildDate>""")
    getPosts(url, soup)
    print("""
        </channel>
    </rss>""")

if len(sys.argv) > 1:
    makeRssFeed(sys.argv[1])
else:
    print("Usage: " + sys.argv[0] + " [facebook page name]")
