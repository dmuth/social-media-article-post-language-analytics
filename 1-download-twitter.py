#!/usr/bin/env python


import configparser
import json
import logging as logger
import logging.config
import sys
import time
import webbrowser

import twython

sys.path.append("lib")
import db
import db.tables.data

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
	logging.debug("Auth URL: " + auth_url)

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

twitter = twython.Twython(app_key, app_secret, twitter_data["final_oauth_token"], twitter_data["final_oauth_token_secret"])

creds = twitter.verify_credentials()
rate_limit = twitter.get_lastfunction_header('x-rate-limit-remaining')
logging.info("Rate limit left: " + rate_limit)

screen_name = creds["screen_name"]
logging.info("My screen name is: " + screen_name)




