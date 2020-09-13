import socket


class DataPublishServer:

    def __init__(self, server_address, server_port):
        self.__server_address = server_address
        self.__server_port = server_port

        self.__queue = None

    def start(self, queue):
        self.__set_queue(queue)
        self.__listen()

    def __set_queue(self, queue):
        self.__queue = queue

    def __listen(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((self.__server_address, self.__server_port))

        try:
            sock.listen(1)
            connection, _ = sock.accept()

            while True:
                data = self.__queue.get()
                connection.send(data.encode())

        except:
            sock.close()
            self.__listen()
