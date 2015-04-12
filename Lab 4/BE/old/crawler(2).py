
# Copyright (C) 2011 by Peter Goodman
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the folowing conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

#
# Updated: Sept 13, 2013
#


import urllib2
import urlparse
from BeautifulSoup import *
from collections import defaultdict
import re
import sqlite3 as lite

# Global variables. Lab 1. -K
# 3 main global variables are docIndex, lex, and invIndex.
docIndex = {};
docTitle = {};
docParDescript = {};
lex = {};
invIndex = {};
pageRank = {};
outboundLinks = {};

def attr(elem, attr):
    """An html attribute from an html element. E.g. <a href="">, then
    attr(elem, "href") will get the href or an empty string."""
    try:
        return elem[attr]
    except:
        return ""

WORD_SEPARATORS = re.compile(r'\s|\n|\r|\t|[^a-zA-Z0-9\-_]')

class crawler(object):
    """Represents 'Googlebot'. Populates a database by crawling and indexing
    a subset of the Internet.

    This crawler keeps track of font sizes and makes it simpler to manage word
    ids and document ids."""

    def __init__(self, db_conn, url_file):
        """Initialize the crawler with a connection to the database to populate
        and with the file containing the list of seed URLs to begin indexing."""
        self._url_queue = [ ]
        self._doc_id_cache = { }
        self._word_id_cache = { }

        # functions to call when entering and exiting specific tags
        self._enter = defaultdict(lambda *a, **ka: self._visit_ignore)
        self._exit = defaultdict(lambda *a, **ka: self._visit_ignore)

        # add a link to our graph, and indexing info to the related page
        self._enter['a'] = self._visit_a

        # record the currently indexed document's title an increase
        # the font size
        def visit_title(*args, **kargs):
            self._visit_title(*args, **kargs)
            self._increase_font_factor(7)(*args, **kargs)
          

	# Store paragraph if within <p> head
	# Lab 1 bonus. -K
	def visit_paragraph(*args, **kargs):
            self._visit_paragraph(*args, **kargs)
	
	
        # increase the font size when we enter these tags
        self._enter['b'] = self._increase_font_factor(2)
        self._enter['strong'] = self._increase_font_factor(2)
        self._enter['i'] = self._increase_font_factor(1)
        self._enter['em'] = self._increase_font_factor(1)
        self._enter['h1'] = self._increase_font_factor(7)
        self._enter['h2'] = self._increase_font_factor(6)
        self._enter['h3'] = self._increase_font_factor(5)
        self._enter['h4'] = self._increase_font_factor(4)
        self._enter['h5'] = self._increase_font_factor(3)
        self._enter['title'] = visit_title
        self._enter['TITLE'] = visit_title

	# Store information of text with <p> header. Lab 1 bonus. -K
	self._enter['P'] = visit_paragraph
	self._enter['p'] = visit_paragraph

        # decrease the font size when we exit these tags
        self._exit['b'] = self._increase_font_factor(-2)
        self._exit['strong'] = self._increase_font_factor(-2)
        self._exit['i'] = self._increase_font_factor(-1)
        self._exit['em'] = self._increase_font_factor(-1)
        self._exit['h1'] = self._increase_font_factor(-7)
        self._exit['h2'] = self._increase_font_factor(-6)
        self._exit['h3'] = self._increase_font_factor(-5)
        self._exit['h4'] = self._increase_font_factor(-4)
        self._exit['h5'] = self._increase_font_factor(-3)
        self._exit['title'] = self._increase_font_factor(-7)

        # never go in and parse these tags
        self._ignored_tags = set([ 
            'meta', 'script', 'link', 'meta', 'embed', 'iframe', 'frame', 
            'noscript', 'object', 'svg', 'canvas', 'applet', 'frameset', 
            'textarea', 'style', 'area', 'map', 'base', 'basefont', 'param',
        ])

        # set of words to ignore
        self._ignored_words = set([
            '', 'the', 'of', 'at', 'on', 'in', 'is', 'it',
            'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j',
            'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't',
            'u', 'v', 'w', 'x', 'y', 'z', 'and', 'or',
        ])

        # TODO remove me in real version
        self._mock_next_doc_id = 1
        self._mock_next_word_id = 1

        # keep track of some info about the page we are currently parsing
        self._curr_depth = 0
        self._curr_url = ""
        self._curr_doc_id = 0
        self._font_size = 0
        self._curr_words = None

        # get all urls into the queue
        try:
            with open(url_file, 'r') as f:
                for line in f:
                    self._url_queue.append((self._fix_url(line.strip(), ""), 0))
        except IOError:
            pass
    
    # TODO remove me in real version
    def _mock_insert_document(self, url):
        """A function that pretends to insert a url into a document db table
        and then returns that newly inserted document's id."""
        ret_id = self._mock_next_doc_id
        self._mock_next_doc_id += 1
        return ret_id
    
    # TODO remove me in real version
    def _mock_insert_word(self, word):
        """A function that pretends to inster a word into the lexicon db table
        and then returns that newly inserted word's id."""
        ret_id = self._mock_next_word_id
        self._mock_next_word_id += 1
        return ret_id
    
    def word_id(self, word):
        """Get the word id of some specific word."""
   
        if word in self._word_id_cache:
            return self._word_id_cache[word]
        
        # TODO: 1) add the word to the lexicon, if that fails, then the
        #          word is in the lexicon
        #       2) query the lexicon for the id assigned to this word, 
        #          store it in the word id cache, and return the id.

        word_id = self._mock_insert_word(word)
        self._word_id_cache[word] = word_id

	# Populate lexicon. -K
	global lex

        if not lex.has_key(word_id):
		lex[word_id] = re.sub('<[^<]+?>', '', str(word)).rstrip()
  
        return word_id
    
    def document_id(self, url):
        """Get the document id for some url."""
        if url in self._doc_id_cache:
            return self._doc_id_cache[url]
        
        # TODO: just like word id cache, but for documents. if the document
        #       doesn't exist in the db then only insert the url and leave
        #       the rest to their defaults.
        
        doc_id = self._mock_insert_document(url)
        self._doc_id_cache[url] = doc_id

	# Save doc ID and current words into global variable docIndex. Lab 1. -K
	# global docIndex
        # docIndex[doc_id] = str(url).rstrip()

        return doc_id
    
    def _fix_url(self, curr_url, rel):
        """Given a url and either something relative to that url or another url,
        get a properly parsed url."""

        rel_l = rel.lower()
        if rel_l.startswith("http://") or rel_l.startswith("https://"):
            curr_url, rel = rel, ""
            
        # compute the new url based on import 
        curr_url = urlparse.urldefrag(curr_url)[0]
        parsed_url = urlparse.urlparse(curr_url)
        return urlparse.urljoin(parsed_url.geturl(), rel)
    def add_link(self, from_doc_id, to_doc_id):
        """Add a link into the database, or increase the number of links between
        two pages in the database."""
        # TODO

    def _visit_title(self, elem):
        """Called when visiting the <title> tag."""
        title_text = self._text_of(elem).strip()
	
	# Store document title in docTitle for bonus. Lab 1. -K
	global docTitle

        if not docTitle.has_key(self._curr_doc_id):
		docTitle[self._curr_doc_id] = str(title_text).rstrip()

        print "document title="+ repr(title_text)

        # TODO update document title for document id self._curr_doc_id
    
    def _visit_paragraph(self, elem):
        """Called when visiting the <p> or <P> tag."""
        # Retrieve paragraph when first entering URL. Lab 1. -K
	# paragraph_text = None
        # paragraph_text = re.sub('<[^<]+?>', '', self._text_of(elem)).strip()

    	# # Find paragraph data to store into docParDescript. Lab 1 bonus. -K
	# global docParDescript

	# if paragraph_text is not None or not paragraph_text.isspace():
	# 	docParDescript[self._curr_doc_id] = [str(paragraph_text).rstrip()]
    
    def _visit_a(self, elem):
        """Called when visiting <a> tags."""

        dest_url = self._fix_url(self._curr_url, attr(elem,"href"))

        global outboundLinks

        if not outboundLinks.has_key(self._curr_doc_id):
        	outboundLinks[self._curr_doc_id] = [self.document_id(dest_url)]
        else:
            	outboundLinks[self._curr_doc_id].append(self.document_id(dest_url))


        #print "href="+repr(dest_url), \
        #      "title="+repr(attr(elem,"title")), \
        #      "alt="+repr(attr(elem,"alt")), \
        #      "text="+repr(self._text_of(elem))

        # add the just found URL to the url queue
        self._url_queue.append((dest_url, self._curr_depth))
        
        # add a link entry into the database from the current document to the
        # other document
        self.add_link(self._curr_doc_id, self.document_id(dest_url))

        # TODO add title/alt/text to index for destination url
    
    def _add_words_to_document(self):
        # TODO: knowing self._curr_doc_id and the list of all words and their
        #       font sizes (in self._curr_words), add all the words into the
        #       database for this document
        
        print "    num words="+ str(len(self._curr_words)).rstrip()

    def _increase_font_factor(self, factor):
        """Increade/decrease the current font size."""
        def increase_it(elem):
            self._font_size += factor
        return increase_it
    
    def _visit_ignore(self, elem):
        """Ignore visiting this type of tag"""
        pass

    def _add_text(self, elem):
        """Add some text to the document. This records word ids and word font sizes
        into the self._curr_words list for later processing."""
        words = WORD_SEPARATORS.split(elem.string.lower())
     
        for word in words:
            word = word.strip()
            if word in self._ignored_words:
                continue

            wordID = self.word_id(word)
            self._curr_words.append((wordID, self._font_size))
      
            # Populate inverted index
            global invIndex

            if invIndex.has_key(wordID):
		if self._curr_doc_id not in invIndex[wordID]:
                    invIndex[wordID].append(self._curr_doc_id)
            else:
        	invIndex[wordID]=[self._curr_doc_id]
        

    def _text_of(self, elem):
        """Get the text inside some element without any tags."""
        if isinstance(elem, Tag):
            text = [ ]
            for sub_elem in elem:
                text.append(self._text_of(sub_elem))        
            return " ".join(text)
        else:
            return elem.string

    def _index_document(self, soup):
        """Traverse the document in depth-first order and call functions when entering
        and leaving tags. When we come accross some text, add it into the index. This
        handles ignoring tags that we have no business looking at."""
        class DummyTag(object):
            next = False
            name = ''
        
        class NextTag(object):
            def __init__(self, obj):
                self.next = obj
        
        tag = soup.html
        stack = [DummyTag(), soup.html]

        while tag and tag.next:
            tag = tag.next

            # html tag
            if isinstance(tag, Tag):

                if tag.parent != stack[-1]:
                    self._exit[stack[-1].name.lower()](stack[-1])
                    stack.pop()

                tag_name = tag.name.lower()

                # ignore this tag and everything in it
                if tag_name in self._ignored_tags:
                    if tag.nextSibling:
                        tag = NextTag(tag.nextSibling)
                    else:
                        self._exit[stack[-1].name.lower()](stack[-1])
                        stack.pop()
                        tag = NextTag(tag.parent.nextSibling)
                    
                    continue
                
                # enter the tag
                self._enter[tag_name](tag)
                stack.append(tag)

            # text (text, cdata, comments, etc.)
            else:
                self._add_text(tag)

    # Find paragraph data to store into docParDescript. Lab 1 bonus. -K
    def _curr_parag(self, soup):
	global docParDescript
 	# Three types of paragraphs obtained through beautiful soup
	# 1. <P>
        # 2. <p>
        # 3. <meta...name:description...>
	parUpperFromSoup = soup.findAll('P')
	parLowerFromSoup = soup.findAll('p')
	metaDescriptFromSoup = soup.findAll(attrs={"name":"description"})
       
        # Helps take out unusual tags/patterns in retrieved string.
        pattern = re.compile(r'<.*?>')

        # Remove all strange characters and retrieve just the text.
        if parUpperFromSoup:
            for index in range(len(parUpperFromSoup)):
                savePar = None
                if parUpperFromSoup[index]:
                    re.sub('<[^>]*>', '', parUpperFromSoup[index])
             
                # Only store if the string obtained has no unusual characters
                if parUpperFromSoup[index]:
                    if not str(parUpperFromSoup[index]).isspace():
                	savePar = pattern.sub('',str(parUpperFromSoup[index]))
                        #Take out any extra whitespace
                        savePar = ' '.join(str(savePar).split())

                # Store these obtained paragraphs into the global variable docParDescript
                if savePar and not savePar.isspace():
                    if docParDescript.has_key(self._curr_doc_id):
                        if savePar not in docParDescript[self._curr_doc_id]:
                            docParDescript[self._curr_doc_id].append(savePar)
                    else:
                        docParDescript[self._curr_doc_id] = [savePar]

        
        # Do the same for <p>
        if parLowerFromSoup:
            for index in range(len(parLowerFromSoup)):
                savePar = None
                if parLowerFromSoup[index]:
                    re.sub('<[^>]*>', '', str(parLowerFromSoup[index])) 
            
                if parLowerFromSoup[index]:
                    if not str(parLowerFromSoup[index]).isspace():  
                        savePar = pattern.sub('',str(parLowerFromSoup[index]))
                        # Take out extra whitespace
                        savePar = ' '.join(str(savePar).split())
       
                # Store these obtained paragraphs into the global variable docParDescript
                if savePar and not savePar.isspace():
                    if docParDescript.has_key(self._curr_doc_id):
                        if savePar not in docParDescript[self._curr_doc_id]:
                            docParDescript[self._curr_doc_id].append(savePar)
                    else:
                        docParDescript[self._curr_doc_id] = [savePar]

        # Do the same for meta
        if metaDescriptFromSoup:
            for index in range(len(metaDescriptFromSoup)):
                savePar = None
                if metaDescriptFromSoup[index]:
                    re.sub('<[^>]*>', '', str(metaDescriptFromSoup[index]))

                if metaDescriptFromSoup[index]:
                    if not str(metaDescriptFromSoup[index]).isspace():
                        savePar = pattern.sub('',str(metaDescriptFromSoup[index]))
                        # Take out extra whitespace
                        savePar = ' '.join(str(savePar).split())
      
            # Store these obtained paragraphs into the global variable docParDescript
                if savePar and not savePar.isspace():
                    if docParDescript.has_key(self._curr_doc_id):
                        if savePar not in docParDescript[self._curr_doc_id]:
                            docParDescript[self._curr_doc_id].append(savePar)
                else:
                    docParDescript[self._curr_doc_id] = [savePar]
       
    # # Find meta data to store into docMetaDescript. Lab 1 bonus. -K
    # def _curr_meta(self, soup):
    #     global docMetaDescript
    #     meta_text = None
    #     if soup.find("meta", {"name":"description"}) is not None:
    #         meta_text = soup.find("meta", {"name":"description"})['content']

    #     if meta_text is not None or meta_text is not '':
    #         if not docMetaDescript.has_key(self._curr_doc_id): 
    #     	docMetaDescript[self._curr_doc_id] = [str(meta_text).rstrip()]
    #         elif len(docMetaDescript[self._curr_doc_id]) < 3:
    #     	docMetaDescript[self._curr_doc_id].append(str(meta_text).rstrip())
   
    # Find paragraph data to store into docParDescript. Lab 1 bonus. -K
    # def _curr_title(self, soup):
    #     # Titles obtained through beautiful soup
    #     titleFromSoup = soup.findAll('title')

    #     # Remove all strange characters and retrieve just the text.
    #     if titleFromSoup:
    #         for index in range(len(titleFromSoup)):        
    #         	if titleFromSoup[index]:
    #                 re.sub('<[^<]+?>', '', str(titleFromSoup[index])).rstrip()
    #                 titleFromSoup = str(titleFromSoup).split('<title>')[1].split('</title>')[0]
    #                 print titleFromSoup
    #                 # Only store if the string obtained has no unusual characters
    #                 if titleFromSoup[index]:
    #                     if not str(titleFromSoup[index]).isspace():  
    #                         global docTitle
    #                         docTitle[self._curr_doc_id] = titleFromSoup[index]
                           
    def _curr_title(self, soup):
	global docTitle
 	# Three types of paragraphs obtained through beautiful soup
	# 1. <P>
        # 2. <p>
        # 3. <meta...name:description...>
	titleLowerFromSoup = soup.findAll('title')
	titleUpperFromSoup = soup.findAll('TITLE')
  
        # Helps take out unusual tags/patterns in retrieved string.
        pattern = re.compile(r'<.*?>')
    
        # Remove all strange characters and retrieve just the text.
        if titleLowerFromSoup:
            for index in range(len(titleLowerFromSoup)):
                title_name = None
            
                if titleLowerFromSoup[index]:
                    re.sub('<[^>]*>', '', str(titleLowerFromSoup[index]))
                
                # Only store if the string obtained has no unusual characters
                if titleLowerFromSoup[index]:
                    if not str(titleLowerFromSoup[index]).isspace():
                	title_name = pattern.sub('',str(titleLowerFromSoup[index]))
                        #Take out any extra whitespace                   
                        title_name = ' '.join(str(title_name).split())
     
                # Store title
                if title_name and not title_name.isspace():     
                    if not docTitle.has_key(self._curr_doc_id): 
                        docTitle[self._curr_doc_id] = title_name
              
    
        if titleUpperFromSoup:
            for index in range(len(titleUpperFromSoup)):
                title_name = None
                if titleUpperFromSoup[index]:
                    re.sub('<[^>]*>', '', str(titleUpperFromSoup[index]))
                
                # Only store if the string obtained has no unusual characters
                if titleUpperFromSoup[index]:
                    if not str(titleUpperFromSoup[index]).isspace():
                	title_name = pattern.sub('',str(titleUpperFromSoup[index]))
                        #Take out any extra whitespace
                        title_name = ' '.join(str(title_name).split())

                # Store title
                if title_name and not title_name.isspace():
                    if not docTitle.has_key(self._curr_doc_id):
                            docTitle[self._curr_doc_id] = title_name
    

    def crawl(self, depth=2, timeout=3):
	#Initialize global variables. -K
	global docIndex
	global lex
	global invIndex

        """Crawl the web!"""
        seen = set()

        while len(self._url_queue):

            url, depth_ = self._url_queue.pop()
     

            # skip this url; it's too deep
            if depth_ > depth:
                continue
      
            doc_id = self.document_id(url)
       
            # Store pageRank
            # Only increment page rank if it is within the set depth of crawler. If beyond depth, do not store for consistency.
            # global pageRank
        
            # if doc_id not in pageRank:
            # 	pageRank[doc_id] = 1
            # else:
    	    #     pageRank[doc_id] = pageRank[doc_id] + 1 

            # we've already seen this document
            if doc_id in seen:
                continue
            
            seen.add(doc_id) # mark this document as haven't been visited
            
            socket = None
            try:
                socket = urllib2.urlopen(url, timeout=timeout)
                soup = BeautifulSoup(socket.read())
                
                self._curr_depth = depth_ + 1
                self._curr_url = url
                self._curr_doc_id = doc_id
                self._font_size = 0
                self._curr_words = [ ]
                self._index_document(soup)
		# self._curr_title(soup)                
		self._curr_parag(soup)      
                self._curr_title(soup)
                self._add_words_to_document()

                if not docIndex.has_key(doc_id):
                	docIndex[doc_id] = str(url).rstrip()

                print "    url="+repr(self._curr_url)
                print "    doc_id="+repr(self._curr_doc_id)
            except Exception as e:
                print e
                pass
            finally:
                if socket:
                    socket.close()

        # Calculate page rank
        self.rankPage()

        # Store data structures into SQL database.
        self.storeIntoSQL()

    def rankPage(self):
        global pageRank
        global outboundLinks

        damping_factor = 0.85

        inboundLinks = {}

        # Calculate inbound links
        for key,value in outboundLinks.iteritems():
            for index in range(len(value)):
                if not inboundLinks.has_key(value[index]):
                    inboundLinks[value[index]] = [key]
                else:
                    inboundLinks[value[index]].append(key)

        # Calculate partial page rank: pageRank = (1 - damping_factor) / numberOutbounds
        for key,index in docIndex.iteritems():
            if outboundLinks.has_key(key):
                pageRank[key] = (1 - damping_factor) / (len(outboundLinks[key]))
            else:
                pageRank[key] = 0

        # Add partial outbounds of other pageRanks that link to it, over 20 iterations
        # pageRank = curr_pageRank + sum(damping_factor*(pageRankOfInbound)/numOutboundlinks)  
        for repeat in range(0,20):               
            for key,value in inboundLinks.iteritems():
                if docIndex.has_key(key):
                	pageRank[key] = (1 - damping_factor) / (len(value))
                	for index in range(len(value)):
                    		# print pageRank[key]
                    		# print value[index]
                    		# print pageRank[value[index]]
                    		# print outboundLinks[value[index]]
                    		pageRank[key] = pageRank[key] + damping_factor*pageRank[value[index]]/len(outboundLinks[value[index]])
                
    # Print SQL statements of corresponding input word.
    def get_SQL_from_word(self, word):
	con = lite.connect("dbFile.db")
        cur = con.cursor()
    
        with con:
		cur.execute('''SELECT dI.url, dT.title, dPD.descript, pR.rank
			     FROM docIndex dI, docTitle dT, docParDescript dPD, lex l, invIndex iI, pageRank pR
			     WHERE l.word = ?
				AND l.wordID = iI.wordID
				AND iI.docID = dI.docID
				AND iI.docID = dT.docID
				AND iI.docID = dPD.docID
				AND iI.docID = pR.docID''', [word])
                data = cur.fetchall()
        print data
                
        con.close()
	return 

    # Store all global data structures into SQL
    # Allows persistant storage for access in front end
    def storeIntoSQL(self):
        global docIndex
        global docTitle
        global docParDescript
        global lex
        global invIndex
        global pageRank

        # Create SQL connection
        con = lite.connect("dbFile.db")
        cur = con.cursor()
        
        # Create tables for each global variable
        with con:
            cur.execute('CREATE TABLE IF NOT EXISTS docIndex(docID INTEGER PRIMARY KEY, url TEXT);')

            cur.execute('CREATE TABLE IF NOT EXISTS docTitle(docID INTEGER PRIMARY KEY, title TEXT);')

            cur.execute('CREATE TABLE IF NOT EXISTS docParDescript(docID INTEGER PRIMARY KEY, descript TEXT);')

            cur.execute('CREATE TABLE IF NOT EXISTS lex(wordID INTEGER PRIMARY KEY, word TEXT);')

            cur.execute('CREATE TABLE IF NOT EXISTS invIndex(wordID INTEGER, docID INTEGER, PRIMARY KEY(wordID,docID));')

            cur.execute('CREATE TABLE IF NOT EXISTS pageRank(docID INTEGER PRIMARY KEY, rank INTEGER);')

        # Store docIndex
        with con:
            for key,value in docIndex.iteritems():
                try:
                    cur.execute('''INSERT INTO docIndex(docID,url) VALUES(?,?)''', (key,str(value)))
                except lite.IntegrityError, m:
                    cur.execute('''UPDATE docIndex SET url=? WHERE docID=?''', (str(value),key))
                   
                # data = cur.execute('''SELECT * FROM docIndex''')
                # rows = cur.fetchall()
                # print data
                # print rows
                # print "I'm here!!!"

        # Store docTitle
        with con:
            for key,value in docTitle.iteritems():
                try:
                    cur.execute('''INSERT INTO docTitle VALUES (?,?)''', (key,str(value)))
                except lite.IntegrityError, m:
                    cur.execute('''UPDATE docTitle SET title=? WHERE docID=?''', (str(value),key))

        # Store docParDescript
        with con:
            for key,value in docParDescript.iteritems():
                try:
                    cur.execute('INSERT INTO docParDescript VALUES (?,?)', (key,str(" ".join(str(value)))))
                except lite.IntegrityError, m:
                    cur.execute('''UPDATE docParDescript SET descript=? WHERE docID=?''', (str(" ".join(str(value))),key))
                # data = cur.execute('''SELECT * FROM docParDescript''')
                # rows = cur.fetchall()
                # print data
                # print rows
                # print "I'm here!!!"

        # Store lex
        with con:
            for key,value in lex.iteritems():
                try:
                    cur.execute('INSERT INTO lex VALUES (?,?)', (key,str(value)))
                except lite.IntegrityError, m:
                    cur.execute('''UPDATE lex SET word=? WHERE wordID=?''', (str(value),key))

        # Store invIndex
        with con:
            for key,value in invIndex.iteritems():
                for index in range(len(value)):
                    try:
                        cur.execute('INSERT INTO invIndex VALUES (?,?)', (key,value[index]))
                    except lite.IntegrityError, m:
                        cur.execute('DELETE FROM invIndex WHERE wordID=? AND docID=?',(key,value[index]))
                        cur.execute('INSERT INTO invIndex VALUES (?,?)', (key,value[index]))
                        #cur.execute('''UPDATE invIndex SET docID=? WHERE wordID=?''', (value[index],key))


        # Store pageRank
        with con:
            for key,value in pageRank.iteritems():
                try:
                    cur.execute('INSERT INTO pageRank VALUES (?,?)', (key,value))
                except lite.IntegrityError, m:
                    cur.execute('''UPDATE pageRank SET rank=? WHERE docID=?''', (value,key))

        with con:
            data = cur.fetchone()
            con.commit()

        # print data
        # print "Hello"
        con.close()



