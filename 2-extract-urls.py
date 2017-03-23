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

import dateutil.parser

sys.path.append("lib")
import db
import db.tables.data
import db.tables.urls

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
urls_table = db.tables.urls.data(sql)

pattern = re.compile("^(http(s)?://.*)")

#
# Select our tweets, break each one up on spaces, and grab anything that 
# looks like a URL.
#
def extractFromTweets(sql, urls_table, pattern):

	query = "SELECT rowid, * FROM tweets "
	results = sql.execute(query)

	for row in results:
		value = row["value"]
		data = json.loads(value)
		text = data["text"]

		words = text.split(" ")
		for word in words:
			result = pattern.match(word)
			if result:
				url = result.group(0)
				urls_table.put(url, data)
				print("Storing URL '%s'..." % url)
	

def extractFromFacebookPosts(sql, urls_table, pattern):

	query = "SELECT rowid, * from facebook_posts"
	results = sql.execute(query)
	
	for row in results:
		value = row["value"]
		data = json.loads(value)
		text = data["message"]

		if "link" in data:
			text += " " + data["link"]

		words = text.split(" ")
		for word in words:
			result = pattern.match(word)
			if result:
				url = result.group(0)
				urls_table.put(url, data)
				print("Storing URL '%s'..." % url)


extractFromTweets(sql, urls_table, pattern)
extractFromFacebookPosts(sql, urls_table, pattern)

	
