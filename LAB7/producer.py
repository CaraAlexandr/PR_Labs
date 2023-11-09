import pika
import requests
from bs4 import BeautifulSoup
import time


def connect_to_rabbitmq(retries=5, delay=5, host='rabbitmq', port=5672):
    last_exception = None
    for attempt in range(retries):
        try:
            return pika.BlockingConnection(pika.ConnectionParameters(host=host, port=port))
        except pika.exceptions.AMQPConnectionError as error:
            print(f"Attempt {attempt + 1} failed: {error}")
            last_exception = error
            time.sleep(delay)
    raise last_exception  # Raise the last exception if all retries failed


# Set up RabbitMQ connection and declare the queue
rabbitmq_host = 'rabbitmq'  # Ensure this is the correct hostname reachable from the script
queue_name = 'url_queue'
connection = connect_to_rabbitmq()  # Use the connection function with retry mechanism
channel = connection.channel()
channel.queue_declare(queue=queue_name, durable=True)


def recursive(max_iterations, current_iteration, url_array, data, channel, queue_name):
    if current_iteration >= len(url_array) or current_iteration >= max_iterations:
        print(f"Total URLs collected: {len(data)}")
        return

    url = url_array[current_iteration]
    try:
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")

        # Collect and enqueue product URLs
        for link in soup.find_all('a', href=True, class_='js-item-ad'):
            full_link = f"https://999.md{link.get('href')}"
            if full_link not in data:
                data.add(full_link)  # Use a set to prevent duplicates
                channel.basic_publish(exchange='', routing_key=queue_name, body=full_link)
                print(f"Sent URL to queue: {full_link}")

        # Find new pages to crawl
        for page in soup.select('nav.paginator > ul > li > a'):
            new_url = f"https://999.md{page.get('href')}"
            if new_url not in url_array:
                url_array.append(new_url)

        # Recursive call for the next page
        recursive(max_iterations, current_iteration + 1, url_array, data, channel, queue_name)

    except requests.RequestException as e:
        print(f"Failed to fetch URL {url}: {str(e)}")


# Initialize the URL collection and start the recursive crawling
seen_data = set()
starting_url = "https://999.md/ru/list/animals-and-plants/the-birds"
recursive(100000000, 0, [starting_url], seen_data, channel, queue_name)

# Close the RabbitMQ connection after the crawling is done
connection.close()
