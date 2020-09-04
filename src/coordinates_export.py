try:
    import cPickle as pickle
except ModuleNotFoundError:
    import pickle

from queue import Queue
import time
import socket
import threading
import sys


class CoordinatesExport:

    def __init__(self, coordinates_export_config):
        self.coordinates_export_config = coordinates_export_config

        self.data_queue = Queue(1)


def save_config(coordinates_export_config_data):
    # Overwrites any existing file.
    with open('../assets/configs/coordinates_export_config_data.pkl', 'wb') as output:
        pickle.dump({
            'marker_lenght': coordinates_export_config_data.marker_lenght,
            'selected_marker': coordinates_export_config_data.selected_marker}, output, pickle.HIGHEST_PROTOCOL)


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
