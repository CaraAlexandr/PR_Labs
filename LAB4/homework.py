import socket

# Constants
HOST = "localhost"
PORT = 8081  # Updated port
BUFFER_SIZE = 4096


def fetch_page_content(path):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))

        request = f"GET {path} HTTP/1.1\r\nHost: {HOST}\r\nConnection: close\r\n\r\n"
        s.sendall(request.encode())

        chunks = []
        while True:
            chunk = s.recv(BUFFER_SIZE)
            if not chunk:
                break
            chunks.append(chunk)

        content = b"".join(chunks).decode("utf-8")
        # Extract the body of the response
        body = content.split("\r\n\r\n", 1)[1]
        return body


def extract_product_links(content):
    return [line.split('\'')[1] for line in content.splitlines() if "/product/" in line]


def extract_product_details(content):
    lines = content.splitlines()
    name = next(line for line in lines if '<h1>' in line).replace('<h1>', '').replace('</h1>', '').strip()
    author = next(line for line in lines if 'Author:' in line).split(': ')[1].replace('</p>', '').strip()
    price = float(next(line for line in lines if 'Price:' in line).split('$')[1].replace('</p>', '').strip())
    description = next(line for line in lines if 'Description:' in line).split(': ')[1].replace('</p>', '').strip()
    return {
        "name": name,
        "author": author,
        "price": price,
        "description": description
    }


# Storing pages content and products
pages_content = {}
products = []

# Fetch and save the home page content
home_page_content = fetch_page_content("/")
pages_content["/"] = home_page_content
product_links = extract_product_links(home_page_content)

# Fetch and save each page's content and extract product details if it's a product page
for path in product_links:
    page_content = fetch_page_content(path)
    pages_content[path] = page_content
    if "/product/" in path:
        product_details = extract_product_details(page_content)
        products.append(product_details)

print("Pages Content:")
for path, content in pages_content.items():
    print(f"Path: {path}\n{content}\n\n{'-' * 50}\n")

print("Products Details:")
for product in products:
    print(product)
