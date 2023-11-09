import http.server
import socketserver
import re
import json
from jinja2 import Template


class Product:
    def __init__(self, name, author, price, description):
        self.name = name
        self.author = author
        self.price = price
        self.description = description


with open('products.json', 'r') as file:
    products_data = json.load(file)

products = [Product(**data) for data in products_data]

# Define HTML templates using Jinja2
home_page_template = Template("""
<h1>This is our home page</h1>
<p>Check out our <a href='/about'>about page</a></p>
<p>Check out your <a href='/cart'>cart</a></p>
<h2>Products</h2>
{% for product in products %}
    <p><a href='/product/{{ loop.index }}'>{{ product.name }}</a> - Price: ${{ product.price }} <a href='/add_to_cart/{{ loop.index }}'>Add to Cart</a></p>
{% endfor %}
""")

about_page_template = Template("""
<h1>About our store:</h1>
<a href="/">Go back</a>
<p>Here are the best Romania hits</p>
""")

cart_page_template = Template("""
<h1>Your Cart</h1>
<a href="/">Go back</a>
{% if cart.items %}
    <ul>
    {% for item in cart.items %}
        <li>{{ item.product.name }} - Price: ${{ item.product.price }} <a href='/remove_from_cart/{{ loop.index }}'>Remove</a></li>
    {% endfor %}
    </ul>
    <p>Total Cost: ${{ cart.get_total_cost() }}</p>
{% else %}
    <p>Your cart is empty</p>
{% endif %}
""")

product_template = Template("""
<h1>{{ product.name }}</h1>
<a href="/">Go back</a>
<p>Author: {{ product.author }}</p>
<p>Price: ${{ product.price }}</p>
<p>Description: {{ product.description }}</p>
""")


# Create a Cart class
class CartItem:
    def __init__(self, product):
        self.product = product


class Cart:
    def __init__(self):
        self.items = []

    def add_item(self, item):
        self.items.append(item)

    def remove_item(self, index):
        if 0 <= index < len(self.items):
            del self.items[index]

    def get_total_cost(self):
        print(self.items)
        return sum(item.product.price for item in self.items)


# Initialize the cart
cart = Cart()


class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(home_page_template.render(products=products).encode())
        elif self.path == '/about':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(about_page_template.render().encode())
        elif self.path == '/cart':
            self.send_response(200)
            self.end_headers()
            self.wfile.write(cart_page_template.render(cart=cart).encode())
        elif re.match(r'/product/\d+', self.path):
            product_id = int(self.path.split('/')[-1])
            if 0 < product_id <= len(products):
                product = products[product_id - 1]
                self.send_response(200)
                self.end_headers()
                self.wfile.write(product_template.render(product=product).encode())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write("Product not found".encode())
        elif re.match(r'/add_to_cart/\d+', self.path):
            product_id = int(self.path.split('/')[-1])
            if 0 < product_id <= len(products):
                product = products[product_id - 1]
                cart.add_item(CartItem(product))
                self.send_response(302)
                self.send_header('Location', '/cart')
                self.end_headers()
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write("Product not found".encode())
        elif re.match(r'/remove_from_cart/\d+', self.path):
            item_index = int(self.path.split('/')[-1])
            cart.remove_item(item_index - 1)
            self.send_response(302)
            self.send_header('Location', '/cart')
            self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write("404 Page not found".encode())


with socketserver.TCPServer(("", 8081), MyHandler) as httpd:
    print("Server started on port 8081")
    httpd.serve_forever()
