from bottle import route, run, post, request, get, error, template
import sqlite3

#<html manifest="demo_html.appcache">
#http://www.w3schools.com/html/html5_app_cache.asp

#http://www.w3schools.com/html/html5_webstorage.asp

#Global var to keep track of current search results page and search key
#Set to page 1 for default
pagenum = 1
searchkey = ''
numrows = 0
numpages = 0

#Global var that sets the max number of results per page
maxres = 10

#Global var to keep track of access key, default to signed out
access_token = 'signed out'

@route('/setAccessToken')
def setAccessToken():
		#Updates current page number 
		global access_token
		access_token = request.query.accesstk
		return

#Home page, Need to log in to access search page
@get('/')
def LoginPage():
		return template('loginpage')+top_keywords()

@post('/results')	
def SearchPage():
		print 'access_token: '+access_token
		if access_token == 'signed out' or access_token == 'error' or access_token == 'undefined':
			return error403('cannot access, not logged in');

		keywords = [] 
		global searchkey
		#Retrieves the user input
		input = request.forms.get('keyword')

		if input:
			#Tokenize the user input into separate keywords
			#Empty split will get rid of any whitespace
			keywords = input.split()

			#Get rid of capitals
			keywords = [element.lower() for element in keywords]

			#Only interested in searching for first keyword
			#In case no keyword is entered, use implicit booleanness of the empty list
			searchkey = keywords[0]
			
		#Send searchkey to get list of URLs
		searchpage = resultsTable()
		return searchpage

@route('/getrows')
@get('/results')
def keywords_db():
		print 'in keywords_db()'
		global numrows
		global numpages
		print 'access_token: '+access_token
		if access_token == 'signed out' or access_token == 'error' or access_token == 'undefined':
			return error403('cannot access, not logged in');

		#Connect to Database
		conn = sqlite3.connect('topKW.db')
		c = conn.cursor()
		
		#c.execute('''DROP TABLE IF EXISTS Keywords''') #For clean up purposes
		
		#Create table to store keywords and totalcount and current count for the submitted query (if the table does not exist previously)
		c.execute('''CREATE TABLE IF NOT EXISTS Keywords (keyword text NOT NULL PRIMARY KEY, totalcount int NOT NULL) ''')
		c.execute('''CREATE TABLE IF NOT EXISTS Data (keyword text NOT NULL , url text) ''')
		#Insert new keyword or update count of existing keyword into Keywords Table
		#Connect to BE Database
		bconn = sqlite3.connect("dbFile.db")
		b = bconn.cursor()
		try:	
			#new keywords, so insert and get urls from backend
			c.execute('''INSERT INTO Keywords VALUES(?, 1) ''', [searchkey])
			
			#Find all URLs that contain the searchkey and order by page rank
			b.execute('''SELECT docIndex.url
						FROM lex
						JOIN invIndex
							ON lex.wordID = invIndex.wordID
						JOIN docIndex
							ON invIndex.docID = docIndex.docID
						JOIN pageRank
							ON docIndex.docID = pageRank.docID
						WHERE lex.word = ? 
						ORDER BY rank DESC, url ASC''', [searchkey])
			rows = b.fetchall()

			for row in rows: 
				c.execute('''INSERT INTO Data VALUES (?,?)''', [searchkey, row[0]])

		except sqlite3.IntegrityError, m:	#existing keywords
			c.execute('''UPDATE Keywords SET totalcount = totalcount + 1 WHERE keyword = ?''', [searchkey])
			c.execute('''SELECT url
						FROM Data
						WHERE keyword = ? ''', [searchkey])
			rows = c.fetchall()
			
		#Commit the changes to FE database 
		conn.commit()
		bconn.commit()
		
		#Close the connection to the BE database
		bconn.close()
			
		#Close the connection to the FE database
		conn.close()

		#Calculate total number of pages needed to display 10 results per page
		numrows = len(rows)
		numpages = numrows/maxres
		if (numrows%maxres): 
			numpages += 1

		return str(rows)
			
def top_keywords():
		#Create an empty string
		s = ''
		#Connect to Database
		conn = sqlite3.connect('topKW.db')
		c = conn.cursor()
		
		#c.execute('''DROP TABLE IF EXISTS Keywords''') #For clean up purposes
		
		#Create table to store keywords and totalcount and current count for the submitted query (if the table does not exist previously)
		c.execute('''CREATE TABLE IF NOT EXISTS Keywords (keyword text NOT NULL PRIMARY KEY, totalcount int NOT NULL) ''')

		#Print out top 20 searched keywords, if exists
		c.execute('''SELECT keyword, totalcount FROM Keywords ORDER BY totalcount DESC''')
		rows = c.fetchall()
		if rows:
			s = '''
						 <center>	
						 <BR>
						 <table border="1"> 
						 <tr> 
								<th align=center>  Word  </th> 
								<th align=center>  Count  </th> 
						 </tr>'''
		i = 0 #Counter, only want top 20
		for row in rows:
			if i > 19:
				break;
			s += '''<tr><td align=center> %s </td><td align=center> %d </td></tr>''' % (row[0], row[1])
			i+=1
			
		#Close the connection to the FE database
		conn.close()
		
		return s

@route('/setPageNum')
def setPage():
		#Updates current page number 
		global pagenum
		pagenum = request.query.pagenm
		getData()

@route('/getSearchkey')
def getSearchkey():
		print 'in get searchkey func = ' + searchkey
		return searchkey

@route('/getAccessToken')
def getAccessToken():
		print 'in get token function, token = ' + access_token
		return access_token

def resultsTable():
		values = {'numpages': numpages, 'cpagenum': pagenum, 'maxres': maxres, 'searchkey':searchkey}  
		return template('resultstablen', **values)
		
#404 File not Found / Page does not Exist
@error(404)
def error404(error):
	return template('error404')

@error(403)
def error403(error):
	return template('error403')
		
					
		
#Runs the server on localhost
#Allows access to webpage through http://localhost:8080/
run(host='localhost', port=8080, debug=True)

#run(host='0.0.0.0', port=80)


#set path=%path%;C:\python27