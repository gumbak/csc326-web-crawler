from bottle import route, run, post, request, get, error
import sqlite3


#Global var to keep track of current search results page and search key
#Set to page 1 for default
pagenum = 1
searchkey = ''

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
		#Use HTML & CSS to make the query page
		loginpage = '''<!DOCTYPE HTML>
						<html> 
						<head> 
							<title>CSC326 Search Engine</title> 
							<style>
								body {text-align:center; margin: 0 0 1px; position: fixed; 
  										top: 0; left: 0; bottom: 0; right: 0; vertical-align:middle; 
										}
}								button{background-color:#f24537; color: white;}
							</style>
						<meta http-equiv="content-type" content="text/html; charset=iso-8859-1" />
						</head>	
						<body> 
							<script src="http://code.jquery.com/jquery-latest.js" type="text/javascript"></script>
							<script type="text/javascript">
							window.___gcfg = {
								lang: 'eng', parsetags: 'onload'
								
							};
							(function() {
									var po = document.createElement('script'); po.type = 'text/javascript'; po.async = true;
									po.src = 'https://apis.google.com/js/plusone.js';
									var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(po, s);
								})();
							
							</script>

							<script type="text/javascript">
								//Creating a global var to store access_token
								var access_token;
								function signinCallback(authResult) {
									if (authResult['access_token']) {
										// Update the app to reflect a signed in user
										// Hide the sign-in button now that the user is authorized, for example:
										document.getElementById('signinButton').setAttribute('style', 'display: none');
										
										//Display the search bar and submit button now
										document.getElementById('searchForm').setAttribute('style', 'display: block');
										document.getElementById('revokeButton').setAttribute('style', 'display: block');
									} else if (authResult['error']) {
										// Update the app to reflect a signed out user
										// Possible error values:
										//   "user_signed_out" - User is signed-out
										//   "access_denied" - User denied access to your app
										//   "immediate_failed" - Could not automatically log in the user
										console.log('Sign-in state: ' + authResult['error']);
									}
									window.access_token = authResult['access_token'];
									assign(window.access_token);
								}
					
								function disconnectUser() {
									var revokeUrl = 'https://accounts.google.com/o/oauth2/revoke?token=' + window.access_token;

									// Perform an asynchronous GET request.
									$.ajax({
										type: 'GET',
										url: revokeUrl,
										async: false,
										contentType: "application/json",
										dataType: 'jsonp',
										success: function(nullResponse) {
											// The response is always undefined.
											//set access_token to signed_out
											window.access_token = 'signed out';
											assign(window.access_token);
											revert(window.access_token);
										},
										error: function(e) {
											// Handle the error
											// console.log(e);
											// You could point users to manually disconnect if unsuccessful
											// https://plus.google.com/apps
										}
									});
								}
								function revert(access_token){
									if (access_token == 'signed out' || access_token == 'error'){
										//Put back the signing button
										document.getElementById('signinButton').setAttribute('style', 'display: block');
										//Hide the search bar and submit button now
										document.getElementById('searchForm').setAttribute('style', 'display: none');
										document.getElementById('revokeButton').setAttribute('style', 'display: none');
										//Open new window to log user out of google+
										myWindow = window.open('https://mail.google.com/mail/u/0/?logout&hl=en'); 
										//gapi.auth.signOut();
									};
								}
								function assign(access_token){
									var xmlhttp;
									if (window.XMLHttpRequest)
									  {// code for IE7+, Firefox, Chrome, Opera, Safari
									  xmlhttp=new XMLHttpRequest();
									  }
									else
									  {// code for IE6, IE5
									  xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
									  }
									xmlhttp.onreadystatechange=function()
									  {
									  if (xmlhttp.readyState==4 && xmlhttp.status==200)
										{
										document.getElementById("myDiv").innerHTML=xmlhttp.responseText;
										}
									  }
									xmlhttp.open("GET","/setAccessToken?accesstk="+access_token,true);
									xmlhttp.send();
								}
							</script>
							<span id="signinButton">
								<span
									class="g-signin"
									data-callback="signinCallback"
									data-clientid="476613193859.apps.googleusercontent.com"
									data-cookiepolicy="single_host_origin"
									data-requestvisibleactions="http://schemas.google.com/AddActivity"
									data-scope="https://www.googleapis.com/auth/plus.login">
								</span>
							</span>
							<center>
							<button id="revokeButton" name="revokeButton" style="display:none" onclick="disconnectUser()">Log Out</button>
							<h3>Space Explorer <img src="http://goo.gl/2z51Zw" width="50" height="50"></h3>
							<div style="display:none;" id="searchForm" name="searchForm">
								<form action="/results" method="POST"> 
									<b>Search: </b><input type="text" id ="searchBar" name="keyword" > 
									<input type="submit" id="submitButton" name="submitb"value="Submit">
								</form>
							</div>
						</body> 
						</html> 
					'''

		return loginpage

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
		searchpage = getData()
		return searchpage

