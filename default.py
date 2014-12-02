import urllib, urllib2, re, sys, cookielib
import xbmc, xbmcgui, xbmcplugin, xbmcaddon
import time, os, fnmatch, string
from glob import glob
import CommonFunctions
common = CommonFunctions
#from BeautifulSoup import BeautifulSoup, SoupStrainer

handle = int(sys.argv[1])

recursion = 0

USERAGENT = "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8"

urls = {}
urls['categories'] = "http://kolibka.com/menu.html"
urls['category'] = "http://kolibka.com/movies.php?cat=%s&page=%s&orderby=movie"

def buildItemUrl(item_params = {}, url = ""):
	blacklist = ("Title", "thumbnail", "icon")
	for key, value in item_params.items():
		if key not in blacklist:
			url += key + "=" + urllib.quote_plus(value) + "&"
	return url

def getParameters(parameterString):
	commands = {}
	splitCommands = parameterString[parameterString.find('?')+1:].split('&')

	for command in splitCommands:
		if (len(command) > 0):
			splitCommand = command.split('=')
			name = splitCommand[0]
			value = splitCommand[1]
			commands[name] = value

	return commands

def addFolderListItem(item_params = {}, size = 0):
	item = item_params.get
	
	icon = "DefaultFolder.png"
	if (item("thumbnail", "DefaultFolder.png").find("http://") == -1):
		thumbnail = "DefaultFolder.png"
	else:
		thumbnail = item("thumbnail")

	listitem = xbmcgui.ListItem(item("Title"), iconImage=icon, thumbnailImage=thumbnail)
	listitem.setInfo(type = 'video', infoLabels = {'Title': item("Title")})
	url = buildItemUrl(item_params, '%s?' % sys.argv[0])
	
	folder = True

	xbmcplugin.addDirectoryItem(handle, url=url, listitem=listitem, isFolder=folder, totalItems=size)

def addActionListItem(item_params = {}, size = 0):
	item = item_params.get
	folder = False 

	icon = "DefaultFolder.png"
	if (item("thumbnail", "DefaultFolder.png").find("http://") == -1):
		thumbnail = "DefaultFolder.png"
	else:
		thumbnail = item("thumbnail")

	listitem = xbmcgui.ListItem(item("Title"), iconImage=icon, thumbnailImage=thumbnail)
	listitem.setInfo(type = 'video', infoLabels = {'Title': item("Title")})
	listitem.setProperty('IsPlayable', 'true');
	url = buildItemUrl(item_params, '%s?' % sys.argv[0])

	xbmcplugin.addDirectoryItem(handle, url=url, listitem=listitem, isFolder=folder, totalItems=size)

def showMessage(heading, message):
	xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % (heading, message, 3000))

def getURL(url):
	#print "getURL open: " + url

	req = urllib2.Request(url)
        req.add_header('User-Agent', USERAGENT)
	
        response = urllib2.urlopen(req)
        link=response.read()
        response.close()	

	#print link
	return link

def scrapeVideos(url):
	result = getURL(url)
	objects = []

	videos = re.compile('href="download.php\?mid=([^"]*?)".*?>(.*?)</a>', re.DOTALL).findall(result);
		
	for vid, name in videos:
		item = {}
		item['id'] = vid
		item['title'] = name
		objects.append(item)

	return objects

#Added to check for next page with videos.
def addNextFolder(url):
	result = getURL(url)
	udata = result.decode("utf-8")
	asciidata = udata.encode("ascii","ignore")
	pagination = common.parseDOM(asciidata, "div", attrs = { "class": "paginationNew"})
	if (len(pagination) > 0):
		tmp = str(pagination)
		if (tmp.find("nextPage") > 0):
			return True

def MainMenu():
	addFolderListItem({'Title': 'Categories', 'act': 'categories'})


def ListVideos(url):
	objects = scrapeVideos(url)
	for video in objects:
		addActionListItem({'Title': video['title'], 'thumbnail': 'DefaultFolder.png', 'act': 'play', 'vid': video['id'], 'name': video['title']})

