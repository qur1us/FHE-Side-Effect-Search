import json
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

from classes.database import Database
from classes.query import Query

IP_ADDRESS = '127.0.0.1'
PORT = 8000


class Server():
    def __init__(self) -> None:
        self.database = Database()
        self.database.generate_random()


    class ServerHTTPHandler(BaseHTTPRequestHandler):
        def __init__(self, request, client_address, server, database, *args, **kwargs):
            self.database = database
            super().__init__(request, client_address, server, *args, **kwargs)


        def do_POST(self):
            if self.path.startswith('/query'):
                self.post_handler()
            else:
                # Handle other paths as needed
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b'Not Found')


        def do_GET(self):
                if self.path.startswith('/query'):
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

            # Search the database using the query
            results = self.database.search(query)

            # Serialize the results
            serialized_result = json.dumps(results)

            # Set the response content
            self.wfile.write(serialized_result.encode('utf-8'))


        def get_handler(self):
            # Set the response status code
            self.send_response(200)

            # Set the response headers
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            # Parse the query parameters from the URL
            parsed_url = urllib.parse.urlparse(self.path)
            query_params = urllib.parse.parse_qs(parsed_url.query)

            if 'indexes' in query_params:
                try:
                    indexes = json.loads(query_params['indexes'][0])
                    restult: str = self.database.get_data(indexes)

                    self.wfile.write(restult.encode('utf-8'))
                except ValueError as e:
                    # If there's an error in parsing the JSON or processing the data
                    self.send_response(400)
                    self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            else:
                # If 'indexes' parameter is not present
                self.send_response(400)
                self.wfile.write(b'Missing required parameter: numbers')


    def start_server(self):
        server_address = (IP_ADDRESS, PORT)
        httpd = HTTPServer(server_address, lambda request, client_address, server: self.ServerHTTPHandler(request, client_address, server, self.database))

        print(f"Server listening on port {PORT}...")

        httpd.serve_forever()


if __name__ == "__main__":
    server: Server = Server()
    server.start_server()
