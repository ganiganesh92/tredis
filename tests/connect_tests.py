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


class ConnectTests(base.AsyncTestCase):

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
    def test_bad_connect_raises_exception(self):
        client = tredis.RedisClient(str(uuid.uuid4()))
        with self.assertRaises(exceptions.ConnectError):
            yield client.get('foo')

    @testing.gen_test
    def test_bad_db_raises_exception(self):
        client = tredis.RedisClient(os.getenv('REDIS_HOST', 'localhost'),
                                    int(os.getenv('NODE1_PORT', '6379')),
                                    db=255)
        with self.assertRaises(exceptions.RedisError):
            yield client.get('foo')

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
                                    int(os.getenv('NODE1_PORT', '6379')), 0,
                                    on_close)
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
