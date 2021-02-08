import zmq
from .utils import get_socket_address_from_conf


class SocketConnection(object):
    '''
    Handles message queue socket connections
    '''
    @staticmethod
    def bind_to_socket():
        '''
        Binds the publisher to the sockek
        '''
        context = zmq.Context()
        sock = context.socket(zmq.PUSH)
        socket_address = get_socket_address_from_conf()
        sock.bind(socket_address)
        return sock, context

    @staticmethod
    def connect_to_socket():
        '''
        Connects a worker to the socker connection
        '''
        context = zmq.Context()
        sock = context.socket(zmq.PULL)
        socket_address = get_socket_address_from_conf()
        sock.connect(socket_address)
        return sock, context
