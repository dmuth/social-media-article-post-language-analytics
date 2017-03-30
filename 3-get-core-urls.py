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
	rs = (grequests.get(u, timeout = timeout, headers = headers) for u in urls)

	results = grequests.map(rs, size=10, exception_handler = exceptionHandler)

	for result in results:

		if result:
			first_url = result.url
			final_url = result.url
			code = result.status_code
			content_type = result.headers["content-type"]
			content = ""


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
			if str(code)[0] == "2" and re.search("^text/", content_type):
				content = result.text

			urls_data.put(first_url, final_url, code, content_type, content)
			logger.info("Stored %d bytes for URL '%s' (code=%d, content-type=%s)" 
				% (len(content), final_url, code, content_type))


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
		if (urls_data.get(first_url)):
			continue

		logger.info("Adding URL '%s' to fetch queue" % first_url)
		urls_to_fetch.append(first_url)

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
url_results = getUrlCursor(limit = 100)
#fetchUrls(url_results, urls_data, max_queue_size = 5)
fetchUrls(url_results, urls_data, max_queue_size = 10)



