# Initial Prep

Because of my experience with using Python as a web-backend language, I chose
to use Python for this project. Javascript/Node would have been another good
choice, but I am less experienced with those tools.

I chose Flask as the web framework despite my more extensive experience with
Django because Flask is much simpler and would allow for much quicker
development of the simple JSON APIs necessary to complete the project. I
believe that Django is too full-featured and heavy weight for this simple
messaging API.

One of my concerns with developing this project using Python was that I wanted
to make sure that anyone who wanted to run this would be able to do so. So I
decided to include a simple Dockerfile which would make it possible to run the
application without installing any of the dependencies upon the host system.

I chose to use SQLite as the database backing this API. I had initially
considered using global memory which would get reset with each run of the app,
but I liked the idea of persisting messages even if the app were to be
restarted. For a production-destined app, I would have chosen Postgres over
SQLite.

# Planning the API

Before I begun to code up the app, I wanted to design the API so that the
interface to the frontend would be intuitive. I begun by writing
`API_REFERNECE.md` which is intended to be the documentation that I would
provide to the frontend developer who would be integrating with this API.

I decided to base my API design off of one of the best public API documentation
references that I know of: [Lithic](https://docs.lithic.com/). I had browsed their
API last year for research into a personal project that I had in mind, and I
remembered how much I liked the structure of their API and the organization of
their documentation.

# Writing Tests

Once I had the API mapped out, I moved on to writing some simple tests using
the `flask_unittest` module which I would eventually be able to use to validate
the application's functionality.

I created tests using the example data that I provided in the API Reference,
and added a few more to cover invalid API use and other corner cases.

# Writing the App Itself

Given that my planned API only had views, one `GET` and one `POST`, I created
two functions decorated with the appropriate flask routes.

## SQLite Integration

Integrating with SQLite proved tricky until I found a section of the Flask
reference manual which explained the concept of app context and provided
example code for integrating with the database.

## Send Message View

For the `send_message` view, I simply extracted the important data out of the
request's JSON attributes, performed some cleanup, then inserted the messages
into the database using a SQLite `INSERT` command.

## Get Message View

For the `get_message` view, first I extracted and validated the data provided in the
request's JSON attributes.

Because there are several different filters available in the request, I ended
up with several `SELECT` queries which are used to apply the appropriate
filters to the messages.

The group messaging feature made it more difficult to filter messages by
recipient, as the `recipients` field may contain multiple comma-separated
usernames. I used the `LIKE` filter to match individual names within a list of
recipients.

# Iteration

I tried at first to use PyInstaller to package this project, but the output
executible had issues with running on different machines. The system which I'm
running on is based on Arch Linux, therefore my packages are more recent than
typical. After a quick test on a Ubuntu docker image, I determined that
PyInstaller would not allow this project to run on some older systems.
PyInstaller doesn't package glibc into the executible, and some of the SQLite
commands I am using do not work on the older version available for Ubuntu.

As I went along writing the app, I wrote more tests which verified that the
validation errors that I was throwing were getting thrown correctly.
