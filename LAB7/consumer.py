import pika
import psycopg2
import requests
from bs4 import BeautifulSoup
import json
import threading


def extract_info(URL):
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, "html.parser")
    dict_result = {}

    title = soup.find('h1', itemprop='name')
    if title:
        dict_result['Title'] = title.text

    desc = soup.find('div', itemprop='description')
    if desc:
        dict_result['Description'] = desc.text

    price = soup.find(
        'span', class_='adPage__content__price-feature__prices__price__value')
    currency = soup.find('span', itemprop='priceCurrency')
    if price:
        if price.text.find('negociabil') != -1:
            dict_result['Price'] = price.text
        else:
            dict_result['Price'] = price.text + ' ' + currency.get('content')

    country = soup.find('meta', itemprop='addressCountry')
    locality = soup.find('meta', itemprop='addressLocality')
    if country and locality:
        dict_result['Location'] = locality.get(
            'content') + ', ' + country.get('content')

    ad_info = {}
    views = soup.find('div', class_='adPage__aside__stats__views')
    if views:
        ad_info['Views'] = views.text
    date = soup.find('div', class_='adPage__aside__stats__date')
    if date:
        ad_info['Update Date'] = date.text
    ad_type = soup.find('div', class_='adPage__aside__stats__type')
    if ad_type:
        ad_info['Ad Type'] = ad_type.text
    owner_username = soup.find(
        'a', class_='adPage__aside__stats__owner__login buyer_experiment  has-reviews')
    if owner_username:
        ad_info['Owner Username'] = owner_username.text
    dict_result['Ad Info'] = ad_info

    general_div = soup.find('div', class_='adPage__content__features__col')
    general_dict = {}
    li_elements = general_div.find_all('li')
    for li in li_elements:
        key_element = li.find('span', class_='adPage__content__features__key')
        value_element = li.find(
            'span', class_='adPage__content__features__value')
        if key_element and value_element:
            key = key_element.text.strip()
            value = value_element.text.strip()
            general_dict[key] = value
    dict_result['General Info'] = general_dict

    features_div = soup.find(
        'div', class_='adPage__content__features__col grid_7 suffix_1')
    features_dict = {}
    li_elements = features_div.find_all('li')
    for li in li_elements:
        key_element = li.find('span', class_='adPage__content__features__key')
        value_element = li.find(
            'span', class_='adPage__content__features__value')
        if key_element and value_element:
            key = key_element.text.strip()
            value = value_element.text.strip()
            features_dict[key] = value
    dict_result['Features'] = features_dict

    print(json.dumps(dict_result, indent=4, ensure_ascii=False))

    return dict_result
def callback(ch, method, properties, body):
    url = body.decode()
    print(f"Received URL: {url}")
    product_info = extract_info(url)
    try:
        # Insert data into PostgreSQL database
        with psycopg2.connect(
            dbname="scooters",
            user="admin",
            password="adminpass",
            host="db"
        ) as conn:
            with conn.cursor() as cur:
                # Define your PostgreSQL INSERT statement here
                insert_query = """
                INSERT INTO product_details (title, description, price, location, ad_info, general_info, features)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cur.execute(insert_query, (
                    product_info.get('Title'),
                    product_info.get('Description'),
                    product_info.get('Price'),
                    product_info.get('Location'),
                    json.dumps(product_info.get('Ad Info')),
                    json.dumps(product_info.get('General Info')),
                    json.dumps(product_info.get('Features'))
                ))
            conn.commit()
        print(f"Product info from {url} saved to database.")
    except Exception as e:
        print(f"Error saving to database: {str(e)}")
    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)

def start_consumer():
    rabbitmq_host = 'rabbitmq'
    queue_name = 'url_queue'
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue_name, on_message_callback=callback)
    print('Consumer started. To exit press CTRL+C')
    channel.start_consuming()

# Number of consumer threads to run
num_consumers = 5  # Set this to the number of concurrent consumers you want

# Starting multiple consumer threads
for i in range(num_consumers):
    consumer_thread = threading.Thread(target=start_consumer)
    consumer_thread.start()
    print(f"Started consumer thread {i+1}")

print(f"{num_consumers} consumer threads have been started.")