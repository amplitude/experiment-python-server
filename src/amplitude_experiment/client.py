import threading
import time
from time import sleep
from .config import Config
from .version import __version__
from .variant import Variant
from .user import User
import http.client
import json
import logging


class Client:
    """Main client for fetching variant data."""

    def __init__(self, api_key, config=None):
        """
        Creates a new Experiment Client instance.
            Parameters:
                api_key (str): The environment API Key
                config (Config): Config Object

            Returns:
                Experiment Client instance.
        """
        if not api_key:
            raise ValueError("Experiment API key is empty")
        self.api_key = api_key
        self.config = config or Config()
        self.logger = logging.getLogger("Amplitude")
        self.logger.addHandler(logging.StreamHandler())
        if self.config.debug:
            self.logger.setLevel(logging.DEBUG)

    def fetch(self, user: User):
        """
        Fetch all variants for a user synchronous.This method will automatically retry if configured.
            Parameters:
                user (User): The Experiment User

            Returns:
                Variants Dictionary.
        """
        try:
            return self.__fetch_internal(user)
        except Exception as e:
            self.logger.error(f"[Experiment] Failed to fetch variants: {e}")
            return {}

    def fetch_async(self, user: User, callback=None):
        """
        Fetch all variants for a user asynchronous. Will trigger callback after fetch complete
            Parameters:
                user (User): The Experiment User
                callback (callable): Callback function, takes user and variants arguments
        """
        thread = threading.Thread(target=self.__fetch_async_internal, args=(user, callback))
        thread.start()

    def __fetch_async_internal(self, user, callback):
        try:
            variants = self.__fetch_internal(user)
            if callback:
                callback(user, variants)
            return variants
        except Exception as e:
            self.logger.error(f"[Experiment] Failed to fetch variants: {e}")
            if callback:
                callback(user, {})
            return {}

    def __fetch_internal(self, user):
        self.logger.debug(f"[Experiment] Fetching variants for user: {user}")
        try:
            return self.__do_fetch(user, self.config.fetch_timeout_millis)
        except Exception as e:
            self.logger.error(f"Experiment] Fetch failed: {e}")
            return self.__retry_fetch(user)

    def __retry_fetch(self, user):
        if self.config.fetch_retries == 0:
            return {}
        self.logger.debug("[Experiment] Retrying fetch")
        err = None
        delay_millis = self.config.fetch_retry_backoff_min_millis
        for i in range(self.config.fetch_retries):
            sleep(delay_millis / 1000.0)
            try:
                return self.__do_fetch(user, self.config.fetch_timeout_millis)
            except Exception as e:
                self.logger.error(f"[Experiment] Retry failed: {e}")
                err = e
            delay_millis = min(delay_millis * self.config.fetch_retry_backoff_scalar,
                               self.config.fetch_retry_backoff_max_millis)
        raise err

    def __do_fetch(self, user, timeout_millis):
        start = time.time()
        user_context = self.__add_context(user)
        headers = {
            'Authorization': f"Api-Key {self.api_key}",
            'Content-Type': 'application/json;charset=utf-8'
        }
        scheme, _, host = self.config.server_url.split('/', 3)
        Connection = http.client.HTTPConnection if scheme == 'http:' else http.client.HTTPSConnection
        conn = Connection(host, timeout=timeout_millis / 1000)
        conn.connect()
        body = user_context.to_json().encode('utf8')
        if len(body) > 8000:
            self.logger.warning(f"[Experiment] encoded user object length ${len(body)} "
                                f"cannot be cached by CDN; must be < 8KB")
        self.logger.debug(f"[Experiment] Fetch variants for user: {str(user_context)}")
        conn.request('POST', '/sdk/vardata', body, headers)
        response = conn.getresponse()
        elapsed = '%.3f' % ((time.time() - start) * 1000)
        self.logger.debug(f"[Experiment] Fetch complete in {elapsed} ms")
        json_response = json.loads(response.read().decode("utf8"))
        variants = self.__parse_json_variants(json_response)
        self.logger.debug(f"[Experiment] Fetched variants: {json.dumps(variants, default=str)}")
        conn.close()
        return variants

    def __add_context(self, user):
        user = user or {}
        user.library = user.library or f"experiment-python-server/{__version__}"
        return user

    def __parse_json_variants(self, json_response):
        variants = {}
        for key, value in json_response.items():
            variant_value = ''
            if 'value' in value:
                variant_value = value['value']
            elif 'key' in value:
                variant_value = value['key']
            variants[key] = Variant(variant_value, value.get('payload'))
        return variants
