from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json
import os
import cgi


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/file':
            self.handle_file_metadata()
        elif self.path == '/url':
            self.handle_parse_url()
        else:
            self.send_error(404, "Endpoint not found.")

    def handle_file_metadata(self):
        ctype, pdict = cgi.parse_header(self.headers['content-type'])
        pdict['boundary'] = bytes(pdict['boundary'], "utf-8")
        content_length = int(self.headers['Content-Length'])
        pdict['CONTENT-LENGTH'] = content_length
        if ctype == 'multipart/form-data':
            fields = cgi.parse_multipart(self.rfile, pdict)
            file_content = fields.get('file')[0].decode()
            search_string = fields.get('string')[0]
            response_data = {
                'length_of_text': len(file_content),
                'amount_of_alphanumeric': sum(c.isalnum() for c in file_content),
                'occurrences_of_string': file_content.lower().count(search_string.lower())
            }
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())
        else:
            self.send_error(400, "Invalid form data")

    def handle_parse_url(self):
        length = int(self.headers['content-length'])
        body = self.rfile.read(length).decode()
        parsed_url = urlparse(body)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            self.send_error(400, "Invalid URL provided.")
            return
        path_steps = parsed_url.path.strip("/").split("/") if parsed_url.path else []
        query_params = parse_qs(parsed_url.query)
        response_data = {
            'protocol': parsed_url.scheme,
            'domain': parsed_url.netloc,
            'path_steps': path_steps,
            'query_parameters': query_params
        }
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode())

    def do_GET(self):
        if self.path.startswith('/images/'):
            self.handle_image_request()
        elif self.path == '/':
            self.handle_docs()
        else:
            self.send_error(404, "Endpoint not found.")

    def handle_image_request(self):
        filepath = os.path.join(os.getcwd(), self.path[1:])
        if os.path.isfile(filepath) and filepath.endswith(('.png', '.jpeg', '.jpg')):
            with open(filepath, 'rb') as file:
                self.send_response(200)
                self.send_header('Content-type', 'image/png')
                self.end_headers()
                self.wfile.write(file.read())
        else:
            self.send_error(404, "Image not found.")

    def handle_docs(self):
        docs = {
            '/file': 'POST length of whole text, amount of alphanumeric symbols, and number of occurrences of that string in the text, not case sensitive.',
            '/url': 'POST It gets any valid url, parses it and provides a human-readable information about it.',
            '/images/{filename}': 'GET returns a pic',
            '/': 'GET endpoint for documentation '
        }
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(docs).encode())

def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler):
    server_address = ('', 8000)
    httpd = server_class(server_address, handler_class)
    print("Server started at http://localhost:8000")
    httpd.serve_forever()

if __name__ == '__main__':
    run()
