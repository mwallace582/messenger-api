# API Reference Guide

## Send Message

Sends a text message from one user to one or several other users.

```
POST http:/127.0.0.1/messages
```

### Request

| Field        | Type             | Description                          |
| -----        | ----             | -----------                          |
| `sender`     | String           | Sender of the message                |
| `recipients` | Array of strings | Recipient(s) of the message          |
| `text`       | String           | The text body of the message to send |

#### Example

```
curl http:/127.0.0.1:5000/messages \
  -X POST --silent \
  -H "Content-Type: application/json" \
  -d '{"sender":"leonardo","text":"Cowabunga!","recipients":["raphael","donatello","michelangelo"]}' | jq
```

### Response

| Field                      | Type    | Description                                     |
| -----                      | ----    | -----------                                     |
| `message_id`               | Integer | Unique identifier for the message               |
| `error_message` (optional) | String  | Detailed error message (only returned on error) |

#### Example

```
  {
    "message_id" : 523652
  }
```

## Get Messages

Retrieves an array of text messages which have been sent to a given recipient.

```
GET http:/127.0.0.1/messages
```

### Request

| Field               | Type    | Description                                               |
| -----               | ----    | -----------                                               |
| `recipient`         | String  | The user for which to retrieve messages                   |
| `sender` (optional) | String  | Filter retrieved messages by a specific sender            |
| `limit` (optional)  | Integer | Maximum number of messages to retrieve (default 100)      |
| `all` (optional)    | Boolean | Retrieve all messages in the last 30 days (default False) |

_Note_ `all` and `limit` are mutually exclusive options.

#### Example

```
curl http:/127.0.0.1:5000/messages \
  -X GET --silent \
  -H "Content-Type: application/json" \
  -d '{"recipient":"raphael","all":true}' | jq
```

### Response

| Field                      | Type             | Description                                     |
| -----                      | ----             | -----------                                     |
| `sender`                   | String           | Sender of the message                           |
| `recipients`               | Array of strings | Recipient(s) of the message                     |
| `text`                     | String           | The text body of the message                    |
| `message_id`               | Integer          | Unique identifier for the message               |
| `error_message` (optional) | String           | Detailed error message (only returned on error) |

_Note_ `recipients` are guaranteed to be ordered alphabetically.

#### Example

```
  [
    {
      "sender"     : "leonardo",
      "text"       : "Cowabunga!",
      "recipients" : [
        "donatello",
        "michelangelo"
        "raphael",
      ],
      "message_id" : 523652
    },
    {
      "sender"     : "michelangelo",
      "text"       : "Forgiveness Is Divine, But Never Pay Full Price For A Late Pizza",
      "recipients" : [
        "raphael"
      ],
      "message_id" : 523653
    },
    {
      "sender"     : "michelangelo",
      "text"       : "I Love Being A Turtle",
      "recipients" : [
        "donatello",
        "michelangelo",
        "raphael",
        "splinter"
      ],
      "message_id" : 523654
    }
  ]
```

## Notes

* Usernames are case-sensitive
* The use of `jq` is optional, it simply makes for prettier printing of JSON data
