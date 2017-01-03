#! /usr/bin/python
import codecs
import commands
import json
import requests
import urllib2
import yaml
from datetime import datetime, timedelta
from lxml import etree

with open('config.json', 'r') as f:
    config = json.load(f)

def get_exist_article():
    # get data from discourse
    url = config["discourse-url"] + config["discourse-target-path"]
    r = requests.get(url)
    #print r.status_code, r.headers['content-type'], r.encoding, r.text 
    topics = r.json()['topic_list']['topics']
    ret = []
    for i in range(len(topics)):
        ret.append({'id':topics[i]['id'], 'title':topics[i]['title'], 'datetime':topics[i]['created_at']})
    return ret

def get_sayit_title():   
    hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
           'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
           'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
           'Accept-Encoding': 'none',
           'Accept-Language': 'en-US,en;q=0.8',
           'Connection': 'keep-alive'}
    request = urllib2.Request(config["sayit-url"]+config["sayit-target-path"], headers=hdr)
    response = urllib2.urlopen(request)
    page = etree.HTML(response.read())
    ret = []
    for txt in page.xpath(u"//li/span/a"):
        if txt.text[:6] == '2016-1': #if txt.text[:5] == '2016-' or txt.text[:5] == '2015-':
            ret.append({'date':txt.text[:10], 'title':txt.text[11:], 'url': config["sayit-url"] + txt.values()[0]})
    return ret

def check_title(sayit, discourse):
    ret = []
    for i in range(len(sayit)):
        discourse_id = 0
        for j in range(len(discourse)):
            if sayit[i]['title'][:10].upper() == discourse[j]['title'][:10].upper():
                discourse_id = discourse[j]['id']
        #print discourse_id , sayit[i]['date'], sayit[i]['title']           
        ret.append({'date':sayit[i]['date'], 'title':sayit[i]['title'], 'url':sayit[i]['url'], 'id':discourse_id}) 
    return ret           

def update_raw(list_data):
    for i in range(len(list_data)):
        if list_data[i]['id'] == 0:
            discourse_create(list_data[i])
        elif list_data[i]['id'] != 0:  
            r = requests.get(config["discourse-url"] + '/t/topic/'+ str(list_data[i]['id']) +'.json')
            real_id = str(r.json()['post_stream']['posts'][0]['id'])
            list_data[i]['id'] = real_id
            r = requests.get(config["discourse-url"] + '/posts/' + real_id + '.json')
            yaml_raw = yaml.load(r.json()['raw'])
            if 'content' in yaml_raw.keys():
                yaml_content = yaml_raw['content']
                has_transcript = 0
                for j in range(len(yaml_content)):
                    if 'Transcript' in yaml_content[j].keys():
                        if yaml_content[j]['Transcript'] is None:
                            yaml_raw['content'][j]['Transcript'] = list_data[i]['url']
                            list_data[i]['raw'] = yaml_raw
                            discourse_update(list_data[i])
                        has_transcript = 1
                if has_transcript == 0:
                    # with Youtube, Soundcloud, Slido, Wiselike, Discourse
                    yaml_raw['content'].append({"Transcript":list_data[i]['url']})
                    list_data[i]['raw'] = yaml_raw
                    discourse_update(list_data[i]) 
            else:
                # Add new content
                yaml_raw["content"] = [{"Transcript":list_data[i]['url']}]
                list_data[i]['raw'] = yaml_raw
                discourse_update(list_data[i])

def discourse_update(data):
    #print 'discourse_update' , data['id'], data['title'], data['raw']
    post_details = {'post[raw]': yaml.safe_dump(data['raw'], encoding='utf-8', allow_unicode=True, default_flow_style=False),}
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    url = config["discourse-url"] + '/posts/'+data['id']+'?api_key='+config["discourse-api-key"]+'&api_username='+config["discourse-api-username"]
    resp = requests.put(url, data=post_details, headers=headers)
    log('discourse_update: ' + str(resp.status_code)+', '+str(data['id']))#+', '+str(data['title']))
    return 0

def discourse_create(data):
    deadline = datetime.now().date() - timedelta(days=config["sayit-days-ago"])
    posttime = datetime.strptime(data['date'],"%Y-%m-%d").date()
    if posttime < deadline :
        #print 'out of deadline'
        return 0
    #print 'discourse_create', data['id'], data['title'], data['date']# data['url'],
    raw = {}
    raw['content'] = [ {"Transcript":data['url']} ]
    post_details = {
        "title":  data['title'],
        "raw": yaml.safe_dump(raw, encoding='utf-8', allow_unicode=True, default_flow_style=False),
        "category": config["discourse-category-id"]
        "created_at": str(data['date'])+"T00:00:00.000Z +08:00"
        }    
    headers = {'content-type': 'application/x-www-form-urlencoded'}
    url = config["discourse-url"] + '/posts?api_key='+config["discourse-api-key"]+'&api_username='+config["discourse-api-username"]
    resp = requests.post(url, data=post_details, allow_redirects=True, verify=False, headers=headers)
    log('discourse_create: ' + str(resp.status_code)+', '+str(data['date']))#+', '+str(data['title']))
    return 0

def log(msg):
    logfile = codecs.open("discupdater.log", "a", "utf-8")
    logfile.write(str(datetime.now()) + ' ' + msg + '\n')
    logfile.close()

if __name__ == '__main__':
    log('===== ACTION =====')
    list_sayit = get_sayit_title()
    list_discourse = get_exist_article()
    list_for_update = check_title(list_sayit, list_discourse)
    update_raw(list_for_update)
