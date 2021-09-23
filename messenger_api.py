#!/usr/bin/env python3

import os
import sys
import ast
import sqlite3
from datetime import datetime, timedelta
from flask import Flask, g, request, jsonify, Response
flask_app = Flask(__name__)

# Hide Flask Development Server Warning
# https://gist.github.com/jerblack/735b9953ba1ab6234abb43174210d356
cli = sys.modules['flask.cli']
cli.show_server_banner = lambda *x: None

# Check the environment for a different database name.
# This is used by the unittests to use a test-only database
DATABASE = os.environ.get('DATABASE', 'messages.db')

# Following SQLite Flask pattern outlined here:
# https://flask.palletsprojects.com/en/2.0.x/patterns/sqlite3/

# START DB Management Section
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def init_db():
    with flask_app.app_context():
        db = get_db()
        with flask_app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def query_db(query, args=(), one=False):
    db = get_db()
    cur = db.execute(query, args)
    rv = cur.fetchall()
    cur.close()
    db.commit()
    return (rv[0] if rv else None) if one else rv

@flask_app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
# END DB Management Section

# START Main App Section
@flask_app.route('/messages', methods=['POST'])
def send_message():
    '''Send a message from one user into the message database'''

    if not request.is_json:
        return jsonify({'error_message': 'Request does not have JSON content'}), 400

    required_fields = ['sender', 'recipients', 'text']
    missing_fields = list(required_fields - request.json.keys())
    if len(missing_fields) > 0:
        missing_fields.sort()
        return jsonify({'error_message': f'Missing required fields: {missing_fields}'}), 400

    sender = request.json['sender']
    recipients = request.json['recipients']
    text = request.json['text']

    if isinstance(recipients, list):
        # Sort the list alphabetically here so that we can make it easier on
        # the frontend to support group messages.
        recipients.sort()

        # Convert a list object to a string representation of a list:
        # From ['raphael', 'donatello', 'michelangelo']
        # To   "['raphael', 'donatello', 'michelangelo']"
        recipients = str(recipients)
    else:
        # This allows us to support non-list single recipient strings as lists of one.
        # From 'raphael'
        # To   '['raphael']'
        recipients = str([recipients])

    # Insert the new message into the database
    query_results = query_db('INSERT INTO messages(message,sender,recipients) VALUES (?, ?, ?) RETURNING id;', (text, sender, recipients))

    # Return the message's ID to the user
    return jsonify({'message_id': query_results[0][0]})

@flask_app.route('/messages', methods=['GET'])
def get_messages():
    '''Return a list of messages to the user'''

    if not request.is_json:
        return jsonify({'error_message': 'Request does not have JSON content'}), 400

    try:
        recipient = request.json['recipient']
    except KeyError:
        return jsonify({'error_message': 'Missing required recipient field'}), 400

    if 'limit' in request.json and 'all' in request.json:
        # The two options are mutually exclusive
        return jsonify({'error_message': '\'limit\' and \'all\' are mutually exclusive options'}), 400

    limit = request.json.get('limit', 100)
    all_requested = request.json.get('all', False)
    sender = request.json.get('sender', None)

    a_month_ago = datetime.now() - timedelta(30)

    # Here we prepare to use the SQLite LIKE query to match the name we care about, even in a list of other names.
    # Note that % is a wildcard that matches any number of characters
    recipient_query = f"%'{recipient}'%"

    # Make the LIKE query case-sensitive
    query_db('PRAGMA case_sensitive_like = true;')

    query_results = []
    if all_requested:
        if sender:
            query_results = query_db('SELECT * FROM messages WHERE sender = ? AND recipients LIKE ? AND timestamp > strftime(?);',
                                     (sender, recipient_query, a_month_ago))
        else:
            query_results = query_db('SELECT * FROM messages WHERE recipients LIKE ? AND timestamp > strftime(?);',
                                     (recipient_query, a_month_ago))
    else:
        if sender:
            query_results = query_db('SELECT * FROM messages WHERE sender = ? AND recipients LIKE ? AND timestamp > strftime(?) LIMIT ?;',
                                     (sender, recipient_query, a_month_ago, limit))
        else:
            query_results = query_db('SELECT * FROM messages WHERE recipients LIKE ? AND timestamp > strftime(?) LIMIT ?;',
                                     (recipient_query, a_month_ago, limit))

    # Process SQLites return into a list of dictionaries that we can easily JSONify
    processed_messages = []

    # According to the schema, the order of the columns is:
    # message, sender, recipients, id, timestamp
    for message in query_results:
        processed_messages.append({
            'sender'     : message[1],
            # Convert the recipients value from a string representation of a list back to a list
            'recipients' : ast.literal_eval(message[2]),
            'text'       : message[0],
            'message_id' : message[3],
        })

    return jsonify(processed_messages)

if __name__ == '__main__':
    print('Launching Messenger API')
    init_db();
    flask_app.run()
# END Main App Section
