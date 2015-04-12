from bottle import route, run, post, request, get
import sqlite3

@get('/')
def QueryPage():
		querypage = '''<!DOCTYPE HTML>\
						<html> \
						<head> \
							<title>CSC326 Search Engine</title> \
							<link rel="stylesheet" type="text/css" href="/main.css" /> \
							<style>\
								body {text-align:center; margin: auto; position: fixed;
  										top: 0; left: 0; bottom: 0; right: 0; vertical-align:middle;}\
							</style>\
						<meta http-equiv="content-type" content="text/html; charset=iso-8859-1" />\
						</head>	\
						<body> \
							<h1>Space Explorer <img src="http://goo.gl/2z51Zw" width="50" height="50"></h1>\
							<form action="/search" method="POST"> \
								Search: <input type="text" name="keyword"> \
								<input type="submit" value="Submit"> \
							</form>	\
						</body> \
						</html> \
					'''
		#pass in an empty list, since there is no user input yet		
		keywords = list()
		querypage +=keywords_db(keywords, 1)
		return querypage
		
		
@post('/search')	
def searchpage():
		input = request.forms.get('keyword')
		print "Keywords are ", input
		#empty split will get rid of any whitespace
		keywords = input.split()
		print "Keyword tokens:  ", keywords
		print "# of keywords: ", len(keywords)
		searchpage = keywords_db(keywords, 2)
		return searchpage

def keywords_db(keywords, page):
		conn = sqlite3.connect('example.db')
		c = conn.cursor()
		#c.execute('''DROP TABLE IF EXISTS Keywords''')
		c.execute('''CREATE TABLE IF NOT EXISTS Keywords (word text NOT NULL PRIMARY KEY, count int NOT NULL) ''')
		
		if page == 1:
			#print out top 20 searched keywords
			print 'made table!'
			c.execute('''SELECT * FROM Keywords ORDER BY count DESC''')
			rows = c.fetchall()
			s = '''
						 <center>	
						 <BR>
						 <table border="1"> 
						 <tr> 
						 		<th align=center>  Word  </th> 
						 		<th align=center>  Count  </th> 
						 </tr>'''

			i = 0 #counter, only want top 20
			for row in rows:
				if i > 19:
					break;
				s += '''<tr><td align=center> %s </td><td align=center> %d </td></tr>''' % (row[0], row[1])
				i+=1

		else:
			for i in range(len(keywords)) :
				try:
					c.execute('''INSERT INTO Keywords VALUES(?, 1) ''', [keywords[i].lower()])
				except sqlite3.IntegrityError, m:
					c.execute('''UPDATE Keywords SET count = count + 1 WHERE word = ?''', [keywords[i].lower()])
			#Output results table			
			s = '''<!DOCTYPE HTML>
						 <html> 
						 <head> 
						 		<title>CSC326 Search Engine</title> 
						 </head>
						 <center>
						 <text>The number of entered keywords are: %d</text>''' % len(keywords)
			s += '''
						 <BR>
						 <BR>
						 <table border="1"> 
						 <tr> 
						 		<th align=center>  Word  </th> 
						 		<th align=center>  Count  </th> 
						 </tr>
						'''

			for key in keywords:
				c.execute('''SELECT * FROM Keywords WHERE word = ?''', [key.lower()])
				rows = c.fetchall()
				for row in rows:
					s += '''<tr><td align=center> %s </td><td align=center> %d </td></tr>''' % (row[0], row[1])

		conn.commit()
		conn.close()
		return s


		
run(host='localhost', port=8080, debug=True)


