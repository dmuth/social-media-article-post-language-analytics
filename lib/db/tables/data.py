#
# This module is used for wrapping access to the "data" table.
#


import sqlite3


class data():

	#
	# The table we're working with
	#
	table = "data"

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
	# Fetch the first (and only!) row for a specific key.
	#
	def get(self, key):

		query = "SELECT rowid, * FROM %s WHERE key=?" % self.table
		results = self.db.execute(query, [key])

		for row in results:

			retval = {
				"rowid": row["rowid"],
				"key": row["key"],
				"value": row["value"],
				}
			return(retval)


	#
	# Insert a value for a specific key.
	#
	def put(self, key, value):
		query = "INSERT OR REPLACE INTO %s (key, value) VALUES (?, ?)" % self.table
		self.db.execute(query, (key, value))


