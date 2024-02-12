from datetime import datetime, timedelta
import names
from pymongo import MongoClient
import random
from faker import Faker

fake = Faker()

client = MongoClient('mongodb://mongoadmin:secret@localhost:27017/')

db = client['service']

collection = db['service_data']

email_domains = ['example.com', 'mail.com', 'test.org', 'sample.net', 'demo.co']


def random_date(start, end):
    return start + timedelta(
        seconds=random.randint(0, int((end - start).total_seconds())))


def generate_data(num_records):
    start_date = datetime(2024, 2, 5, 0, 0, 0, 0)
    end_date = datetime(2024, 2, 12, 23, 59, 59, 59)
    email_domains = ['example.com', 'mail.com', 'test.org', 'sample.net', 'demo.co']

    for _ in range(num_records):
        name = names.get_full_name()
        email = '{}@{}'.format(name.lower().replace(' ', '.'), random.choice(email_domains))
        origin = {
            'count': random.randint(0, 10),
            'country': random.choice(['russia', 'usa', 'germany', 'france', 'china'])
        } if random.choice([True, False]) else None

        record = {
            'name': name,
            'email': email,
            'timestamp': random_date(start_date, end_date),
            'status': random.choice(['active', 'inactive', 'pending']),
            'score': random.uniform(0, 100),
            'comments': fake.text()
        }

        if random.choice([True, False]):
            record['age'] = random.randint(18, 99)

        if random.choice([True, False]):
            record['origin'] = origin

        if random.choice([True, False]):
            record['additional_info'] = {
                'preferences': random.choice(['sports', 'music', 'books', 'travel']),
                'membership': random.choice(['bronze', 'silver', 'gold', 'platinum'])
            }

        yield record


for data in generate_data(1000000):
    collection.insert_one(data)
count = collection.count_documents({})
print(count)
