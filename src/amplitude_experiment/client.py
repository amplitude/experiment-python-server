from .config import Config
from .version import __version__
from .variant import Variant
import http.client
import json


class Client:
    def __init__(self, api_key, config=None):
        self.api_key = api_key
        self.config = config or Config()

    def fetch(self, user):
        try:
            return self.fetch_internal(user)
        except:
            print("[Experiment] Failed to fetch variants")
            return {}

    def fetch_internal(self, user):
        try:
            return self.do_fetch(user, self.config.fetch_timeout_millis)
        except:
            print("Experiment] Fetch failed")
            return self.retry_fetch(user)

    def retry_fetch(self, user):
        if self.config.fetch_retries == 0:
            return {}
        pass

    def do_fetch(self, user, timeout_millis):
        user_context = self.add_context(user)
        headers = {
            'Authorization': f"Api-Key {self.api_key}",
            'Content-Type': 'application/json;charset=utf-8'
        }
        scheme, _, host = self.config.server_url.split('/', 3)
        Connection = http.client.HTTPConnection if scheme == 'http:' else http.client.HTTPSConnection
        conn = Connection(host)
        conn.connect()
        body = user_context.to_json().encode('utf8')
        conn.request('POST', '/sdk/vardata', body, headers)
        response = conn.getresponse()
        json_response = json.loads(response.read().decode("utf8"))
        variants = self.parse_json_variants(json_response)
        conn.close()
        return variants

    def add_context(self, user):
        user = user or {}
        user.library = user.library or f"experiment-python-server/{__version__}"
        return user

    def parse_json_variants(self, json_response):
        variants = {}
        for key, value in json_response.items():
            variant_value = ''
            if 'value' in value:
                variant_value = value['value']
            elif 'key' in value:
                variant_value = value['key']
            variants[key] = Variant(variant_value, value.get('payload'))
        return variants
