#!/usr/bin/env python
#
# Go through our extracted text and pull our interesting things.
# (I'll be a little more specific once I figure out what I want to do with this script!)
#


import argparse
import configparser
import json
import logging as logger
import logging.config
import nltk
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


parser = argparse.ArgumentParser(description = "Analyze crawled text")
parser.add_argument("-l", "--limit", type = int, help = "Only process a certain number of URLs")

args = parser.parse_args()


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
# Execute a query to get our crawled pages.
#
def getUrlsTextCursor(**kwargs):

	query = "SELECT rowid, * from urls_text "
	if "limit" in kwargs:
		query += " LIMIT %d" % kwargs["limit"]

	retval = sql.execute(query)
	return(retval)


rows = getUrlsTextCursor(limit = args.limit)


for row in rows:

	data = json.loads(row["value"])

	title = (" ".join(data.get("title", "")) 
		+ " " + " ".join(data.get("h1", ""))
		+ " " + " ".join(data.get("h2", ""))
		+ " " + " ".join(data.get("h3", ""))
		)
	title = title.replace("\n", "")
	title = title.replace("\r", "")

	logger.info(title)


#
# TODO:
#
# Create a function for each of these and arguments to try each:
#
# - Look for most common words: fdist = nltk.FreqDist(w.lower() for w in news_text)
# - Look for colocations: http://www.nltk.org/howto/collocations.html
# - most_common()
# - FreqDist(): sorted(w for w in set(text6) if len(w) > 7 and fdist[w] > 7)
# - Copy unusual_words() from http://www.nltk.org/book/ch02.html
#



