from bottle import route, run, post, request, get, error
import sqlite3

@get('/')
def QueryPage():
		#Use HTML & CSS to make the query page
		querypage = '''<!DOCTYPE HTML>
						<html> 
						<head> 
							<title>CSC326 Search Engine</title> 
							<style>
								body {text-align:center; margin: auto; position: fixed; 
  										top: 0; left: 0; bottom: 0; right: 0; vertical-align:middle; color:white;
										background: #000 url('http://www.hdwallpaperstop.com/wp-content/uploads/2013/09/Space-Background-Widescreen-Wallpaper.jpg') 0 0 no-repeat; background-size: 100%; background-repeat:repeat-y;}
}
							</style>
						<meta http-equiv="content-type" content="text/html; charset=iso-8859-1" />
						</head>	
						<body> 
							<h1>Space Explorer <img src="http://goo.gl/2z51Zw" width="50" height="50"></h1>
							<form action="/search" method="POST"> 
								<b>Search: </b><input type="text" name="keyword"> 
								<input type="submit" value="Submit"> 
							</form>	
						</body> 
						</html> 
					'''
		#Pass in an empty list, since there is no user input yet		
		#keywords = list()
		#querypage +=keywords_db(keywords, 1)
		return querypage
		
		
@post('/search')	
def SearchPage():	
		keywords = [] 
		searchkey = ''
		#Retrieves the user input
		input = request.forms.get('keyword')
		
		#Tokenize the user input into separate keywords
		#Empty split will get rid of any whitespace
		keywords = input.split()

		#Get rid of capitals
		keywords = [element.lower() for element in keywords]

		#Only interested in searching for first keyword
		#In case no keyword is entered, use implicit booleanness of the empty list
		if keywords:
			searchkey = keywords[0]
			print searchkey
		#Send searchkey to BE and grab the URLS & bonus - title+descr & page rank
		#Use BE bonus functions
		#crawler.get_url_title()
		#crawler.get_url_description()
		#return URLS sorted by page rank

		#Send keywords to Database
		#searchpage = keywords_db(keywords, 2)
		#searchpage = 
		searchpage = urls_db(searchkey)
		return searchpage

#@route('/search')
def scrollpage():
	return '''<html>
			  <head>
			  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />

			  <script type="text/javascript">
			  
			'''

def urls_db(searchkey):
		#Connect to Database
		conn = sqlite3.connect("dbFile.db")
		c = conn.cursor()
		#Create an empty string
		s = ''
		
		#Output total number of keywords entered if a phrase is entered		
		s = '''<!DOCTYPE HTML>
						 <html> 
						 <head> 
						 		<title>CSC326 Search Engine</title> 
								<style>
									body {text-align:center; margin: auto; position: fixed; color:white;
											top: 0; left: 0; bottom: 0; right: 0; vertical-align:middle;
											background: #000 url('http://static.tumblr.com/1d6145f98f1d856ffa3115853ee85ff0/lh9td6e/p2smmlu6n/tumblr_static_space-background.jpg') 0 0 no-repeat; background-size: 100%; background-repeat:repeat-y;}
}
								</style>
						 </head>
						 <center>
							<h1>Space Explorer <img src="http://goo.gl/2z51Zw" width="50" height="50"></h1>
							<form action="/search" method="POST"> 
								<b>Search Again: </b><input type="text" name="keyword"> 
								<input type="submit" value="Submit"> 
							</form>'''
			
		#Output Query Results Table	
		#Output header of table
		s += '''<BR><BR>
						<table border="1"> 
						<tr> 
						 	<th align=center>  Page Rank  </th> 
							<th align=center>  Title  </th> 
							<th align=center>  URL  </th> 
							<th align=center>  Description  </th> 
						</tr>
				 '''
		#Output each URL and its title and description in separate rows
		c.execute('''SELECT pageRank.rank, docTitle.title, docIndex.url, docParDescript.descript, lex.wordID, invIndex.docID
								 FROM lex
								 JOIN invIndex
							   		ON lex.wordID = invIndex.wordID
								 JOIN docIndex
							   		ON invIndex.docID = docIndex.docID
								 JOIN docTitle
							   		ON docIndex.docID = docTitle.docID
								 JOIN docParDescript
							   		ON docTitle.docID = docParDescript.docID
								 JOIN pageRank
							   		ON docIndex.docID = pageRank.docID
								 WHERE lex.word = ? 
								 ORDER BY rank DESC, url ASC''', [searchkey])
		rows = c.fetchall()
		for row in rows:
			s += '''<tr><td align=center> %f </td><td align=center> %s </td><td align=center> %s </td><td align=center> %s </td></tr>''' % (row[0], row[1], row[2], row[3])
			#print row[4], row[5], row[0], row[1], row[2]	#Debugging

		#Close the connection to the database
		conn.close()

		return s

