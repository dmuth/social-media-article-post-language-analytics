#
# This module is used for wrapping access to the "twitter" table.
#


import json
import sqlite3


class data():

	#
	# The table we're working with
	#
	table = "urls"

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

		query = "CREATE TABLE %s (url VARCHAR(255) UNIQUE NOT NULL, value TEXT NOT NULL)" % self.table
		self.db.execute(query)


	#
	# Insert a value for a specific key.
	#
	def put(self, url, value):

		query = "INSERT OR REPLACE INTO %s (url, value) VALUES (?, ?)" % self.table

		if "rowid" in value:
			del value["rowid"]
		if "url" in value:
			del value["url"]

		value = json.dumps(value)
		self.db.execute(query, (url, value))


