#!/usr/bin/env python3

import os
import unittest
import flask_unittest
import flask.globals
from datetime import datetime, timedelta

# Ideally I would swap out the real database with an in-memory SQLite database
# for testing, however there are threading issues with using in-memory
# databases for Flask testing.
# https://gehrcke.de/2015/05/in-memory-sqlite-database-and-flask-a-threading-trap/
os.environ['DATABASE'] = '/tmp/messenger_api_testing.db'

from messenger_api import flask_app, init_db, query_db

class MessengerApiTest(flask_unittest.ClientTestCase):
    app = flask_app

    def setUp(self, client):
        # Perform set up before each test
        init_db()

    def tearDown(self, client):
        # Perform tear down after each test
        os.remove(os.environ['DATABASE'])

    # BEGIN POST Tests
    def test_bad_sends(self, client):
        '''Send a bad request to the messages route'''
        rv = client.post('/messages', json={
            'bad_data' : 'bad_data',
        })
        self.assertEqual(rv.status, '400 BAD REQUEST')
        self.assertEqual(rv.json['error_message'], 'Missing required fields: [\'recipients\', \'sender\', \'text\']')

    def test_post_bad_route(self, client):
        '''Try to POST to an invalid route'''
        rv = client.post('/bad_route', json={
            'bad_data' : 'bad_data',
        })
        self.assertEqual(rv.status, '404 NOT FOUND')

    def test_send_to_single(self, client):
        '''Send a message to a single user'''
        rv = client.post('/messages', json={
            'sender' : 'michelangelo',
            'text' : 'Forgiveness Is Divine, But Never Pay Full Price For A Late Pizza',
            'recipients' : 'raphael'
        })
        self.assertTrue(rv.is_json)
        self.assertEqual(rv.json['message_id'], 1)

    def test_send_to_single_as_list(self, client):
        '''Send a message to a single user as a list of one entry'''
        rv = client.post('/messages', json={
            'sender' : 'michelangelo',
            'text' : 'Forgiveness Is Divine, But Never Pay Full Price For A Late Pizza',
            'recipients' : ['raphael']
        })
        self.assertTrue(rv.is_json)
        self.assertEqual(rv.json['message_id'], 1)

    def test_send_to_group(self, client):
        '''Send a message to a group of users'''
        rv = client.post('/messages', json={
            'sender' : 'leonardo',
            'text' : 'Cowabunga!',
            'recipients' : ["raphael","donatello","michelangelo"]
        })
        self.assertTrue(rv.is_json)
        self.assertEqual(rv.json['message_id'], 1)

    def test_incomplete_send_data(self, client):
        '''Send a number of incomplete requests to the messages route'''
        # Required 'recipients' field is missing
        rv = client.post('/messages', json={
            'sender' : 'michelangelo',
            'text' : 'Cowabunga!',
        })
        self.assertEqual(rv.status, '400 BAD REQUEST')
        self.assertEqual(rv.json['error_message'], 'Missing required fields: [\'recipients\']')

        # Required 'text' field is missing
        rv = client.post('/messages', json={
            'sender' : 'michelangelo',
            'recipients' : 'leonardo',
        })
        self.assertEqual(rv.status, '400 BAD REQUEST')
        self.assertEqual(rv.json['error_message'], 'Missing required fields: [\'text\']')

        # Required 'sender' field is missing
        rv = client.post('/messages', json={
            'text' : 'Cowabunga!',
            'recipients' : 'leonardo',
        })
        self.assertEqual(rv.status, '400 BAD REQUEST')
        self.assertEqual(rv.json['error_message'], 'Missing required fields: [\'sender\']')
    # END POST Tests

    # BEGIN GET Tests
    def test_get_bad_route(self, client):
        '''Try to GET from an invalid route'''
        rv = client.get('/bad_route', json={
            'bad_data' : 'bad_data',
        })
        self.assertEqual(rv.status, '404 NOT FOUND')

    def test_bad_get(self, client):
        '''Try to GET with invalid fields'''
        rv = client.get('/messages', json={
            'bad_data' : 'bad_data',
        })
        self.assertEqual(rv.status, '400 BAD REQUEST')
        self.assertEqual(rv.json['error_message'], 'Missing required recipient field')

    def test_get_no_recipient(self, client):
        '''Try to retrieve messages without a recipient specified'''
        rv = client.get('/messages', json={})
        self.assertEqual(rv.status, '400 BAD REQUEST')
        self.assertEqual(rv.json['error_message'], 'Missing required recipient field')

    def test_getting_messages(self, client):
        '''Try to retrieve messages in several different ways when there are several'''

        # Populate the database with several sent messages
        message_ids = []
        rv = client.post('/messages', json={
            'sender' : 'leonardo',
            'text' : 'Cowabunga!',
            'recipients' : ["raphael","donatello","michelangelo"]
        })
        message_ids.append(rv.json['message_id'])

        rv = client.post('/messages', json={
            'sender' : 'michelangelo',
            'text' : 'Forgiveness Is Divine, But Never Pay Full Price For A Late Pizza',
            'recipients' : ['raphael']
        })
        message_ids.append(rv.json['message_id'])

        # This message is not to raphael and will not be returned
        rv = client.post('/messages', json={
            'sender' : 'splinter',
            'text' : 'When You Die It Will Be Without Honor',
            'recipients' : ['shredder']
        })
        message_ids.append(rv.json['message_id'])

        # This message is older than 30 days and will not be returned by any query
        # Inserting directly, as there's no mechanism to submit old messages via the API
        old_timestamp = datetime.now() - timedelta(31)
        ret = query_db('INSERT INTO messages(message,sender,recipients,timestamp) VALUES (?, ?, ?, ?) returning id;',
                 ('old_message', 'nobody', "['raphael']", old_timestamp))
        message_ids.append(ret[0][0])

        # Insert a large volume of messages to test the default limit
        for i in range(0, 100):
            rv = client.post('/messages', json={
                'sender' : "April O'Neil",
                'text' : f'Hello #{i+1}',
                'recipients' : ['raphael']
            })
            message_ids.append(rv.json['message_id'])

        #  ----- Done populating message database, time to test ---- #

        # Query for all raphael's messages sent by anyone
        rv = client.get('/messages', json={
            'recipient' : 'raphael',
            'all' : True,
        })

        self.assertTrue(rv.is_json)
        # 100 from April, 1 from leonardo, 1 from michelangelo
        self.assertEqual(len(rv.json), 102)

        self.assertEqual(rv.json[0]['message_id'], message_ids[0])
        self.assertEqual(rv.json[0]['text'], 'Cowabunga!')
        self.assertEqual(rv.json[0]['sender'], 'leonardo')
        self.assertEqual(rv.json[0]['recipients'], ['donatello', 'michelangelo', 'raphael'])

        self.assertEqual(rv.json[1]['message_id'], message_ids[1])
        self.assertEqual(rv.json[1]['text'], 'Forgiveness Is Divine, But Never Pay Full Price For A Late Pizza')
        self.assertEqual(rv.json[1]['sender'], 'michelangelo')
        self.assertEqual(rv.json[1]['recipients'], ['raphael'])

        self.assertEqual(rv.json[2]['message_id'], message_ids[4])
        self.assertEqual(rv.json[2]['text'], 'Hello #1')
        self.assertEqual(rv.json[2]['sender'], "April O'Neil")
        self.assertEqual(rv.json[2]['recipients'], ['raphael'])
        #...No use in validating all 100 messages here

        # Query for all raphael's messages sent by leonardo
        rv = client.get('/messages', json={
            'recipient' : 'raphael',
            'sender' : 'leonardo',
            'all' : True,
        })

        self.assertTrue(rv.is_json)
        self.assertEqual(len(rv.json), 1)

        self.assertEqual(rv.json[0]['message_id'], message_ids[0])
        self.assertEqual(rv.json[0]['text'], 'Cowabunga!')
        self.assertEqual(rv.json[0]['sender'], 'leonardo')
        self.assertEqual(rv.json[0]['recipients'], ['donatello', 'michelangelo', 'raphael'])

        # Query for only one of raphael's messages
        rv = client.get('/messages', json={
            'recipient' : 'raphael',
            'limit' : 1,
        })

        self.assertTrue(rv.is_json)
        self.assertEqual(len(rv.json), 1)

        self.assertEqual(rv.json[0]['message_id'], message_ids[0])
        self.assertEqual(rv.json[0]['text'], 'Cowabunga!')
        self.assertEqual(rv.json[0]['sender'], 'leonardo')
        self.assertEqual(rv.json[0]['recipients'], ['donatello', 'michelangelo', 'raphael'])

        # Query for only two of raphael's messages, with sender limit filters
        rv = client.get('/messages', json={
            'recipient' : 'raphael',
            'sender' : "April O'Neil",
            'limit' : 1,
        })

        self.assertTrue(rv.is_json)
        self.assertEqual(len(rv.json), 1)

        self.assertEqual(rv.json[0]['message_id'], message_ids[4])
        self.assertEqual(rv.json[0]['text'], 'Hello #1')
        self.assertEqual(rv.json[0]['sender'], "April O'Neil")
        self.assertEqual(rv.json[0]['recipients'], ['raphael'])

        # Default query for raphael's messages
        rv = client.get('/messages', json={
            'recipient' : 'raphael',
        })

        self.assertTrue(rv.is_json)
        # 100 from April, 1 from leonardo, 1 from michelangelo, limited to 100 by default
        self.assertEqual(len(rv.json), 100)

        self.assertEqual(rv.json[0]['message_id'], message_ids[0])
        self.assertEqual(rv.json[0]['text'], 'Cowabunga!')
        self.assertEqual(rv.json[0]['sender'], 'leonardo')
        self.assertEqual(rv.json[0]['recipients'], ['donatello', 'michelangelo', 'raphael'])

        self.assertEqual(rv.json[1]['message_id'], message_ids[1])
        self.assertEqual(rv.json[1]['text'], 'Forgiveness Is Divine, But Never Pay Full Price For A Late Pizza')
        self.assertEqual(rv.json[1]['sender'], 'michelangelo')
        self.assertEqual(rv.json[1]['recipients'], ['raphael'])

        self.assertEqual(rv.json[2]['message_id'], message_ids[4])
        self.assertEqual(rv.json[2]['text'], 'Hello #1')
        self.assertEqual(rv.json[2]['sender'], "April O'Neil")
        self.assertEqual(rv.json[2]['recipients'], ['raphael'])
        #...No use in validating all 100 messages here

    def test_get_no_messages(self, client):
        '''Try to retrieve messages when there are none'''
        rv = client.get('/messages', json={
            'recipient' : 'leonardo',
        })
        self.assertTrue(rv.is_json)
        self.assertEqual(len(rv.json), 0)

    def test_get_two_mutually_exclusive_options(self, client):
        '''Try to filter messages using two mutually exclusive options'''
        rv = client.get('/messages', json={
            'recipient' : 'leonardo',
            'limit' : '10',
            'all' : True,
        })
        self.assertEqual(rv.status, '400 BAD REQUEST')
        self.assertEqual(rv.json['error_message'], '\'limit\' and \'all\' are mutually exclusive options')

    def test_case_sensitivity(self, client):
        '''Test to make sure that usernames are case sensitive'''
        message_ids = []
        rv = client.post('/messages', json={
            'sender' : 'LEONARDO',
            'text' : 'Testing upper case',
            'recipients' : ["RAPHAEL"]
        })
        message_ids.append(rv.json['message_id'])

        rv = client.post('/messages', json={
            'sender' : 'leonardo',
            'text' : 'Testing lower case',
            'recipients' : ["raphael"]
        })
        message_ids.append(rv.json['message_id'])

        # Test to retrieve messages sent to the lower case 'raphael'
        rv = client.get('/messages', json={
            'recipient' : 'raphael',
        })
        self.assertTrue(rv.is_json)
        # Should only return the message to lower case 'raphael'
        self.assertEqual(len(rv.json), 1)

        self.assertEqual(rv.json[0]['message_id'], message_ids[1])
        self.assertEqual(rv.json[0]['text'], 'Testing lower case')
        self.assertEqual(rv.json[0]['sender'], 'leonardo')
        self.assertEqual(rv.json[0]['recipients'], ['raphael'])

        # Test to retrieve messages sent to the upper case 'RAPHAEL'
        rv = client.get('/messages', json={
            'recipient' : 'RAPHAEL',
        })
        self.assertTrue(rv.is_json)
        # Should only return the message to upper case 'RAPHAEL'
        self.assertEqual(len(rv.json), 1)

        self.assertEqual(rv.json[0]['message_id'], message_ids[0])
        self.assertEqual(rv.json[0]['text'], 'Testing upper case')
        self.assertEqual(rv.json[0]['sender'], 'LEONARDO')
        self.assertEqual(rv.json[0]['recipients'], ['RAPHAEL'])

        # Test that the 'sender' field is also case-sensitive
        rv = client.get('/messages', json={
            'recipient' : 'raphael',
            'sender' : 'LEONARDO',
        })
        self.assertTrue(rv.is_json)
        # Upper case 'LEONARDO' never sent a message to 'raphael'
        self.assertEqual(len(rv.json), 0)
    # END GET Tests

if __name__ == '__main__':
    unittest.main()
