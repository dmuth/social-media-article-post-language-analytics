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
import db.tables.posts

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
data_posts = db.tables.posts.data(sql)

access_token = config["facebook"].get("access_token")


#
# Retrieve some posts from Facebooke.
# 
# @param string access_token The access token
# @param integer limit The number of posts to retrieve
#
def getPosts(access_token, limit, **kwargs):

	retval = {"posts": [], "count": 0, 
		"skipped_not_shared_story": 0, "skipped_no_link": 0}

	if "next" in kwargs and next:
		url = kwargs["next"]

	else:
		fields = "status_type,created_time,message,story,link"
		url = ("https://graph.facebook.com/me/feed?fields=" + fields + 
			"&limit=" + str(limit) + "&access_token=" + access_token)

	r = requests.get(url)

	logger.info("Status Code: " + str(r.status_code))

	for row in r.json()["data"]:

		if row["status_type"] != "shared_story":
			retval["skipped_not_shared_story"] += 1
			continue

		if not "message" in row:
			retval["skipped_no_link"] += 1
			continue

		post = {}
		post["message"] = row["message"]
		post["created_time_raw"] = row["created_time"]
		post["created_time"] = int(dateutil.parser.parse(row["created_time"]).timestamp())
		post["id"] = row["id"]
		post["link"] = row["link"]

		retval["posts"].append(post)
		retval["count"] += 1

	retval["next"] = r.json()["paging"]["next"]

	return(retval)


num_posts_left = 1000
limit = 100
stats = {"num_posts_written": 0, "skipped_not_shared_story": 0, "skipped_no_link": 0}

next = ""

while True:

	logger.info("Querying Facebook Graph for %d posts..." % limit)
	results = getPosts(access_token, limit, next=next)
	num_posts_left -= results["count"]
	next = results["next"]
	logger.info("posts=%d, skipped_not_shared_story=%d, skipped_no_link=%d num_posts_left=%d" % (
		results["count"], results["skipped_not_shared_story"], 
		results["skipped_no_link"], num_posts_left))
	stats["skipped_no_link"] += results["skipped_no_link"]
	stats["skipped_not_shared_story"] += results["skipped_not_shared_story"]


	for post in results["posts"]:
		id = post["id"]
		data_posts.put(id, post)
		stats["num_posts_written"] += 1

	if (num_posts_left <= 0):
		break

logger.info("posts_written: %d, skipped_no_link=%d, skipped_not_shared_story=%d" % (
	stats["num_posts_written"], stats["skipped_no_link"], stats["skipped_not_shared_story"]))






