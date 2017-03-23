#!/usr/bin/env python
#
# Download our statuses from Facebook and save them to the databsae.
#


import configparser
import json
import logging as logger
import logging.config
import requests
import sys
import time

import dateutil.parser

sys.path.append("lib")
import db
import db.tables.data
import db.tables.facebook_posts

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
data_posts = db.tables.facebook_posts.data(sql)

access_token = config["facebook"].get("access_token")


#
# Should we return a post?
#
# @return mixed If we're keeping the post, True is returned. Otherwise, 
#	a string with the code why we're not keeping it is returned.
#
def keepPost(post):

	if not "message" in post:
		return("no_message")

	#
	# If there's no link, check for one in content.
	#
	if not "link" in post:

		if "message" in post:
			if "http://" in post["message"]:
				return(True)
			if "https://" in post["message"]:
				return(True)

		return("no_link")

	if "twitter.com" in post["link"]:
		return("link_twitter")

	#
	# We don't care about photos.
	#
	if not "status_type" in post:
		return("no_status_type")

	if post["status_type"] == "added_photos":
		return("status_type_photos")

	if "application" in post:
		if "name" in post["application"]:
			#
			# Old posts mirrored from Twitter. Mostly useless.
			#
			if post["application"]["name"] == "Twitter":
				return("application_twitter")

			#
			# Stuff I post via Buffer is generally solid.
			#
			if post["application"]["name"] == "Buffer":
				return(True)


	#
	# We're gonna default to dropping this, but since there is
	# a very long tail of reasons why to drop a post, it's best just
	# to group them together as "unknown".
	#
	return("unknown")


#
# Retrieve some posts from Facebooke.
# 
# @param string access_token The access token
# @param integer limit The number of posts to retrieve
#
# @return dict A dictionary containing posts and stats on 
#	how many posts were skipped and why
#
def getPosts(access_token, limit, **kwargs):

	retval = {"posts": [], "count": 0, "skipped": {}}

	if "next" in kwargs and next:
		url = kwargs["next"]

	else:
		fields = "status_type,created_time,message,story,link,application"
		url = ("https://graph.facebook.com/me/feed?fields=" + fields + 
			"&limit=" + str(limit) + "&access_token=" + access_token)

	r = requests.get(url)

	logger.info("Status Code from Facebook: " + str(r.status_code))

	for row in r.json()["data"]:

		result = keepPost(row)

		if result != True:
			reason = result
			if not reason in retval["skipped"]:
				retval["skipped"][reason] = 0

			retval["skipped"][reason] += 1
			continue

		post = {}
		post["message"] = row["message"]
		post["created_time_raw"] = row["created_time"]
		post["created_time"] = int(dateutil.parser.parse(row["created_time"]).timestamp())
		post["id"] = row["id"]
		if "link" in row:
			post["link"] = row["link"]

		retval["posts"].append(post)
		retval["count"] += 1

	if "paging" in r.json():
		if "next" in r.json()["paging"]:
			retval["next"] = r.json()["paging"]["next"]

	return(retval)


#
# Convert our skipped stats into text which can be printed.
#
def getSkippedText(stats):

	retval = ""
	for key, value in stats["skipped"].items():
	
		if retval:
			retval += ", "

		retval += "skipped_" + key + "=" + str(value)

	return(retval)


num_posts_left = 10000
limit = 200
stats = {"num_posts_written": 0, "skipped": {}}

next = ""

while True:

	logger.info("Querying Facebook Graph for %d posts..." % limit)
	results = getPosts(access_token, limit, next=next)
	num_posts_left -= results["count"]

	if not "next" in results:
		logger.info("No \"next\" link in paging, stopping!")
		break

	next = results["next"]

	skipped_text = ""

	for key, value in results["skipped"].items():

		if not key in stats["skipped"]:
			stats["skipped"][key] = 0
		stats["skipped"][key] += value

		if skipped_text:
			skipped_text += ", "

		skipped_text += "skipped_" + key + "=" + str(value)

	for post in results["posts"]:
		id = post["id"]
		data_posts.put(id, post)
		stats["num_posts_written"] += 1

	logger.info("posts=%d, %s" % (results["count"], skipped_text))
	logger.info("posts_written: %d, %s" % (stats["num_posts_written"], getSkippedText(stats)))

	if (num_posts_left <= 0):
		break

logger.info("posts_written: %d, %s" % (stats["num_posts_written"], getSkippedText(stats)))







