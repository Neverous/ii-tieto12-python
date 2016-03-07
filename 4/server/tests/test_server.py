# -*- encoding: utf-8 -*-
import unittest
from mock import Mock
import cPickle as pickle

from socketserver.SocketServer import BomberFactory, BomberProtocol
from protocolObjects import Countdown, Position, Map

class ServerTestCase(unittest.TestCase):
    def setUp(self):
        self.factory = BomberFactory(2, (20, 10))

    def tearDown(self):
        self.factory = None

    def test_countdown(self):
        client1 = BomberProtocol()
        client1.factory = self.factory
        client1.transport = Mock()
        client1.transport.write = Mock(return_value = None)
        client1.connectionMade()

        client2 = BomberProtocol()
        client2.factory = self.factory
        client2.transport = Mock()
        client2.transport.write = Mock(return_value = None)
        client2.connectionMade()

        # reaktor nie działa więc odpalam ręcznie
        self.factory.pregame(True)
        self.assertEqual(client1.transport.write.call_count, 1)
        self.assertEqual(len(client1.transport.write.call_args[0]), 1)
        obj = pickle.loads(client1.transport.write.call_args[0][0])
        self.assertIsInstance(obj, Countdown)
        self.assertEqual(obj.number, 3)
        self.assertEqual(obj.mapSize, Position(10, 20))

        self.assertEqual(client2.transport.write.call_count, 1)
        self.assertEqual(len(client2.transport.write.call_args[0]), 1)
        obj = pickle.loads(client2.transport.write.call_args[0][0])
        self.assertIsInstance(obj, Countdown)
        self.assertEqual(obj.number, 3)
        self.assertEqual(obj.mapSize, Position(10, 20))

        self.factory.pregame()
        self.assertEqual(client1.transport.write.call_count, 2)
        self.assertEqual(len(client1.transport.write.call_args[0]), 1)
        obj = pickle.loads(client1.transport.write.call_args[0][0])
        self.assertIsInstance(obj, Countdown)
        self.assertEqual(obj.number, 2)
        self.assertEqual(obj.mapSize, Position(10, 20))

        self.assertEqual(client2.transport.write.call_count, 2)
        self.assertEqual(len(client2.transport.write.call_args[0]), 1)
        obj = pickle.loads(client2.transport.write.call_args[0][0])
        self.assertIsInstance(obj, Countdown)
        self.assertEqual(obj.number, 2)
        self.assertEqual(obj.mapSize, Position(10, 20))

        self.factory.pregame()
        self.assertEqual(client1.transport.write.call_count, 3)
        self.assertEqual(len(client1.transport.write.call_args[0]), 1)
        obj = pickle.loads(client1.transport.write.call_args[0][0])
        self.assertIsInstance(obj, Countdown)
        self.assertEqual(obj.number, 1)
        self.assertEqual(obj.mapSize, Position(10, 20))

        self.assertEqual(client2.transport.write.call_count, 3)
        self.assertEqual(len(client2.transport.write.call_args[0]), 1)
        obj = pickle.loads(client2.transport.write.call_args[0][0])
        self.assertIsInstance(obj, Countdown)
        self.assertEqual(obj.number, 1)
        self.assertEqual(obj.mapSize, Position(10, 20))

        self.factory.pregame()
        self.assertEqual(client1.transport.write.call_count, 4)
        self.assertEqual(len(client1.transport.write.call_args[0]), 1)
        obj = pickle.loads(client1.transport.write.call_args[0][0])
        self.assertIsInstance(obj, Map)

        self.assertEqual(client2.transport.write.call_count, 4)
        self.assertEqual(len(client2.transport.write.call_args[0]), 1)
        obj = pickle.loads(client2.transport.write.call_args[0][0])
        self.assertIsInstance(obj, Map)

