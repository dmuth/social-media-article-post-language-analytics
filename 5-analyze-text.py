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
from nltk.stem import *
from nltk.stem.porter import *
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
parser.add_argument("-ut", "--unusual-words-title", action = "store_true", help = "Display unusual words found in title")
parser.add_argument("-ub", "--unusual-words-body", action = "store_true", help = "Display unusual words found in body")
parser.add_argument("-fw", "--frequent-words", type = int, metavar = "N", help = "Display words occuring more then N times in body")
parser.add_argument("-s", "--stem", action = "store_true", help = "Use stemming on unusual and frequent words")


args = parser.parse_args()
#print(args) # Debugging


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


#
# Conditionally download our NLTK files
#
def nltkDownload():

	try: 
		nltk.word_tokenize("hello world")
		nltk.corpus.words.words()

	except Exception as e:
		logger.warn("Unable to use NLTK tokenizer, let's download our corpus! Error: %s" % (e))
		nltk.download("punkt")
		nltk.download("words")



#
# Extract unusual words from text. 
#
def unusualWords(text, stem):

	text_vocab = set(w.lower() for w in text if w.isalpha() and len(w) <= 15)
	english_vocab = set(w.lower() for w in nltk.corpus.words.words())
	retval = text_vocab - english_vocab

	if stem:
		retval = [stemmer.stem(plural) for plural in retval]

	return (sorted(retval))


#
# Return a list of our frequent words exceeding num. 
# We enforce a minimum of 7 character to avoid small words and get more proper nouns
#
def frequentWords(text, min, stem):

	fdist = nltk.FreqDist(words_text)

	retval = (list(w for w in set(words_text) if fdist[w] > min and len(w) >= 7))

	if stem:
		retval = sorted([stemmer.stem(plural) for plural in retval])

	return(sorted(retval))


nltkDownload()
rows = getUrlsTextCursor(limit = args.limit)

if args.stem:
	stemmer = PorterStemmer()

for row in rows:

	data = json.loads(row["value"])

	title = (" ".join(data.get("title", "")) 
		+ " " + " ".join(data.get("h1", ""))
		+ " " + " ".join(data.get("h2", ""))
		+ " " + " ".join(data.get("h3", ""))
		)
	title = title.replace("\n", "")
	title = title.replace("\r", "")

	print("Title: %s" % title[0:120])
	words_title = list(w.lower() for w in nltk.word_tokenize(title))
	words_text = list(w.lower() for w in nltk.word_tokenize(data["text"]))

	if args.frequent_words:
		print("Frequent words in body (more than %d times): %s" % (args.frequent_words, 
			frequentWords(words_text, args.frequent_words, args.stem)))

	if args.unusual_words_title:
		print("Unusual wods in title: %s" % (unusualWords(words_title, args.stem)))

	if args.unusual_words_body:
		print("Unusual wods in body: %s" % (unusualWords(words_text, args.stem)))

	print("")


print(args) # Debugging

#
# TODO:
#
# Create a function for each of these and arguments to try each:
#
# - Look for colocations: http://www.nltk.org/howto/collocations.html
#	- I should do this for the body
#
# - For each mode (ut, ub, fw) keep running totals in a dictions and print up stats at end
#



