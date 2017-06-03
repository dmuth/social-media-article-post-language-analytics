
# Social Media Article Post Language Analytics

Yeah, that's the best title I could come up with to describe this.  I am so sorry.

Also, let's be clear: this isn't production code.  It's basically a side project that I had been working on
for awhile, got the code as far as I could take it (for now), and decided to publish it so I could move onto
other things.

So awhile back, someone suggested to me that I consder taking all of the links I ever posted to Twitter
and Facebook, download the text, and do some sort of curation or language analytics on them.  That led
down a rabiit hole wherein I got back up to speed on Python, taught myself a few modules such as 
<a href="https://twython.readthedocs.io/en/latest/">Twython</a> (Twitter API integration), 
<a href="http://docs.python-requests.org/en/master/">Requests</a> (for talking to Facebook),
<a href="https://docs.python.org/3/library/argparse.html">Argparse</a> (a fantastic document parser),
and <a href="https://www.sqlite.org/">SQLite</a> (for data storage).


## Installation

- `git clone`
- `virtualenv virtualenv`
- `./virtualenv/bin/activate`
- `pip install -r ./requirements.txt`


## Configuration

You will need to copy `config.ini.example` to `config.ini` and then obtain an Access Token from
Facebook, and an API key and secret from Twitter.


## Usage

This app is broken down into multiple Python scripts, and each script starts with a number, which helps 
make clear which order they should be run in.

All scripts will create their database table in SQLite on an as-needed basis.

All scripts are also written to make use of "INSERT OR REPLACE INTO" syntax so that if the same
script is run multiple times, you will not wind up with duplicate copies of the data.  For example,
if the *1-download-facebook.py* script is run multiple times, existing posts will not get duplicated,
but rather only new posts will be downloaded.


### 1-download-facebook.py

### 1-download-twitter.py

### 2-extract-urls.py

### 3-get-core-urls.py

### 4-extract-text.py

### 5-analyze-text.py


## A bit about database design

Since I'm dealing with different parts of HTML docuemnts (title, body, h1, h2 tags, etc.),
I need a way to store all of those in a database, without having to constantly adjust the
schema.  I wound up geting an idea 
<a href="http://blog.wix.engineering/2015/12/10/scaling-to-100m-mysql-is-a-better-nosql/"
	>from this post in the Wix Engineering Blog</a> which stated: *"Fields only exist to 
be indexed. If a field is not needed for an index, store it in one blob/text field 
(such as JSON or XML)"* and ran with it.  So all tables in this project have a field called 
`value`, which holds JSONified data which contains whatever data I need.  This approach
turned out to be quite useful, because as my needed changed and I decded to add more data,
no schema changes were made.

I'm not sure I would totally advocate this approach for an actual production system, at
least not without extensive testing (which is what Wix appears to have done).


## Troubleshooting

Dealing with this error:

`[SSL: SSLV3_ALERT_HANDSHAKE_FAILURE] sslv3 alert handshake failure (_ssl.c:645)`

You're probably using a an older version of OpenSSL.  Check your OpenSSL version with:

`python -c 'import ssl; print (ssl.OPENSSL_VERSION)'`

If's under 1.0, that's cause for concern.  This is a real problem on MacOS/X.
That said, if you're on MacOS/X, <a href="https://brew.sh/">install HomeBrew</a>
and then install Python 3 and OpenSSL, e.g.: `brew install python3 openssl`.

Now createa new virtualenv folder with the specific path for Python 3:

`virtualenv -p /path/to/homebrew/path/to/python3 virtualenv3`

Activate that virtualenv, and that should use the copy of Python in Homebrew
along with its copy of OpenSSL.  Check again, and you'll be at least version 1.0.2
of OpenSSL as of this writing.

