import requests
from bs4 import BeautifulSoup
import json


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


URL = "https://999.md/ro/84307033"
extract_info(URL)