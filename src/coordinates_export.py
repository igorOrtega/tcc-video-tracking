try:
    import cPickle as pickle
except ModuleNotFoundError:
    import pickle

from queue import Queue
import socket
import threading
import sys


class CoordinatesExport:

    def __init__(self, coordinates_export_config):
        self.coordinates_export_config = coordinates_export_config

        self.data_queue = Queue(1)

    def run(self):
        server_thread = threading.Thread(target=self.connection)
        server_thread.daemon = True
        server_thread.start()

    def connection(self):

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (self.coordinates_export_config.server_address,
                          self.coordinates_export_config.server_port)
        sock.bind(server_address)

        sock.listen(1)

        while True:
            connection, _ = sock.accept()

            while True:
                data = self.data_queue.get()
                connection.send(data.encode())

    def export_data(self, data):
        if(self.data_queue.full()):
            self.clear_queue()

        self.data_queue.put(data)

    def clear_queue(self):
        while not self.data_queue.empty():
            try:
                self.data_queue.get(False)
            except:
                continue

            self.data_queue.task_done()


def save_config(coordinates_export_config_data):
    # Overwrites any existing file.
    with open('../assets/configs/coordinates_export_config_data.pkl', 'wb') as output:
        pickle.dump({
            'server_address': coordinates_export_config_data.server_address,
            'server_port': coordinates_export_config_data.server_port}, output, pickle.HIGHEST_PROTOCOL)


def load_config():
    with open('../assets/configs/coordinates_export_config_data.pkl', 'rb') as file:
        return pickle.load(file)


class CoordinatesExportCofig:

    def __init__(self, server_address, server_port):
        self.server_address = server_address
        self.server_port = server_port

    @classmethod
    def persisted(cls):
        coordinates_export_config_data = load_config()
        return cls(coordinates_export_config_data['server_address'],
                   coordinates_export_config_data['server_port'])
