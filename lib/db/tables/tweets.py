#
# This module is used for wrapping access to the "twitter" table.
#


import json
import sqlite3


class data():

	#
	# The table we're working with
	#
	table = "tweets"

	#
	# Our database object
	#
	db = ""


	def __init__(self, db):
		self.db = db
		#
		# Set the database to return associative arrays
		#
		self.db.conn.row_factory = sqlite3.Row

		#
		# If the table is found, stop.  Otherwise, create it.
		#
		query = "SELECT name FROM sqlite_master WHERE type='table' AND name='%s'" % self.table
		results = self.db.execute(query)
		for row in results:
			return(None)

		query = "CREATE TABLE %s (tweet_id INTEGER UNIQUE NOT NULL, value TEXT NOT NULL)" % self.table
		self.db.execute(query)



	#
	# Fetch the first (and only!) row for a specific tweet_id
	#
	def get(self, tweet_id):

		query = "SELECT rowid, * FROM %s WHERE tweet_id=?" % self.table
		results = self.db.execute(query, [tweet_id])

		for row in results:

			try:
				value = json.loads(row["value"])

			except Exception as e:
				value = row["value"]

			retval = {
				"rowid": row["rowid"],
				"tweet_id": row["tweet_id"],
				"value": value,
				}

			retval = value
			retval["rowid"] = row["rowid"]
			retval["tweet_id"] = row["tweet_id"]

			return(retval)


	#
	# Insert a value for a specific key.
	#
	def put(self, tweet_id, value):

		query = "INSERT OR REPLACE INTO %s (tweet_id, value) VALUES (?, ?)" % self.table

		if "rowid" in value:
			del value["rowid"]
		if "tweet_id" in value:
			del value["tweet_id"]

		value = json.dumps(value)
		self.db.execute(query, (tweet_id, value))


