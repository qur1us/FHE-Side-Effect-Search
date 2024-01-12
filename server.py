from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import sqlite3
import seal

from database import Database
from query import Query

IP_ADDRESS = '127.0.0.1'
PORT = 8000

class MyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Set the response status code
        self.send_response(200)

        # Set the response headers
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        # Read the POST data
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        # Parse and decode the POST data
        post_data = urllib.parse.unquote(post_data.decode('utf-8'))
        
        query: Query = Query.deserialize(post_data)
        
        database: Database = Database()
        database.generate_random()

        database.search(query)

        # Set the response content
        response_content = f"Hello, custom Python web server (POST)!\nReceived data: {post_data}"
        self.wfile.write(response_content.encode('utf-8'))


def start_server():
    server_address = (IP_ADDRESS, PORT)
    httpd = HTTPServer(server_address, MyHandler)

    print(f"Server listening on port {PORT}...")

    httpd.serve_forever()


if __name__ == "__main__":
    start_server()
