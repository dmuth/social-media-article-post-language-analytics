#!/usr/bin/env python
#
# Extract our URLs from Tweets and Facebook posts and store them in the urls table.
#


import configparser
import json
import logging as logger
import logging.config
import re
import requests
import requests.models
import sqlite3
import sys
import time

import grequests

sys.path.append("lib")
import db
import db.tables.data
import db.tables.urls_data

#
# Set up the logger
#
logging.config.fileConfig("logging_config.ini", disable_existing_loggers = True)

#
# Read our configuration
#
config = configparser.ConfigParser()
config.read("config.ini")

#
# Create our data object for writing to the data table.
#
sql = db.db()
sql.conn.row_factory = sqlite3.Row
urls_data = db.tables.urls_data.data(sql)


#
# This function is called whenever we have an exception of some kind 
# while fetching a URL.
#
def exceptionHandler(self, e):
	print("Caught Exception:", e)


#
# Execute a query to get URLs from the url table, and return a cursor 
# to the result set.
#
def getUrlCursor(**kwargs):

	query = "SELECT rowid, * from urls"
	if "limit" in kwargs:
		query += " LIMIT %d" % kwargs["limit"]

	retval = sql.execute(query)
	return(retval)


#
# Download an array of URLs and write the results into the urls_data table
#
def fetchUrlsDownload(urls, urls_data):

	timeout = 10
	logger.info("Fetching %d URLs with timeout of %d secs" % (len(urls), timeout))

	#
	# Setting this to "Mozilla/5.0" as per http://webmasters.stackexchange.com/questions/6205/what-user-agent-should-i-set
	# 
	# TODO: For now, the URL is of my website.  When this code goes public, I'll fix that.
	#
	headers = {"user-agent": "Mozilla/5.0 (compatible; http://www.dmuth.org/)"}

	first_urls = []
	for url in urls:
		first_urls.append(url["first_url"])

	rs = (grequests.get(u, timeout = timeout, headers = headers) for u in first_urls)

	results = grequests.map(rs, size=10, exception_handler = exceptionHandler)

	for result in results:

		if result:
			first_url = result.url
			final_url = result.url
			code = result.status_code
			content = ""
			content_type = ""

			#
			# Some webservers don't return content-type.  That's a new one on me!
			#
			if "content-type" in result.headers:
				content_type = result.headers["content-type"]

			#
			# If this is a photo posted on Twitter, flag it so we don't store the content
			#
			if re.search("//twitter.com.*/status/.*/photo/", final_url):
				content_type = "local/twitter-image"

			if result.history:
				first_url = result.history[0].url
	
			#
			# If we got an HTTP 2xx (success) and the result type was text,
			# copy the result content over to the content variable.
			#
			if str(code)[0] == "2":
				if content_type:
					if re.search("^text/", content_type):
						content = result.text

					else:
						logger.warn("Ignoring URL with content type '%s'" % content_type)
						urls_data.put(first_url, final_url, code, content_type, content)

				else:
					content = result.text

			else:
				logger.warn("Ignoring URL with status code '%d'" % code)
				urls_data.put(first_url, final_url, code, content_type, content)


			urls_data.put(first_url, final_url, code, content_type, content)
			logger.info("Stored %d bytes for URL '%s' (code=%d, content-type=%s)" 
				% (len(content), final_url, code, content_type))

		else:
			logger.warn("Got no result, so there isn't much we can do here...")

	#
	# Now go through our URLs and verify that they were downloaded.  If not, then
	# write that to the urls_data table.
	#
	for url in urls:
		escaped_url = url["escaped_url"]
		if (not urls_data.get(escaped_url)):
			logger.warn("We did not find anything for %s (%s)" % (url["first_url"], escaped_url))
			urls_data.put(escaped_url, "", "", "timed out? not found?", "")


#
# Loop through our list of URLs to fetch and fetch them
#
def fetchUrls(cursor, urls_data, **kwargs):

	max_queue_size = 10
	if "max_queue_size" in kwargs:
		max_queue_size = kwargs["max_queue_size"]

	urls_to_fetch = []

	logger.info("Starting to fetch URLs with max queue size of %d" % max_queue_size)

	for row in cursor:

		#
		# If we already have data on this URL, skip it
		#
		first_url = row["url"]
		#first_url = "http://localhost" # Debugging
		#first_url = "http://google.com" # Debugging
		#first_url = "http://twitter.com" # Debugging

		#
		# I learned the hard way that a URL with unicode in it is converted 
		# into percent-encoded text by requests, which means that the URL 
		# eventually written to the table doesn't byte-for-byte match the 
		# original URL.  I ended up doing a code dive into the requests source 
		# and found the function which converts that URL.  So I'm going to call 
		# it here so that the URL I check for in the database is the same as 
		# what would eventually get written.
		#
		p = requests.models.PreparedRequest()
		p.prepare(url = first_url)

		if (urls_data.get(p.url)):
			continue

		logger.info("Adding URL '%s' to fetch queue" % first_url)
		urls_to_fetch.append({"first_url": first_url, "escaped_url": p.url})

		#
		# If we have enough URLs in our batch, download them.
		#
		if (len(urls_to_fetch) >= max_queue_size):
			fetchUrlsDownload(urls_to_fetch, urls_data)
			urls_to_fetch = []

	#
	# Download whatever's left.
	#
	fetchUrlsDownload(urls_to_fetch, urls_data)


#url_results = getUrlCursor(limit = 10) # Debugging
#url_results = getUrlCursor(limit = 100) # Debugging
#url_results = getUrlCursor(limit = 200)
#url_results = getUrlCursor(limit = 1000)
url_results = getUrlCursor()
#fetchUrls(url_results, urls_data, max_queue_size = 5)
#fetchUrls(url_results, urls_data, max_queue_size = 10)
fetchUrls(url_results, urls_data, max_queue_size = 100)




