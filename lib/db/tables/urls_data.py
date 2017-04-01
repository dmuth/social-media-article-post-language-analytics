#
# This module is used for wrapping access to the "twitter" table.
#


import json
import sqlite3


class data():

	#
	# The table we're working with
	#
	table = "urls_data"

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

		schema = (""
			#
			# The URL that was retrieved from Facebook or Twitter.  This is very likely a shortener.
			#
			+ "first_url VARCHAR(255) UNIQUE NOT NULL, "
			#
			# The final URL that it resolves to, if it resolves.
			#
			+ "final_url VARCHAR(255), "
			#
			# The HTTP code from the final URL.
			#
			+ "code VARCHAR(4) DEFAULT '' NOT NULL, "
			#
			# The content type of the response
			#
			+ "content_type VARCHAR(64) DEFAULT '' NOT NULL, "
			#
			# The content of the response.
			#
			+ "content BLOB DEFAULT '' NOT NULL" )

		self.db.createTable(self.table, schema)

	#
	# Fetch a row from the table with the specified first_url value.
	# If a row is found, return true, otherwise return false
	#
	def get(self, first_url):

		query = "SELECT * FROM %s WHERE first_url = ?" % self.table

		cursor = self.db.execute(query, (first_url,))
		row = cursor.fetchone()

		if row:
			return(True)

		return(False)


	#
	# Insert a value for a specific key.
	#
	def put(self, first_url, final_url, code, content_type, content):

		query = "INSERT OR REPLACE INTO %s (first_url, final_url, code, content_type, content) VALUES (?, ?, ?, ?, ?)" % self.table

		self.db.execute(query, (first_url, final_url, code, content_type, content))



