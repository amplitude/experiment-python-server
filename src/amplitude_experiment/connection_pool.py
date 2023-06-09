import threading
import time
import logging
from typing import Any

from http.client import HTTPConnection, HTTPResponse, HTTPSConnection


class WrapperHTTPConnection:

    def __init__(self, pool: 'HTTPConnectionPool', conn: HTTPConnection) -> None:
        """
        Wrapped Http Connection, used with connection pool
        :param pool: Connection pool this connection belongs to
        :param conn: Wrapped HTTPConnection
        """
        self.pool = pool
        self.conn = conn
        self.response = None
        self.last_time = time.time()
        self.is_available = True

    def __enter__(self) -> 'WrapperHTTPConnection':
        return self

    def __exit__(self, *exit_info: Any) -> None:
        if not self.response.will_close and not self.response.is_closed():
            self.close()
        self.pool.release(self)

    def request(self, *args: Any, **kwargs: Any) -> HTTPResponse:
        try:
            self.conn.request(*args, **kwargs)
            self.response = self.conn.getresponse()
            return self.response
        except Exception as e:
            self.close()
            raise e

    def close(self) -> None:
        self.conn.close()
        self.is_available = False


class HTTPConnectionPool:

    def __init__(self, host: str, port: int = None, max_size: int = None, idle_timeout: int = None,
                 read_timeout: float = None, scheme: str = 'https') -> None:
        """
        A simple connection pool to reuse the http connections
        :param host: pass
        :param port: pass
        :param max_size: Max connection allowed
        :param idle_timeout: Idle timeout to clear the connection
        :param read_timeout: Read timeout with connection
        :param scheme: http or https
        """
        self.host = host
        self.port = port
        self.max_size = max_size
        self.idle_timeout = idle_timeout
        self.read_timeout = read_timeout
        self.scheme = scheme
        self._lock = threading.Condition()
        self._pool = []
        self.conn_num = 0
        self.is_closed = False
        self._clearer = None
        self.start_clear_conn()

    def acquire(self, blocking: bool = True, timeout: int = None) -> WrapperHTTPConnection:
        if self.is_closed:
            raise ConnectionPoolClosed
        with self._lock:
            if self.max_size is None or not self.is_full():
                if self.is_pool_empty():
                    self._put_connection(self._create_connection())
            else:
                if not blocking:
                    if self.is_pool_empty():
                        raise EmptyPoolError
                elif timeout is None:
                    while self.is_pool_empty():
                        self._lock.wait()
                elif timeout < 0:
                    raise ValueError("'timeout' must be a non-negative number")
                else:
                    end_time = time.time() + timeout
                    while self.is_pool_empty():
                        remaining = end_time - time.time()
                        if remaining <= 0:
                            raise EmptyPoolError
                        self._lock.wait(remaining)
            return self._get_connection()

    def release(self, conn: WrapperHTTPConnection) -> None:
        if self.is_closed:
            conn.close()
            return
        with self._lock:
            if not conn.is_available:
                conn.close()
                self.conn_num -= 1
                conn = self._create_connection()
            self._put_connection(conn)
            self._lock.notify()

    def _get_connection(self) -> WrapperHTTPConnection:
        try:
            return self._pool.pop()
        except IndexError:
            raise EmptyPoolError

    def _put_connection(self, conn: WrapperHTTPConnection) -> None:
        conn.last_time = time.time()
        self._pool.append(conn)

    def _create_connection(self) -> WrapperHTTPConnection:
        self.conn_num += 1
        connection = HTTPConnection if self.scheme == 'http:' else HTTPSConnection
        return WrapperHTTPConnection(self, connection(self.host, self.port, timeout=self.read_timeout))

    def is_pool_empty(self) -> bool:
        return len(self._pool) == 0

    def is_full(self) -> bool:
        if self.max_size is None:
            return False
        return self.conn_num >= self.max_size

    def close(self) -> None:
        if self.is_closed:
            return
        self.is_closed = True
        self.stop_clear_conn()
        pool, self._pool = self._pool, None
        for conn in pool:
            conn.close()

    def clear_idle_conn(self) -> None:
        if self.is_closed:
            raise ConnectionPoolClosed
        # Staring a thread to clear idle connections
        threading.Thread(target=self._clear_idle_conn).start()

    def _clear_idle_conn(self) -> None:
        if not self._lock.acquire(timeout=self.idle_timeout):
            return
        current_time = time.time()
        if self.is_pool_empty():
            pass
        elif current_time - self._pool[-1].last_time >= self.idle_timeout:
            self.conn_num -= len(self._pool)
            self._pool.clear()
        else:
            left, right = 0, len(self._pool) - 1
            while left < right:
                mid = (left + right) // 2
                if current_time - self._pool[mid].last_time >= self.idle_timeout:
                    left = mid + 1
                else:
                    right = mid
            self._pool = self._pool[left:]
            self.conn_num -= left
        self._lock.release()

    def start_clear_conn(self) -> None:
        if self.idle_timeout is None:
            return
        self.clear_idle_conn()
        self._clearer = threading.Timer(self.idle_timeout, self.start_clear_conn)
        self._clearer.daemon = True
        self._clearer.start()

    def stop_clear_conn(self) -> None:
        if self._clearer is not None:
            self._clearer.cancel()

    def __enter__(self) -> 'HTTPConnectionPool':
        return self

    def __exit__(self, *exit_info: Any) -> None:
        self.close()


class EmptyPoolError(Exception):
    pass


class ConnectionPoolClosed(Exception):
    pass
