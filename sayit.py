# encoding: utf-8
import requests
import urllib2
import time
from lxml import etree

from HTMLParser import HTMLParser
class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    try:
        s = MLStripper()
        s.feed(html)
        return s.get_data()
    except:
        return html

hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}

request = urllib2.Request("http://sayit.archive.tw/speeches", headers=hdr)
response = urllib2.urlopen(request)
html = response.read()

#print html
page = etree.HTML(html)

ret = []
for txt in page.xpath(u"//li/span/a"):
    txt_title = txt.text
    txt_url = 'http://sayit.archive.tw' + txt.values()[0]
    if txt.text[:5] == "2016-" or txt.text[:5] == "2015-":
        #ret = '{"url":"' + 'http://sayit.archive.tw' + txt.values()[0] + '", "title":"' + txt.text + '", "date":"' + txt.text[:10] +'"}'
        txt_date = txt.text[:10]
        raw = "title: "+txt_title+" \ndate: "+txt_date+"\ntags:\nparticipants:\n\n - Audery Tang\n\ncontent:\n\n - Youtube:\n - transcript: "+txt_url+"\n - soundcloud:\n - slido:\n - wiselike:\n", 
        # post to pdis discourse
        url = "https://talk.pdis.nat.gov.tw/posts?api_key=&api_username="
        post_details = {
            "title":  txt_title,
            "raw": raw,
            "category": "pdis-site"
            }
        resp = requests.post(url, data=post_details, allow_redirects=True, verify=False)
        print resp
        time.sleep(30)
    else: 
        print '{"url":"' + 'http://sayit.archive.tw' + txt.values()[0] + '", "title":"' + txt.text + '"}'
        #txt_date = None
        #raw = "title: "+txt_title+" \ndate: \ntags:\nparticipants:\n\n - Audery Tang\n\ncontent:\n\n - Youtube:\n - transcript: "+txt_url+"\n - soundcloud:\n - slido:\n - wiselike:\n"
    
