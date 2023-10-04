import requests
from bs4 import BeautifulSoup

BASE_URL = 'https://999.md/ru/list/audio-video-photo/headphones'


def fetch_html(url):
    response = requests.get(url)
    return response.text


def extract_pagination_links(url):
    html = fetch_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    pagination_links = soup.select('nav.paginator > ul > li > a')
    return pagination_links


def extract_item_links(url):
    html = fetch_html(url)
    soup = BeautifulSoup(html, 'html.parser')
    item_links = soup.select('a.js-item-ad')

    filtered_links = []
    for item_link in item_links:
        if 'booster' not in item_link['href']:
            new_link = 'https://999.md' + item_link['href']
            if new_link not in filtered_links:
                filtered_links.append(new_link)

    return filtered_links


def get_all_item_links(start_url):
    pagination_links = extract_pagination_links(start_url)

    all_item_links = []
    for pagination_link in pagination_links:
        item_links = extract_item_links('https://999.md' + pagination_link['href'])
        all_item_links.extend(item_links)

    return all_item_links


if __name__ == "__main__":
    all_links = get_all_item_links(BASE_URL)
    print(all_links)
    print(len(all_links))
