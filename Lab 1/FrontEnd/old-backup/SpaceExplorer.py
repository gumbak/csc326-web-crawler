from bottle import route, run, post, request, get
import sqlite3

@get('/')
def QueryPage():
		#Use HTML & CSS to make the query page
		querypage = '''<!DOCTYPE HTML>
						<html> 
						<head> 
							<title>CSC326 Search Engine</title> 
							<link rel="stylesheet" type="text/css" href="/main.css" /> 
							<style>
								body {text-align:center; margin: auto; position: fixed;
  										top: 0; left: 0; bottom: 0; right: 0; vertical-align:middle;}
							</style>
						<meta http-equiv="content-type" content="text/html; charset=iso-8859-1" />
						</head>	
						<body> 
							<h1>Space Explorer <img src="http://goo.gl/2z51Zw" width="50" height="50"></h1>
							<form action="/search" method="POST"> 
								Search: <input type="text" name="keyword"> 
								<input type="submit" value="Submit"> 
							</form>	
						</body> 
						</html> 
					'''
		#Pass in an empty list, since there is no user input yet		
		keywords = list()
		querypage +=keywords_db(keywords, 1)
		return querypage
		
		
@post('/search')	
def SearchPage():
		#Retrieves the user input
		input = request.forms.get('keyword')
		
		#Tokenize the user input into separate keywords
		#Empty split will get rid of any whitespace
		keywords = input.split()
		
		#Send keywords to Database
		searchpage = keywords_db(keywords, 2)
		return searchpage

def keywords_db(keywords, page):
		#Create an empty string
		s = ''
		#Connect to Database
		conn = sqlite3.connect('example.db')
		c = conn.cursor()
		
		#c.execute('''DROP TABLE IF EXISTS Keywords''') #For clean up purposes
		
		#Create table to store keywords and count (if doesn't exist already)
		c.execute('''CREATE TABLE IF NOT EXISTS Keywords (word text NOT NULL PRIMARY KEY, count int NOT NULL) ''')
		
		#Page = 1, print out top 20 on the Query Page
		if page == 1:

			#Print out top 20 searched keywords, if exists
			c.execute('''SELECT * FROM Keywords ORDER BY count DESC''')
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
					c.execute('''INSERT INTO Keywords VALUES(?, 1) ''', [keywords[i].lower()])
				except sqlite3.IntegrityError, m:
					c.execute('''UPDATE Keywords SET count = count + 1 WHERE word = ?''', [keywords[i].lower()])
			
			#Output total number of keywords entered if a phrase is entered		
			s = '''<!DOCTYPE HTML>
						 <html> 
						 <head> 
						 		<title>CSC326 Search Engine</title> 
						 </head>
						 <center>'''
			if len(keywords) > 1:
				s +='''
						 <text>The number of entered keywords are: %d</text>''' % len(keywords)
			
			#Output Query Results Table	
			#Output header of table
			s += '''
						 <BR>
						 <BR>
						 <table border="1"> 
						 <tr> 
						 		<th align=center>  Word  </th> 
						 		<th align=center>  Count  </th> 
						 </tr>
						'''
			#Output each unique keyword and its count in separate rows
			for key in list(set(keywords)):
				c.execute('''SELECT * FROM Keywords WHERE word = ?''', [key.lower()])
				rows = c.fetchall()
				for row in rows:
					s += '''<tr><td align=center> %s </td><td align=center> %d </td></tr>''' % (row[0], row[1])
			
			#Creates a button to go back to Query Page
			s += '''
						<form action="/" method = "link"> 
								<input type="submit" value="Search Again"> 
						</form>	
						</html> 
					'''
		#Commit the changes and close the connection to the database
		conn.commit()
		conn.close()

	



		return s


#Runs the server on localhost
#Allows access to webpage through http://localhost:8080/
run(host='localhost', port=8080, debug=True)


