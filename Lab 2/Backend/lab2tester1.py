# CSC326 Lab 1
# Tester for crawler

# This program shall crawl the URL in urls.txt.
# It shall use function crawler.get_inverted_index() and print output.

from crawler import crawler

if __name__ == "__main__":
    bot = crawler(None,"urls.txt")
    bot.crawl(depth=1)
    
    pageRank = bot.get_page_ranks()
    print pageRank