# get_inverted index
# Returns invIndex as a dictionary    
    def get_inverted_index(self):
	global invIndex
	dictInvIndex = {}

	# inverted index is stored in dictInvIndex and returned.
	for key,value in invIndex.iteritems():
		dictInvIndex[key] = set(value)
	return dictInvIndex
	
# get_resolved_inverted_index
# Returns a dictionary with IDs replaces with words in inverted index
    def get_resolved_inverted_index(self):
         global invIndex
         global docIndex
         global lex

         dictResInvIndex = {}

	# Go through all keys in invIndex
         for key,value in invIndex.iteritems():
             urls = list()

             # Find corresponding URL for each doc ID stored in the value of the inverted index.        
	     for i in range(len(value)):
	       	urls.append(docIndex[value[i]])
             dictResInvIndex[lex[key]] = set(urls)
  	
         return dictResInvIndex

    # get_url_title
    # Returns URL and its corresponding title
    # Lab 1 bonus. -K
    def get_url_title(self):
	global docTitle
	global docIndex
	
	dictURLtitle = {}

	# Go through all titles saved in dictURLtitle and return it.
	for key,value in docIndex.iteritems():
	       titleValue = None	

               if docTitle.has_key(key):
			titleValue = docTitle[key]

               if titleValue:
			dictURLtitle[value] = titleValue
               else:	
			dictURLtitle[value] = "No title available..."


	return dictURLtitle

    # get_url_description
    # Returns URL and corresponding, relevant strings within that URL
    # Lab 1 bonus. -K
    def get_url_description(self):
	global docIndex
        global docParDescript

	dictURLdescript = {}

	# Go through all stored descriptions in docParDescript and return it
	for key, value in docIndex.iteritems():
            par_text = []
            if docParDescript.has_key(key):
                for index in range(len(docParDescript[key])):
                    if docParDescript[key][index] and not docParDescript[key][index].isspace():
                    	par_text.append(docParDescript[key][index])
          
            if par_text:
                dictURLdescript[value] = set(par_text)               
            else:
            	dictURLdescript[value] = "No description available..."
    
	return dictURLdescript


    # Return a dictionary of page ranks
    def get_page_ranks(self):
	global pageRank
    
	return pageRank
    
if __name__ == "__main__":
    bot = crawler(None, "urls.txt")
    bot.crawl(depth=1)
    print "THE END"

# using shell
# from crawler import crawler
# bot = crawler

# docIndex. Save doc ID and URL
# List with 2 columns
# 1st column: docID
# 2nd column: URL

# lex. Save word ID and words
# List with 2 columns
# 1st column: wordID
# 2nd column: word

# Inverted index. save word ID as key and related doc ID
# List with 2 columns
# 1st column: word ID
# 2nd column: Another list containing docIDs with related word ID

# get_inverted_index(). return dict, containing set.
# word ID : set (doc ID)

# get_resolved_inverted_index()
# actual word : set (URl)

