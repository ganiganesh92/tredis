import logging
import os
import re
import mock
import uuid

from tornado import testing
from tornado import gen

import tredis
from tredis import exceptions

from . import base

ADDR_PATTERN = re.compile(r'(addr=([\.\d:]+))')

class BadConnectTestCase(base.AsyncTestCase):

    AUTO_CONNECT = False

    @property
    def redis_host(self):
        return '255.255.255.255'

    @testing.gen_test
    def test_bad_connect_raises_exception(self):
        with self.assertRaises(exceptions.ConnectError):
            yield self.client.connect()


class BadConnectDBTestCase(base.AsyncTestCase):

    AUTO_CONNECT = False

    @property
    def redis_db(self):
        return 255

    @testing.gen_test
    def test_bad_connect_db_raises_exception(self):
        with self.assertRaises(exceptions.RedisError):
            yield self.client.connect()


class ConnectTestCase(base.AsyncTestCase):

    @gen.coroutine
    def _kill_client(self, client):
        results = yield client._execute([b'CLIENT', b'LIST'])
        matches = ADDR_PATTERN.findall(results.decode('ascii'))
        value = None
        for match, addr in matches:
            value = addr
        self.assertIsNotNone(value, 'Could not find client')
        result = yield client._execute(
            [b'CLIENT', b'KILL', value.encode('ascii')])
        logging.info('CLIENT KILL result: %r', result)

    @testing.gen_test
    def test_close_invokes_iostream_close(self):
        yield self.client.set('foo', 'bar', 1)  # Establish the connection
        stream = self.client._connection._stream
        with mock.patch.object(stream, 'close') as close:
            self.client.close()
            close.assert_called_once_with()

    @testing.gen_test
    def test_on_close_callback_invoked(self):
        on_close = mock.Mock()
        client = tredis.RedisClient(os.getenv('REDIS_HOST', 'localhost'),
                                    int(os.getenv('REDIS1_PORT', '6379')), 0,
                                    on_close,
                                    auto_connect=False)
        yield client.connect()
        result = yield client.set('foo', 'bar', 10)
        self.assertTrue(result)
        yield self._kill_client(client)
        on_close.assert_called_once_with()

    @testing.gen_test
    def test_competing_connections(self):
        result1 = self.client.set('foo', 'bar', 10)
        result2 = self.client.set('foo', 'baz', 10)
        yield result1
        yield result2

        self.assertTrue(result1)
        self.assertTrue(result2)

    @testing.gen_test
    def test_competing_connections(self):
        result1 = self.client.set('foo', 'bar', 10)
        result2 = self.client.set('foo', 'baz', 10)
        yield result1
        yield result2
        self.assertTrue(result1)
        self.assertTrue(result2)

    @testing.gen_test
    def test_close_unopened_client(self):
        with self.assertRaises(exceptions.ConnectionError):
            self.client.close()
