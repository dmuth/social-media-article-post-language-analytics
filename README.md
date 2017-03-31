

## Installation

- `git clone`
- `virtualenv virtualenv`
- `./virtualenv/bin/activate`



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