def keywords_db(keywords, page):
		#Create an empty string
		s = ''
		#Connect to Database
		conn = sqlite3.connect('example.db')
		c = conn.cursor()
		
		c.execute('''DROP TABLE IF EXISTS Keywords''') #For clean up purposes
		
		#Create table to store keywords and totalcount and current count for the submitted query (if the table does not exist previously)
		c.execute('''CREATE TABLE IF NOT EXISTS Keywords (word text NOT NULL PRIMARY KEY, totalcount int NOT NULL, count int NOT NULL) ''')
		
		#Page = 1, print out top 20 on the Query Page
		if page == 1:

			#Print out top 20 searched keywords, if exists
			c.execute('''SELECT word, totalcount FROM Keywords ORDER BY totalcount DESC''')
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
		
		#Page = 2, print out count of the entered keywords
		else:

			#Insert new keywords or update count of existing keywords into Keywords Table
			for i in range(len(keywords)) :
				try:
					c.execute('''INSERT INTO Keywords VALUES(?, 0, 1) ''', [keywords[i].lower()])
				except sqlite3.IntegrityError, m:
					c.execute('''UPDATE Keywords SET count = count + 1 WHERE word = ?''', [keywords[i].lower()])
			
			#Output total number of keywords entered if a phrase is entered		
			s = '''<!DOCTYPE HTML>
						 <html> 
						 <head> 
						 		<title>CSC326 Search Engine</title> 
								<style>
									body {text-align:center; margin: auto; position: fixed; color:white;
											top: 0; left: 0; bottom: 0; right: 0; vertical-align:middle;
											background: #000 url('http://static.tumblr.com/1d6145f98f1d856ffa3115853ee85ff0/lh9td6e/p2smmlu6n/tumblr_static_space-background.jpg') 0 0 no-repeat; background-size: 100%;}
}
								</style>
						 </head>
						 <center>
							<h1>Space Explorer <img src="http://goo.gl/2z51Zw" width="50" height="50"></h1>
							<form action="/search" method="POST"> 
								<b>Search Again: </b><input type="text" name="keyword"> 
								<input type="submit" value="Submit"> 
							</form>'''
			if len(keywords) > 1:
				s +='''<BR><BR><text>The number of entered keywords are: %d</text>''' % len(keywords)
			
			#Output Query Results Table	
			#Output header of table
			s += '''<BR><BR>
						 <table border="1"> 
						 <tr> 
						 		<th align=center>  Word  </th> 
						 		<th align=center>  Count  </th> 
						 </tr>
						'''
			#Output each unique keyword and its count in separate rows
			for key in set(keywords):
				c.execute('''SELECT word, count FROM Keywords WHERE word = ? ORDER BY count DESC''', [key.lower()])
				rows = c.fetchall()
				for row in rows:
					s += '''<tr><td align=center> %s </td><td align=center> %d </td></tr>''' % (row[0], row[1])
			
			#Adds the count to total count and reverts the count to 0 for next iteration 
			for i in range(len(keywords)) :
				c.execute('''UPDATE Keywords SET totalcount = totalcount+count, count = 0 WHERE word = ?''', [keywords[i].lower()])

		#Commit the changes and close the connection to the database
		conn.commit()
		conn.close()

		return s

#404 File not Found / Page does not Exist
@error(404)
def error404(error):
	errorpage = '''<!DOCTYPE HTML>
						<html> 
						<head> 
							<title>CSC326 Search Engine</title> 
							<link rel="stylesheet" type="text/css" href="/main.css" /> 
							<style>
								body {text-align:center; margin: auto; position: fixed; color: white;
  										top: 0; left: 0; bottom: 0; right: 0; vertical-align:middle;
										background: #000025	url('http://starscrutiny.files.wordpress.com/2013/10/original.jpg?w=705&h=396') 0 0 no-repeat; background-size: 100%;
}
							</style>
						<meta http-equiv="content-type" content="text/html; charset=iso-8859-1" />
						</head>	
						<body> 
							<h1>ERROR 404: Page Does Not Exist or File is Not Found! </h1>
						</body> 
						</html> 
				'''
					
	#Creates a button to go back to Query Page/Home Page
	errorpage += '''
			<form action="/" method = "link"> 
				<input type="submit" value="Return to Home Page!"> 
			</form>	
			'''
	return errorpage
		
		
		
		
		
		
		
		
		
		
#Runs the server on localhost
#Allows access to webpage through http://localhost:8080/
run(host='localhost', port=8080, debug=True)


