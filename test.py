import json

from confluent_kafka import Producer


CONSUMER_TOPIC = "assembling_message_topic"

p = Producer({'bootstrap.servers': 'localhost:29092'})

def delivery_report(err, msg):
    """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
    if err is not None:
        print('Message delivery failed: {}'.format(err))
    else:
        print('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))


some_data_source = [
    {
        'sender': 'sender',
        'timestamp': 12412412,
        'segment_number': 2,
        "message": " маму",
        "had_error": True,
    },
    {
        'sender': 'sender',
        'timestamp': 12412412,
        'segment_number': 1,
        "message": "Я люблю",
        "had_error": False,
    }
]

for data in some_data_source:
    # Trigger any available delivery report callbacks from previous produce() calls
    p.poll(0)

    # Asynchronously produce a message. The delivery report callback will
    # be triggered from the call to poll() above, or flush() below, when the
    # message has been successfully delivered or failed permanently.
    json_data = json.dumps(data)
    p.produce(CONSUMER_TOPIC, json_data.encode('utf-8'), callback=delivery_report)

# Wait for any outstanding messages to be delivered and delivery report
# callbacks to be triggered.
p.flush()