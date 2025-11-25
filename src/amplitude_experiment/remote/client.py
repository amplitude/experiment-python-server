import json
import threading
import time
from time import sleep
from typing import Any, Dict

from .config import RemoteEvaluationConfig
from .fetch_options import FetchOptions
from ..connection_pool import HTTPConnectionPool
from ..exception import FetchException
from ..user import User
from ..util.deprecated import deprecated
from ..util.variant import evaluation_variants_json_to_variants
from ..variant import Variant
from ..version import __version__


class RemoteEvaluationClient:
    """Main client for fetching variant data."""

    def __init__(self, api_key, config=None):
        """
        Creates a new Experiment Client instance.
            Parameters:
                api_key (str): The environment API Key
                config (RemoteEvaluationConfig): Config Object

            Returns:
                Experiment Client instance.
        """
        if not api_key:
            raise ValueError("Experiment API key is empty")
        self.api_key = api_key
        self.config = config or RemoteEvaluationConfig()
        self.logger = self.config.logger
        self.__setup_connection_pool()

    def fetch_v2(self, user: User, fetch_options: FetchOptions = None):
        """
        Fetch all variants for a user synchronously. This method will automatically retry if configured, and throw if
        all retries fail. This function differs from fetch as it will return a default variant object if the flag
        was evaluated but the user was not assigned (i.e. off).

            Parameters:
                user (User): The Experiment User to fetch variants for.
                fetch_options (FetchOptions): The Fetch Options

            Returns:
                Variants Dictionary.
        """
        try:
            return self.__fetch_internal(user, fetch_options)
        except Exception as e:
            self.logger.error(f"[Experiment] Failed to fetch variants: {e}")
            raise e

    def fetch_async_v2(self, user: User, callback=None):
        """
        Fetch all variants for a user asynchronous. Will trigger callback after fetch complete
            Parameters:
                user (User): The Experiment User
                callback (callable): Callback function, takes user and variants arguments
        """
        thread = threading.Thread(target=self.__fetch_async_internal, args=(user, callback))
        thread.start()

    @deprecated("Use fetch_v2")
    def fetch(self, user: User, fetch_options: FetchOptions = None):
        """
        Fetch all variants for a user synchronous. This method will automatically retry if configured.
            Parameters:
                user (User): The Experiment User
                fetch_options (FetchOptions): The Fetch Options

            Returns:
                Variants Dictionary.
        """
        try:
            variants = self.fetch_v2(user, fetch_options)
            return self.__filter_default_variants(variants)
        except Exception:
            return {}

    @deprecated("Use fetch_async_v2")
    def fetch_async(self, user: User, callback=None):
        """
        Fetch all variants for a user asynchronous. Will trigger callback after fetch complete
            Parameters:
                user (User): The Experiment User
                callback (callable): Callback function, takes user and variants arguments
        """
        def wrapper(u, v, e=None):
            v = self.__filter_default_variants(v)
            if callback is not None:
                callback(u, v, e)
        self.fetch_async_v2(user, wrapper)

    def __fetch_async_internal(self, user, callback):
        try:
            variants = self.__fetch_internal(user)
            if callback:
                callback(user, variants)
            return variants
        except Exception as e:
            if callback:
                callback(user, {}, e)
            return {}

    def __fetch_internal(self, user, fetch_options: FetchOptions = None):
        self.logger.debug(f"[Experiment] Fetching variants for user: {user}")
        try:
            return self.__do_fetch(user, fetch_options)
        except Exception as e:
            self.logger.error(f"[Experiment] Fetch failed: {e}")
            if self.__should_retry_fetch(e):
                return self.__retry_fetch(user, fetch_options)

    def __retry_fetch(self, user, fetch_options: FetchOptions = None):
        if self.config.fetch_retries == 0:
            return {}
        self.logger.debug("[Experiment] Retrying fetch")
        err = None
        delay_millis = self.config.fetch_retry_backoff_min_millis
        for i in range(self.config.fetch_retries):
            sleep(delay_millis / 1000.0)
            try:
                return self.__do_fetch(user, fetch_options)
            except Exception as e:
                self.logger.error(f"[Experiment] Retry failed: {e}")
                err = e
            delay_millis = min(delay_millis * self.config.fetch_retry_backoff_scalar,
                               self.config.fetch_retry_backoff_max_millis)
        raise err

    def __do_fetch(self, user, fetch_options: FetchOptions = None):
        start = time.time()
        user_context = self.__add_context(user)
        headers = {
            'Authorization': f"Api-Key {self.api_key}",
            'Content-Type': 'application/json;charset=utf-8'
        }
        if fetch_options and fetch_options.tracksAssignment is not None:
            headers['X-Amp-Exp-Track'] = "track" if fetch_options.tracksAssignment else "no-track"
        if fetch_options and fetch_options.tracksExposure is not None:
            headers['X-Amp-Exp-Exposure-Track'] = "track" if fetch_options.tracksExposure else "no-track"

        conn = self._connection_pool.acquire()
        body = user_context.to_json().encode('utf8')
        if len(body) > 8000:
            self.logger.warning(f"[Experiment] encoded user object length ${len(body)} "
                                f"cannot be cached by CDN; must be < 8KB")
        self.logger.debug(f"[Experiment] Fetch variants for user: {str(user_context)}")
        try:
            response = conn.request('POST', '/sdk/v2/vardata?v=0', body, headers)
            elapsed = '%.3f' % ((time.time() - start) * 1000)
            self.logger.debug(f"[Experiment] Fetch complete in {elapsed} ms")
            if response.status != 200:
                raise FetchException(response.status,
                                     f"Fetch error response: status={response.status} {response.reason}")
            json_response = json.loads(response.read().decode("utf8"))
            variants = evaluation_variants_json_to_variants(json_response)
            self.logger.debug(f"[Experiment] Fetched variants: {json.dumps(variants, default=str)}")
            return variants
        finally:
            self._connection_pool.release(conn)

    def __setup_connection_pool(self):
        scheme, _, host = self.config.server_url.split('/', 3)
        timeout = self.config.fetch_timeout_millis / 1000
        self._connection_pool = HTTPConnectionPool(host, max_size=1, idle_timeout=30,
                                                   read_timeout=timeout, scheme=scheme)

    def close(self) -> None:
        """
        Close resource like connection pool with client
        """
        self._connection_pool.close()

    def __enter__(self) -> 'RemoteEvaluationClient':
        return self

    def __exit__(self, *exit_info: Any) -> None:
        self.close()

    @staticmethod
    def __add_context(user):
        user = user or {}
        user.library = user.library or f"experiment-python-server/{__version__}"
        return user

    @staticmethod
    def __filter_default_variants(variants: Dict[str, Variant]) -> Dict[str, Variant]:
        def is_default_variant(variant: Variant) -> bool:
            default = False
            if variant.metadata is not None and variant.metadata.get('default') is not None:
                default = variant.metadata.get('default')
            deployed = True
            if variant.metadata is not None and variant.metadata.get('deployed') is not None:
                deployed = variant.metadata.get('deployed')
            return default and not deployed

        return {key: variant for key, variant in variants.items() if not is_default_variant(variant)}

    @staticmethod
    def __should_retry_fetch(err: Exception):
        if isinstance(err, FetchException):
            return err.status_code < 400 or err.status_code >= 500 or err.status_code == 429
        return True
