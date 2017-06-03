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
parser.add_argument("-l", "--limit", type = int, help = "Only process a certain number of URLs", default = 5)
parser.add_argument("-q", "--quiet", action = "store_true", help = "Quiet mode. If specified, don't print out unusual/frequent words for each post, just the totals at the end")
parser.add_argument("-s", "--stem", action = "store_true", help = "Use stemming on words FIRST, before doing anything else")
parser.add_argument("-ut", "--unusual-words-title", action = "store_true", help = "Display unusual words found in title")
parser.add_argument("-ub", "--unusual-words-body", action = "store_true", help = "Display unusual words found in body")
parser.add_argument("-fw", "--frequent-words", type = int, metavar = "N", help = "Display words occuring more then N times in body")


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
def unusualWords(text):

	text_vocab = set(w.lower() for w in text if w.isalpha() and len(w) <= 15)
	english_vocab = set(w.lower() for w in nltk.corpus.words.words())
	retval = text_vocab - english_vocab

	return (sorted(retval))


#
# Return a list of our frequent words exceeding num. 
# We enforce a minimum of 7 character to avoid small words and get more proper nouns
#
def frequentWords(text, min):

	retval = {}

	fdist = nltk.FreqDist(words_text)

	for word in fdist:
		if len(word) > 7:
			if fdist[word] > min:
				retval[word] = fdist[word]

	return(retval)


nltkDownload()
rows = getUrlsTextCursor(limit = args.limit)

if args.stem:
	stemmer = PorterStemmer()

totals = {}
totals["frequent_words"] = {}
totals["unusual_words_title"] = {}
totals["unusual_words_body"] = {}

for row in rows:

	data = json.loads(row["value"])

	title = (" ".join(data.get("title", "")) 
		+ " " + " ".join(data.get("h1", ""))
		+ " " + " ".join(data.get("h2", ""))
		+ " " + " ".join(data.get("h3", ""))
		)
	title = title.replace("\n", "")
	title = title.replace("\r", "")

	print("Processing post: %s" % title[0:120])
	words_title = list(w.lower() for w in nltk.word_tokenize(title))
	words_text = list(w.lower() for w in nltk.word_tokenize(data["text"]))

	#
	# Are we stemming the words from the body?
	#
	if args.stem:
		words_title = [stemmer.stem(plural) for plural in words_title]
		words_text = [stemmer.stem(plural) for plural in words_text]

	if args.frequent_words:

		freq = frequentWords(words_text, args.frequent_words)

		for word in freq:
			if not word in totals["frequent_words"]:
				totals["frequent_words"][word] = 0
			totals["frequent_words"][word] += freq[word]

		if not args.quiet:
			print("Frequent words in body (more than %d times): %s" % (args.frequent_words, freq))


	if args.unusual_words_title:
		words = unusualWords(words_title)

		for word in words:
			if not word in totals["unusual_words_title"]:
				totals["unusual_words_title"][word] = 0
			totals["unusual_words_title"][word] += 1

		if not args.quiet:
			print("Unusual wods in title: %s" % (words))


	if args.unusual_words_body:
		words = unusualWords(words_text)

		for word in words:
			if not word in totals["unusual_words_body"]:
				totals["unusual_words_body"][word] = 0
			totals["unusual_words_body"][word] += 1

		if not args.quiet:
			print("Unusual wods in body: %s" % (words))

print("")
print("Totals:", totals)


