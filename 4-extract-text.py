#!/usr/bin/env python
#
# Extract text from our URLs
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

import bs4
import grequests

sys.path.append("lib")
import db
import db.tables.urls_text

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
urls_text = db.tables.urls_text.data(sql)


#
# Execute a query to get URLs from the url table, and return a cursor 
# to the result set.
#
def getUrlsDataCursor(**kwargs):

	query = "SELECT rowid, * from urls_data WHERE content != ''"
	if "limit" in kwargs:
		query += " LIMIT %d" % kwargs["limit"]

	retval = sql.execute(query)
	return(retval)


#
# Go through all occurences of a given tag and extract the text.
#
def extractTextFromTag(tags):

	retval = []

	for tag in tags:
		retval.append(tag.text)

	return(retval)

#
# Pull text out of our content.
#
def extractText(html):

	retval = {}
	soup = bs4.BeautifulSoup(html, "html.parser")

	for script in soup(["script", "style"]):
		script.decompose()

	retval["title"] = extractTextFromTag(soup.find_all("title"))
	retval["h1"] = extractTextFromTag(soup.find_all("h1"))
	retval["h2"] = extractTextFromTag(soup.find_all("h2"))
	retval["h3"] = extractTextFromTag(soup.find_all("h3"))

	#
	# Found at least one post with no body tags, so we'll have to check for them, too.
	#
	if soup.body:
		retval["text"] = soup.body.text[:10240]
	else:
		retval["text"] = soup.get_text()

	return(retval)


limit = 100
#rows = getUrlsDataCursor(limit = limit)
rows = getUrlsDataCursor()

for row in rows:

	logger.info("Parsing content from '%s'..." % row["final_url"])
	first_url = row["first_url"]

	beenhere = urls_text.get(first_url)
	if beenhere:
		logger.info("We already parsed this content, skipping!")
		continue

	html = row["content"]
	data = extractText(html)
	urls_text.put(first_url, row["final_url"], data)