def Categories():
	objects = [] 
	cid_list = []
	thumb_list = []
	bg_dict = {"space":"Vselena", 
		"technology":"Tehnologii",
		"energy":"Energiya",
		"conflicts":"Konflikti",
		"nature":"Priroda",
		"sea":"Morski svyat",
		"paleontology":"Paleontologiya",
		"animals":"Jivotni",
		"ecology":"Ekologiya",
		"catastrophes":"Katastrofi",
		"world":"Po sveta",
		"civilizations":"Civilizacii",
		"human":"Chovek",
		"society":"Obshtestvo",
		"biography":"Lichnosti",
		"art":"Izkustvo",
		"spiritual":"Duhovni ucheniya",
		"mysteries":"Zagadki",
		"bg":"BG Tvorchestvo" }


	result = getURL(urls[params['act']])
	categories =re.compile('onMouseOver=".*?ex.src=\'(.*?)\'".*?href="\/movies.php\?cat=(.*?)"', re.DOTALL).findall(result);
	for thumb, cid in categories:
		cid_list.append(cid)
		thumb_list.append(thumb)

	thumbnail_root = 'http://kolibka.com/' 

	for cid, thumbnail  in zip(cid_list, thumb_list):
		addFolderListItem( { 'Title': bg_dict[cid], 'act': 'category', 'category_id': cid, 'thumbnail': thumbnail_root + thumbnail } )
	
def Subscriptions():
	result = getPage(urls[params['act']] + username)
	subscriptions = re.compile('class="clipThumb".*?href="/collection:(.*?)".*?src="(.*?)".*?href=".*?">(.*?)</a>', re.DOTALL).findall(result);
	for sid, thumbnail, name in subscriptions:
		addFolderListItem({'Title': name, 'act': 'subscription', 'subscription_id': sid, 'thumbnail': thumbnail})

def recursive_glob(treeroot, pattern):
        results = []
        for base, dirs, files in os.walk(treeroot):
                for extension in pattern:
                        for filename in fnmatch.filter(files, '*.' + extension):
                                results.append(os.path.join(base, filename))
        return results

def getSubtitles(sidUrl):
        subRarPath = '/tmp/subtitle.rar'
	subext = ['srt', 'sub']

        if os.path.exists(subRarPath):  #remove old /tmp/subtitle.rar file
                os.remove(subRarPath)   #

        for allsrt in glob ('/tmp/*.srt'):   #remove old /tmp/*.srt files
                os.remove(allsrt)            #

        opener = urllib2.build_opener(urllib2.HTTPRedirectHandler)      #
        request = opener.open(sidUrl)                                   #
        sid = request.url

        urllib.urlretrieve(sid, subRarPath)     #download subtitle RAR file

	xbmc.executebuiltin("XBMC.Extract(/tmp/subtitle.rar,/tmp/)")
	time.sleep(5)	#waiting 5sec. to complete rar extract
	for filesub in recursive_glob('/tmp/', subext):
		subName = filesub

        return subName

def PlayVid(vid, name = ""):
	opener = urllib2.build_opener(urllib2.HTTPRedirectHandler)
	request = opener.open('http://kolibka.com/download.php?mid=' + vid)
	videoPath = request.url
	#print "videoPath: " + videoPath
	if (videoPath != 'http://kolibka.com/'):
		item = xbmcgui.ListItem(label = name, thumbnailImage = 'http://kolibka.com/images/nav159453900i.gif' , path= videoPath)
		item.setInfo(type = 'video', infoLabels = {'Title': name})
		xbmcplugin.setResolvedUrl(handle=int(sys.argv[1]), succeeded=True, listitem=item)
		sub = getSubtitles("http://kolibka.com/download.php?sid=" + vid)
		time.sleep(5)	#waiting 5sec. to attaching subtitle file
		xbmc.Player().setSubtitles(sub)
		return True
	else:
		showMessage('Error', 'Video not found')
		return False

params = getParameters(sys.argv[2])
get = params.get

cache = True

if get('act') == None:
	MainMenu()
elif get('act') == 'categories':
	Categories()
elif get('act') == 'category':
	ListVideos(urls['category'] % (get('category_id'), get('page', 1)))
elif get('act') == 'play':
	if get('vid') == None:
		params['vid'] = getUserInput()
	PlayVid(urllib.unquote_plus(get('vid')), urllib.unquote_plus(get('name')))

xbmcplugin.endOfDirectory(handle, succeeded=True, cacheToDisc=cache)
