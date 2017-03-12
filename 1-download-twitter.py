#!/usr/bin/env python


import configparser
import json
import logging as logger
import logging.config
import sys
import time
import webbrowser

import dateutil.parser
import twython

sys.path.append("lib")
import db
import db.tables.data
import db.tables.tweets

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
data = db.tables.data.data(sql)
data_tweets = db.tables.tweets.data(sql)

app_key = config["twitter"].get("app_key")
app_secret = config["twitter"].get("app_secret")
logger.debug("App Key: " + app_key)
logger.debug("App Secret: " + app_secret)

#
# Fetch our data from the database.  If we don't have any data, then
# go through the process of getting auth tokens, which is a somewhat involved
# process which also includes opening up a web browser window. (ugh)
#
twitter_data = data.get("twitter_data")

if (not twitter_data):

	logger.info("No cached Twitter credentials found, let's fetch them!")

	twitter = twython.Twython(app_key, app_secret)

	auth = twitter.get_authentication_tokens()

	auth_url = auth["auth_url"]
	logger.debug("Auth URL: " + auth_url)

	print("# ")
	print("# We could not find Twitter credentials, so we'll need to get them.")
	print("# To do that, we will open up a web browser window to Twitter's")
	print("# authentication page.  ")
	print("# ")
	print("# Once the page opens up, copy the code and paste it in the prompt below.")
	print("# ")
	print("# Note that you MAY have to log in to Twitter. ")
	print("# ")
	webbrowser.open(auth_url)
	oauth_verifier = input('Enter Your PIN: ')

	oauth_token = auth['oauth_token']
	oauth_token_secret = auth['oauth_token_secret']
	logger.debug("OAUTH Token: " + oauth_token)
	logger.debug("OAUTH Token Secret: " + oauth_token_secret)

	twitter = twython.Twython(app_key, app_secret, oauth_token, oauth_token_secret)

	try:
		final_step = twitter.get_authorized_tokens(oauth_verifier)

	except twython.exceptions.TwythonError as e:
		print ("! ")
		print ("! Caught twython.exceptions.TwythonError:", e)
		print ("! ")
		print ("! Did you enter the right PIN code?")
		print ("! ")
		exit(1)

	final_oauth_token = final_step['oauth_token']
	final_oauth_token_secret = final_step['oauth_token_secret']
	logger.debug("Final OUATH token: " + final_oauth_token)
	logger.debug("Final OAUTH token secret: " + final_oauth_token_secret)

	twitter_data = {
		"final_oauth_token": final_oauth_token,
		"final_oauth_token_secret": final_oauth_token_secret,
		"created": int(time.time()),
		}

	data.put("twitter_data", twitter_data)


#
# Fetch a number of tweets from Twitter.
#
# @param object twitter - Our Twitter oject
# @param integer count - How many tweets to fetch?
# @param kwarg max_id - The maximum Id of tweets so we can go back in time
#
# @return A dictionary that includes tweets that aren't RTs, the count, the last ID,
#	and how many tweets were skipped.
#
def getTweets(twitter, count, **kwargs):

	#retval = {"tweets": [], "count": 0, "skipped": 0, "last_id": -1}
	retval = {"tweets": [], "count": 0, "skipped": 0}
	logger.info("getTweets(): count=%d, last_id=%d" % (count, kwargs["last_id"]))
	
	#
	# If we have a last ID, decrement it by one and query Twitter accordingly,
	# otherwise we start at the top of the timeline.
	#
	if ("last_id" in kwargs and kwargs["last_id"]):
		max_id = kwargs["last_id"] - 1
		tweets = twitter.get_user_timeline(
			user_id = screen_name, exclude_replies = True, include_rts = True, 
			count = count, max_id = max_id)

	else: 
		tweets = twitter.get_user_timeline(
			user_id = screen_name, exclude_replies = True, include_rts = True, 
			count = count)

	last_id = None

	for row in tweets:
		text = row["text"]

		#
		# Skip RTs
		#
		if (text[0] == "R" and text[1] == "T"):
			retval["skipped"] += 1
			continue

		if not "http://" in text and not "https://" in text:
			retval["skipped"] += 1
			continue

		id = row["id"]

		tweet = {"text": text, "id": id, 
				"timestamp": int(dateutil.parser.parse(row["created_at"]).timestamp()), 
				"timestamp_raw": row["created_at"]
				}
		retval["tweets"].append(tweet)
		retval["count"] += 1
		retval["last_id"] = id;
		
	return(retval)

#
# Verify our Twitter credentials
#
twitter = twython.Twython(app_key, app_secret, twitter_data["final_oauth_token"], twitter_data["final_oauth_token_secret"])

creds = twitter.verify_credentials()
rate_limit = twitter.get_lastfunction_header('x-rate-limit-remaining')
logger.info("Rate limit left for verifying credentials: " + rate_limit)

screen_name = creds["screen_name"]
logger.info("My screen name is: " + screen_name)


tweets = []
num_tweets_left = 5000
#num_tweets_left = 500
#num_tweets_left = 100
#num_tweets_left = 20
num_tweets_to_fetch = 200
#num_tweets_to_fetch = 100
#num_tweets_to_fetch = 50
num_tweets_written = 0
last_id = False

num_passes_zero_tweets = 5
num_passes_zero_tweets_left = num_passes_zero_tweets


#
# Fetch tweets in a loop until we hit our max.
#
while True:

	result = getTweets(twitter, num_tweets_to_fetch, last_id = last_id)
	num_tweets_left -= result["count"]

	if result["count"] == 0:
		num_passes_zero_tweets_left -= 1
		logger.info("We got zero tweets this pass! passes_left=%d (Are we at the end of the timeline?)" % 
			num_passes_zero_tweets_left)
		if num_passes_zero_tweets_left == 0:
			logger.info("Number of zero passes left == 0. Yep, we're at the end of the timeline!")
			break
		continue

	#
	# We got some tweets, reset our zero tweets counter
	#
	num_passes_zero_tweets_left = num_passes_zero_tweets


	#logger.info("Tweets fetched=%d, skipped=%d, last_id=%d" % (result["count"], result["skipped"], result["last_id"]))
	logger.info("Tweets fetched=%d, skipped=%d, last_id=%s" % (result["count"], result["skipped"], result.get("last_id", None)))
	logger.info("Tweets left to fetch: %d" % num_tweets_left)
	rate_limit = twitter.get_lastfunction_header('x-rate-limit-remaining')
	logger.info("Rate limit left: " + rate_limit)

	if "last_id" in result:
		last_id = result["last_id"]

	tweets.extend(result["tweets"])

	for row in result["tweets"]:
		tweet_id = row["id"]
		tweet = row
		data_tweets.put(tweet_id, tweet)
		num_tweets_written += 1

	if (num_tweets_left <= 0):
		break

	


logger.info("Total tweets written: %d" % num_tweets_written)



