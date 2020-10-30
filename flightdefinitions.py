#------------------------------------------------------------------IMPORTS-----------------------------------------------------------

import datetime
import csv
import math
import threading
import os
import shutil
import urllib
from bs4 import BeautifulSoup
import requests
from pyfiglet import figlet_format
from metar import Metar

#------------------------------------------------------------------DEFINITIONS-----------------------------------------------------------

def metar(metar):
    obs = Metar.Metar(str(metar))
    return str(obs)

def taf(loc):
    if loc == "": 
        return ""
    try: 
        url = 'http://www.aviationweather.gov/adds/metars/?station_ids=%s&std_trans=standard&chk_metars=on&hoursStr=most+recent+only&submitmet=Submit' % (loc)
        SHORT_TIMEOUT = 1.3
        page = urllib.request.urlopen(url, timeout=SHORT_TIMEOUT).read()
        soup = BeautifulSoup(page, features="html5lib")
        found = soup.find_all('font')
        found = found[1]
        wx = str(found).split('>')[1].split('<')[0]
        return wx
    except Exception as e: 
        print('TAF fail: {}'.format(e))
        return ''


def getmetar(loc):
    if loc == "": 
        return ""
    try: 
        url = 'http://www.aviationweather.gov/adds/metars/?station_ids=%s&std_trans=standard&chk_metars=on&hoursStr=most+recent+only&submitmet=Submit' % (loc)
        SHORT_TIMEOUT = 1.3
        page = urllib.request.urlopen(url, timeout=SHORT_TIMEOUT).read()
        soup = BeautifulSoup(page, features="html5lib")
        found = soup.find_all('font')
        found = found[0]
        wx = str(found).split('>')[1].split('<')[0]
        return wx
    except Exception as e: 
        print('Weather fail: {}'.format(e))
        return ''

def wind(loc, metar=""):
    if not metar=="": 
        for item in metar.split():
            if "KT" in item: 
                winddir = item[0:3]
                windstrength = item[3:5]
                return (winddir, windstrength)
    weather = getWeather(loc)
    if weather == "": 
        return (0, 0)
    wind = ()
    for item in weather.split():
        if "CALM" in item: 
            return (0, 0)
        if "KT" in item: 
            winddir = item[0:3]
            windstrength = item[3:5]
            if ("VRB" in winddir):
                return (0, 0)
            wind = (winddir, windstrength)
    return wind

def aptnamelatlon(icao):
    readrows=[]
    with open('airports.csv', newline='', encoding='utf-8') as apts:
        for i in csv.reader(apts):
            if str(i[1]).upper()==str(icao).upper():
                alist=[i[3],i[4],i[5]]
                return alist
            else:
                continue
        return [0,0,0]

def getdist(dpt,arr):
    R = 6373.0
    lat1 = math.radians(float(aptnamelatlon(dpt)[1]))
    lon1 = math.radians(float(aptnamelatlon(dpt)[2]))
    lat2 = math.radians(float(aptnamelatlon(arr)[1]))
    lon2 = math.radians(float(aptnamelatlon(arr)[2]))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

def getFlightPath(frm, to, alt='FL330', usesid='Y', usestar='Y', rnav='Y',flight="B738"):
    airac = '2009'
    data = {
        'id1': str((frm).upper()),
        'ic1': '',
        'id2': str((to).upper()),
        'ic2': '',
        'minalt': str(alt),
        'maxalt': str(alt),
        'lvl': 'B',
        'dbid': str(airac),
        'usesid': str(usesid),
        'usestar': str(usestar),
        'easet': 'Y',
        'rnav': str(rnav),
        'nats': 'R',
        'k': '1136863659'
    }
    

    with requests.Session() as s:
        url = 'http://rfinder.asalink.net/free/autoroute_rtx.php'
        r = s.post(url, data=data) #headers=headers)
        soup = BeautifulSoup(r.content, 'html5lib')
        x = soup.find_all('tt')[1]
        x = str(x)
        x = x.replace('<tt>','')
        x = x.replace('</tt>','')
        # x = x.replace('<b>','')
        # x = x.replace('</b>','')
        x = x.replace('\\n','<br>')
        path = x
        x = soup.find_all('tt')[0]
        x = str(x)
        x = x.replace('<tt>','')
        x = x.replace('</tt>','')
        # x = x.replace('<b>','')
        # x = x.replace('</b>','')
        # x = x.replace('<br/>','\n')
        x = x.replace('-&gt;',' -> ')
        x = x.replace('\\n','<br>')
        details = x
        x = soup.find_all('pre')[0]
        x = str(x)
        x = x.replace('<pre>','')
        x = x.replace('</pre>','')
        x = x.replace('\n','<br>')
        routebriefing = x

    data = {
        'EQPT': str(flight),
        'ORIG': str((frm).upper()),
        'DEST': str((to).upper()),
        'submit':'LOADSHEET',
        'okstart':'1'
    }
    

    with requests.Session() as s:
        url = 'http://fuelplanner.com/index.php'
        r = s.post(url, data=data) #headers=headers)
        soup = BeautifulSoup(r.content, 'html5lib')
        x = soup.find_all('pre')[0]
        x = str(x)
        x = x.replace('Copyright 2008-2019 by Garen Evans','')
        x = x.replace('fuelplanner.com | <a href="index.php">home</a>','')
        x = x.replace('<pre>','')
        x = x.replace('</pre>','')
        x = x.replace('\n','<br>')
        loadsheet = x
        return [path,details,routebriefing,str(loadsheet)]

def asciify(text):
     handle=''
     for i in str(text):
        handle+=i
        handle+='      '
     print(figlet_format(handle))
     return str(figlet_format(handle)).replace('\n','<br>')

def getnotams(apt):
    with requests.Session() as s:
        url = 'https://www.notams.faa.gov/dinsQueryWeb/queryRetrievalMapAction.do?reportType=Report&retrieveLocId='+str(apt)+'&actionType=notamRetrievalByICAOs&submit=View+NOTAMs'
        r = s.get(url)
        soup = BeautifulSoup(r.content, 'html5lib')
        notams = soup.find_all("pre")
        notamsasstring=''
        for i in notams:
        	notamsasstring+=str(i)
        return notamsasstring