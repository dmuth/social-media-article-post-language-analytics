#
# This module is used for wrapping access to the "twitter" table.
#


import json
import sqlite3


class data():

	#
	# The table we're working with
	#
	table = "facebook_posts"

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

		query = "CREATE TABLE %s (post_id INTEGER UNIQUE NOT NULL, value TEXT NOT NULL)" % self.table
		self.db.execute(query)



	#
	# Fetch the first (and only!) row for a specific post_id
	#
	def get(self, post_id):

		query = "SELECT rowid, * FROM %s WHERE post_id=?" % self.table
		results = self.db.execute(query, [post_id])

		for row in results:

			try:
				value = json.loads(row["value"])

			except Exception as e:
				value = row["value"]

			retval = {
				"rowid": row["rowid"],
				"post_id": row["post_id"],
				"value": value,
				}

			retval = value
			retval["rowid"] = row["rowid"]
			retval["post_id"] = row["post_id"]

			return(retval)


	#
	# Insert a value for a specific key.
	#
	def put(self, post_id, value):

		query = "INSERT OR REPLACE INTO %s (post_id, value) VALUES (?, ?)" % self.table

		if "rowid" in value:
			del value["rowid"]
		if "post_id" in value:
			del value["post_id"]

		value = json.dumps(value)
		self.db.execute(query, (post_id, value))