@get('/results')
def getData():
		print 'access_token: '+access_token
		if access_token == 'signed out' or access_token == 'error' or access_token == 'undefined':
			return error403('cannot access, not logged in');

		#Connect to Database
		conn = sqlite3.connect("dbFile.db")
		c = conn.cursor()

		#Find all URLs that contain the searchkey and order by page rank
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
									ON docTitle.docID = pageRank.docID
								 WHERE lex.word = ? 
								 ORDER BY rank DESC, url ASC''', [searchkey])
		
		rows = c.fetchall()
		
		#Calculate total number of pages needed to display 10 results per page
		numrows = len(rows)
		numpages = numrows/maxres
		if (numrows%maxres): 
			numpages += 1

		#Send SQL results, total page number and current page number
		s = resultsTable(rows, numpages, pagenum)
		#Close the connection to the database
		conn.close()
		return s


@route('/setPageNum')
def setPage():
		#Updates current page number 
		global pagenum
		pagenum = request.query.pagenm
		getData()

@route('/getAccessToken')
def getAccessToken():
		print 'in get token function, token = ' + access_token
		return access_token

def resultsTable(rows, numpages, i):
		#Template for Search Results page & results table
		#Includes javascript function for pagination - keeps track of which page button is pressed
		s = '''<!DOCTYPE HTML>
						 <html> 
						 <head> 
						 		<title>CSC326 Search Engine</title> 
								<style>
									body {text-align:center; margin: auto; position: fixed; 
											top: 0; left: 0; bottom: 0; right: 0; vertical-align:middle;}
}
								</style>
								<script src="http://code.jquery.com/jquery-latest.js" type="text/javascript"></script>
								<script type="text/javascript">
									var access_token;
										function getAccessToken(){
											var xmlhttp;
											if (window.XMLHttpRequest)
												{// code for IE7+, Firefox, Chrome, Opera, Safari
												xmlhttp=new XMLHttpRequest();
												}
											else
												{// code for IE6, IE5
												xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
												}
											xmlhttp.onreadystatechange=function()
												{
												if (xmlhttp.readyState==4 && xmlhttp.status==200)
													{
													window.access_token = xmlhttp.responseText;
													disconnectUser();
													}
											}
											xmlhttp.open("GET","/getAccessToken",true);
											xmlhttp.send();
										}
										function disconnectUser() {
											var revokeUrl = 'https://accounts.google.com/o/oauth2/revoke?token=' + window.access_token;
											// Perform an asynchronous GET request.
											$.ajax({
												type: 'GET',
												url: revokeUrl,
												async: false,
												contentType: "application/json",
												dataType: 'jsonp',
												success: function(nullResponse) {
													// The response is always undefined.
													//set access_token to signed_out
													window.access_token = 'signed out';
													assign(window.access_token);
													//Sign user out of Google
													myWindow = window.open('https://mail.google.com/mail/u/0/?logout&hl=en'); 
													//Redirect to HomePage
													window.location.replace("http://localhost:8080");
													myWindow.onload = function () { myWindow.close();};
												},
												error: function(e) {
													
													// Handle the error
													// console.log(e);
													// You could point users to manually disconnect if unsuccessful
													// https://plus.google.com/apps
												}
											});
										}
					
										function assign(access_token){
											var xmlhttp;
											if (window.XMLHttpRequest)
												{// code for IE7+, Firefox, Chrome, Opera, Safari
												xmlhttp=new XMLHttpRequest();
												}
											else
												{// code for IE6, IE5
												xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
												}
											xmlhttp.onreadystatechange=function()
												{
												if (xmlhttp.readyState==4 && xmlhttp.status==200)
												{
												document.getElementById("myDiv").innerHTML=xmlhttp.responseText;
												}
												}
											xmlhttp.open("GET","/setAccessToken?accesstk="+access_token,true);
											xmlhttp.send();
										}
									  function checkBtn(event) {
										pagenm = event.target.name;
										var xmlhttp;
										if (window.XMLHttpRequest)
										  {// code for IE7+, Firefox, Chrome, Opera, Safari
										  xmlhttp=new XMLHttpRequest();
										  }
										else
										  {// code for IE6, IE5
										  xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
										  }
										xmlhttp.onreadystatechange=function()
										  {
										  if (xmlhttp.readyState==4 && xmlhttp.status==200)
											{
											document.getElementById("myDiv").innerHTML=xmlhttp.responseText;
											}
										  }
										xmlhttp.open("GET","/setPageNum?pagenm="+pagenm,true);
										xmlhttp.send();
										
									}
								</script>
						 </head>
						 <center>
							<button id="revokeButton" name="revokeButton" onclick="getAccessToken()">Log Out</button>
							<h1>Space Explorer <img src="http://goo.gl/2z51Zw" width="50" height="50"></h1>
							<form action="/results" method="POST"> 
								<b>Search Again: </b><input type="text" name="keyword"> 
								<input type="submit" value="Submit"> 
							</form>
						<BR><BR>
						<div style="height:450px; overflow: auto;">
						<table border="1"> 
						<tr> 
							<th align=center>  Title  </th> 
							<th align=center>  URL  </th> 
							<th align=center>  Description  </th> 
						</tr>
						<div id="container"><div class="loadedcontent" min-height: 3000px;>
				 '''
		#Show 10 results per page. Results include title, URL, and description (row[0] contains pagerank)
		#Results shown are based on the current page number 
		n = (int(i)-1)*maxres+1
		for row in rows[n-1:n+maxres-1]:
			s += '''<tr><td align=center> %s </td><td align=center> %s </td><td align=center style="font-size:13px"> %s </td></tr>''' % (row[1], row[2], row[3])

		s +='''</table></div></div>
			 		 <form action="/results" method = "link">'''

		#If number of pages is greater than 1, start pagination, show page buttons
		if numpages > 1:
			for x in range(1, numpages+1):
				s +='''<input type="submit" name=%d id=%d value=%d onClick="checkBtn(event)"> 	'''%(x, x, x)
		s+='''</form>'''
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

@error(403)
def error403(error):
	errorpage = '''<!DOCTYPE HTML>
						<html> 
						<head> 
							<title>CSC326 Search Engine</title> 
							<link rel="stylesheet" type="text/css" href="/main.css" /> 
							<style>
								body {text-align:center; margin: auto; position: fixed; color: white;
  										top: 0; left: 0; bottom: 0; right: 0; vertical-align:middle;
										background: #000025	url('http://farm2.static.flickr.com/1168/1043205025_36fbaf8d69.jpg') 0 0 no-repeat; background-size: 100%;
}
							</style>
						<meta http-equiv="content-type" content="text/html; charset=iso-8859-1" />
						</head>	
						<body> 
							<h1>ERROR 403: Forbidden! You are not authorized to access this page! </h1>
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


