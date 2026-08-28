#!/usr/bin/env python3

import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parent


class FakeClient:
    instances = []

    def __init__(self):
        self.on_connect = None
        self.on_disconnect = None
        self.on_message = None
        self.on_publish = None
        self.reconnect_delay = None
        self.connect_async_args = None
        self.subscriptions = []
        self.publications = []
        self.loop_started = False
        self.loop_stopped = False
        self.loop_forever_args = None
        self.disconnected = False
        self.instances.append(self)

    def reconnect_delay_set(self, min_delay, max_delay):
        self.reconnect_delay = (min_delay, max_delay)

    def connect_async(self, host, port, keepalive):
        self.connect_async_args = (host, port, keepalive)

    def subscribe(self, topic):
        self.subscriptions.append(topic)

    def publish(self, topic, payload, retain=False):
        self.publications.append((topic, payload, retain))

    def loop_start(self):
        self.loop_started = True

    def loop_stop(self):
        self.loop_stopped = True

    def loop_forever(self, **kwargs):
        self.loop_forever_args = kwargs

    def disconnect(self):
        self.disconnected = True


def install_fake_dependencies():
    paho_module = types.ModuleType("paho")
    mqtt_package = types.ModuleType("paho.mqtt")
    mqtt_client = types.ModuleType("paho.mqtt.client")
    mqtt_client.Client = FakeClient
    paho_module.mqtt = mqtt_package
    mqtt_package.client = mqtt_client

    sys.modules["paho"] = paho_module
    sys.modules["paho.mqtt"] = mqtt_package
    sys.modules["paho.mqtt.client"] = mqtt_client
    sys.modules["simplejson"] = json


def load_module(name, relative_path):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MQTTReconnectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        install_fake_dependencies()
        cls.control = load_module("ruca_mqtt_control_test", "Ruca2_mqtt.py")
        cls.status = load_module("ruca_mqtt_status_test", "Ruca2_mqtt_status.py")
        cls.gui = load_module(
            "ruca_mqtt_gui_test",
            "Ruca2_UI/c_filtros_ruca2_mqtt.py",
        )

    def setUp(self):
        FakeClient.instances.clear()
        self.control.mqtt_conectado.clear()
        self.status.mqtt_conectado.clear()

    def test_control_retries_initial_connection_and_resubscribes(self):
        cliente = self.control.crea_cliente_mqtt()

        self.assertEqual(cliente.reconnect_delay, (1, 30))
        self.assertEqual(cliente.connect_async_args, ("192.168.0.243", 1883, 60))
        cliente.on_connect(cliente, None, None, 0)
        self.assertTrue(self.control.mqtt_conectado.is_set())
        self.assertIn(self.control.MQTT_TOPIC, cliente.subscriptions)

        with mock.patch.object(self.control.MQTTLOOP, "start"):
            self.control.main()

        self.assertEqual(
            FakeClient.instances[-1].loop_forever_args,
            {"retry_first_connection": True},
        )

    def test_status_starts_network_loop_and_tracks_disconnect(self):
        with mock.patch.object(self.status.MQTTLOOP, "start"), mock.patch.object(
            self.status.time,
            "sleep",
            side_effect=KeyboardInterrupt,
        ):
            self.status.main()

        cliente = FakeClient.instances[-1]
        self.assertEqual(cliente.reconnect_delay, (1, 30))
        self.assertEqual(cliente.connect_async_args, ("192.168.0.243", 1883, 60))
        self.assertTrue(cliente.loop_started)
        self.assertTrue(cliente.loop_stopped)

        cliente.on_connect(cliente, None, None, 0)
        self.assertTrue(self.status.mqtt_conectado.is_set())
        cliente.on_disconnect(cliente, None, 1)
        self.assertFalse(self.status.mqtt_conectado.is_set())

    def test_gui_uses_nonblocking_reconnection_and_closes_cleanly(self):
        archivos = "\n".join("Elemento %d" % i for i in range(1, 9))
        with mock.patch("builtins.open", mock.mock_open(read_data=archivos)):
            ruca = self.gui.RUCA(lambda info: None)

        cliente = ruca.mosquitto
        self.assertEqual(cliente.reconnect_delay, (1, 30))
        self.assertEqual(cliente.connect_async_args, ("192.168.0.243", 1883, 60))
        self.assertEqual(cliente.publications, [])

        ruca.run()
        cliente.on_connect(cliente, None, None, 0)
        self.assertTrue(ruca.mqtt_conectado)
        self.assertIn("oan/control/1.5m/ruca2/estado", cliente.subscriptions)
        self.assertEqual(
            cliente.publications[-1][0],
            "oan/control/1.5m/ruca2/cambianombres",
        )

        cliente.on_disconnect(cliente, None, 1)
        self.assertFalse(ruca.mqtt_conectado)
        ruca.cerrar()
        self.assertTrue(cliente.disconnected)
        self.assertTrue(cliente.loop_stopped)


if __name__ == "__main__":
    unittest.main()
