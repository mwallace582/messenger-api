# Messenger API

A simple messenger API written in Python with Flask.

## Getting Started

### Dependencies

* Linux or Mac OS
* Python 3.9.X
    * See requirements.txt for python dependencies
* SQLite 3.36.X
* jq (optional)
    * Makes it easy to pretty print when testing with cURL
* Docker (optional)
    * Only necessary if the are issues with any of the above dependencies

### Running

#### As Script

First install the dependencies. Note that the following commands assume Arch Linux.
```
$ pacman -S sqlite3 python3 python-pip jq
$ pip install -r requirements.txt
```

```
$ ./messenger_api.py
Launching Messenger API
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

#### Within Docker

I have included a simple Dockerfile which can be be used to make it easier to
run the project without installing the dependencies.

```
$ docker run --network host -e 127.0.0.1 -it $(docker build -q .)
Launching Messenger API
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

### Testing

#### As Script

If you have all of the dependencies installed, tests are run as a script.

```
$ ./tests.py
.............
----------------------------------------------------------------------
Ran 13 tests in 0.142s

OK
```

#### Within Docker

Alternatively, the tests can also be run within a docker container to manage
the dependencies.

```
$ docker run -it $(docker build -q .) ./tests.py
.............
----------------------------------------------------------------------
Ran 13 tests in 3.431s

OK
```

## Notes

### Interpretation of Prompt

> ...with a limit of 100 messages or all messages in last 30 days.

I took this very literally to say that there should be two filtering options
that the user may choose between (`all` and `limit`) when requesting messages
from the server. Messages older than 30 days are not returned regardless of filter.

The default limit is 100 if no filter is specified in the request.

### Data Older Than 30 Days

While the API limits the retrieved messages to the past 30 days, there is not
yet a background process which purges older messages from the system.
Currently, this data is simply inaccessible.

### Group Messaging

I have gone slightly beyond the minimum requirements of the project. Instead of
simply supporting messaging between two distinct users, I have added support
for group messaging. Groups are defined a list of the usernames within the
group. It would be the responsibility of the frontend to recognize that a
message is a group message and display it appropriately. To make it easier for
the frontend to determine which group a message should fall into, I have
guaranteed that usernames are always reported in alphabetical order when
returned in the `recipients` array.

In retrospect, the addition of multiple recipients made it harder to filter the
messages when retrieving them from the database. I was able to use the `LIKE`
command to search for a specific user, but this command is slow, especially on
large data sets. A more optimal SQL query would have been possible if I had
used named groups instead.

### Message IDs

I exposed message IDs in the API so that future APIs could be added which
allow messages to be edited or deleted.

## Next Steps

* Deploy with WSGI server such as Gunicorn instead of the Flask dev server.
* Migrate database from SQLite to PostgreSQL for more scalability.
* Integrate websockets so that messages are pushed to recipients immediately
  instead of requiring the frontend to poll for new messages.

## Acknowledgments

Invaluable Guide for using Flask with SQLite
* [Flask Sqlite3 Pattern](https://flask.palletsprojects.com/en/2.0.x/patterns/sqlite3/)

Helpful Blog Post on Unit Testing Flask with SQLite
* [In-memory SQLite database and Flask: a threading trap](https://gehrcke.de/2015/05/in-memory-sqlite-database-and-flask-a-threading-trap/)

Code Snippet to Hide Flask Development Server Warning
* [Prevent Flask Production Env Warning](https://gist.github.com/jerblack/735b9953ba1ab6234abb43174210d356)

API Design and Documentation Inspiration
* [Lithic](https://docs.lithic.com/)

Example Data Inspiration
* [Teenage Mutant Ninja Turtles Quotes](https://screenrant.com/teenage-mutant-ninja-turtles-original-trilogy-best-quotes/)
