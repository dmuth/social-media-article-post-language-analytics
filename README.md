
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
<a href="https://www.crummy.com/software/BeautifulSoup/">Beautiful Soup</a> (HTML parsing),
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

This script will download as many of your Facebook posts as it can, and write them
to the `facebook_posts` table.

If you do not have a Facebook Access Token, you'll need to retrieve one from 
<a href="https://developers.facebook.com/tools/explorer">https://developers.facebook.com/tools/explorer</a>

This script employs some basic sanity checking--posts that don't have links, have
links to Twitter, or are photos will be skipped.

A successful run will generate lines like these:

```
2017-06-03 16:44:07,301 INFO: Querying Facebook Graph for 200 posts...
2017-06-03 16:44:08,192 INFO: Status Code from Facebook: 200
2017-06-03 16:44:08,269 INFO: posts=85, skipped_no_message=3, skipped_no_link=112
2017-06-03 16:44:08,269 INFO: posts_written: 1036, skipped_no_status_type=2, skipped_status_type_photos=1649, skipped_link_twitter=12, skipped_unknown=226, skipped_no_message=284, skipped_application_twitter=140, skipped_no_link=1446
```

Note that even through we asked Facebook for 200 posts, we don't always get 200 posts.  
As far as I can tell, that's normal behavior for their API.


### 1-download-twitter.py

This script will download your Tweets from Twitter.  For reasons only Twitter knows, just the
last 3200 tweets are available.

Part of the process of authentication to Twitter involves opening up a web browser to retrieve
a code from Twitter and then paste it into a prompt the script generates.  This code is then
stored in the table `data`.

This script employs sanity checking to to skip Tweets that don't have links or are RTs.

A successful run produces results like these:
```
2017-06-03 17:37:49,027 INFO: getTweets(): count=200, last_id=861355973117714432
2017-06-03 17:37:49,336 INFO: Tweets fetched=65, skipped=79, last_id=852296277933076484
2017-06-03 17:37:49,336 INFO: Tweets left to fetch: 4865
2017-06-03 17:37:49,337 INFO: Rate limit left: 898
```


### 2-extract-urls.py

This script goes through all of the saved Tweets and Facebook posts, extracts the URL(s)
present in each post, and writes them out to the the `urls` table.  Since we are making 
use of `INSERT OR REPLACE INTO`, if the same URL is posted to both Twitter and Facebook
(URL shorteners not withstanding), only one row will wind up in the table so as to
avoid duplicated.


### 3-get-core-urls.py

This script goes through the process of downloading the contents of each URL 
(if it hasn't already been downloaded) and storing the results in the `urls_data` table.
Once the URL is downloaded, the "final" de-shortened URL is noted as well, and the
original URL, the final URL, and the contents are written to `urls_data`.

This script is by **far** the most network-intensive part of this project.

By default, 100 URLs are downloaded with a 10 second timeout.  Then there is sanity checking
which catches things like Twitter photos (which can't be caught by the Content-Type header)
and non-2XX responses.  All results (including non-2XX) are written to the table, to ensure
that we don't repeatedly try to call 404 pages, images, etc.

Sanity checking will also be applied to filter out Twitter images, links to other Twitter posts, 
and links to Facebook posts.

A successful run will print results at the end in a table similar to this:

```
                            Content-Type	Code	Count
                            ============	====	=====
                                 (blank)	 200	    2
                         application/pdf	 200	    1
                               image/gif	 200	    8
                              image/jpeg	 200	   52
                          local/facebook	 200	   13
                           local/twitter	 200	  195
                     local/twitter-image	 200	  574
                               text/html	 200	  227
                text/html; charset=utf-8	 200	  936
                text/html;;charset=UTF-8	 200	   14
                 text/html;charset=UTF-8	 200	   87
                              text/plain	 200	    2
                   timed out? not found?	    	  129
                              video/webm	 200	    1
```

Anything that starts with `local/` isn't an actual Content-Type, just a way for my script
to note that we did not crawl that URL for some reason.


### 4-extract-text.py

This script goes through `urls_data`, pulls the text of every URL that was crawled,
parses the HTML, and then writes it to the `urls_text` table.

There are a few key tags that we pay attention to, namely the title, and any h1, h2, and h3 tags.
The body is also grabbed, but only the first 10K (so as to keep things to a reasonable size).


### 5-analyze-text.py


Finally, the text analysis part!  This is the whole reason why I wrote this project, and why
I wanted to play around with the <a href="http://www.nltk.org/">Natural Language ToolKit</a>.

Running this script with `-h` will give you a list of options, but in summary, the following 
operations can be performed against all content stored in the `urls_text` table:

- Get a list of unusual words in the titles
- Get a list of unusual words in the post bodies
- Display words occuring in post bodies more than a certain number of times
- Perform stemming on all words before any of the above operations

When the script is complete, totals will be printed for unusual words or frequent words 
(if either/both were searched for).

A successful run will display output similar to this:
```

Number of posts processed: 1775

Top unusual words that were found in post bodies:

Unusual words that showed up 583 times: years
Unusual words that showed up 566 times: terms
Unusual words that showed up 561 times: facebook
Unusual words that showed up 530 times: things
Unusual words that showed up 483 times: using
Unusual words that showed up 426 times: email
Unusual words that showed up 365 times: features
Unusual words that showed up 360 times: called
Unusual words that showed up 350 times: states
Unusual words that showed up 332 times: makes
Unusual words that showed up 330 times: developers, comments

Top unusual words that were found in post titles:

Unusual words that showed up 176 times: youtube
Unusual words that showed up 160 times: comments
Unusual words that showed up 123 times: posts
Unusual words that showed up 98 times: stories
Unusual words that showed up 97 times: facebook
Unusual words that showed up 85 times: online
Unusual words that showed up 81 times: categories
Unusual words that showed up 77 times: things
Unusual words that showed up 69 times: viewing
Unusual words that showed up 67 times: email

Top frequent words that were found in post bodies:

Unusual words that showed up 259 times: featured
Unusual words that showed up 145 times: password
Unusual words that showed up 110 times: facebook
Unusual words that showed up 98 times: mcdonald’s
Unusual words that showed up 89 times: bloomberg
Unusual words that showed up 86 times: hydraulic
Unusual words that showed up 78 times: pinterest
Unusual words that showed up 76 times: toothpaste, comments, dynamite
Unusual words that showed up 73 times: undertale, javascript
```

Looking at the unusual words above, it's apparent that I like to post links to
articles which mention Facebook, along with article about developers, and
YouTube videos.  Looking at the frequent words, I apparently link to Bloomberg a lot
and like to talk about <a href="http://undertale.com/">Undertale</a> and Javascript.


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


## TODO / Room For Improvement

I only got up to speed on the argparse module towards the end of this project.  I should
really add support for argument parsing into the scripts that download social media posts
and the contents of the URLs in them.  That would make future development a little easier
in that I could limit a run to just 5 posts, rather than having to tweak code to do that.


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


## Final Thoughts

Even though the end product didn't turn out as awesome as I hoped it would, I still learned
a lot about Nautral Language Processing and the substantial amount of work that goes into it.
It gives me a greater appreaciation for what happens "behind the scenes" with Google queries
as well as Siri.

I don't see myself doing much more work on this particular project, as NLP is definately 
not my paritcular brand of vodka, but I figured I'd share the code just so others can take
a look at it and maybe find it useful.




