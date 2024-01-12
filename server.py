from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse

from classes.database import Database
from classes.query import Query

IP_ADDRESS = '127.0.0.1'
PORT = 8000

class MyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/query':
            self.post_handler()
        else:
            # Handle other paths as needed
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')


    def do_GET(self):
            if self.path == '/query':
                self.get_handler()
            else:
                # Handle other paths as needed
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'Not Found')


    def post_handler(self):
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

        # Deserialize the query
        query = Query.deserialize(post_data)

        # Create a Database instance and generate random data
        database = Database()
        database.generate_random()

        # Search the database using the query
        results = database.search(query)

        # Serialize the results
        serialized_result = ','.join(results)

        # Set the response content
        self.wfile.write(serialized_result.encode('utf-8'))


    def get_handler(self):
        pass
        # TODO


def start_server():
    server_address = (IP_ADDRESS, PORT)
    httpd = HTTPServer(server_address, MyHandler)

    print(f"Server listening on port {PORT}...")

    httpd.serve_forever()


if __name__ == "__main__":
    start_server()
