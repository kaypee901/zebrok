import concurrent.futures
from .connection import SocketType, ZmqBindConnection, ZmqConnectTypeConnection
from .registry import InMemoryTaskRegistry
from .logging import create_logger
from .discovery import get_discovered_task_by_name
from .utils import get_publisher_port_and_host

logger = create_logger(__name__)


class TaskRunner(object):
    def __init__(self, task_registry, auto_discover=False):
        self.auto_discover = auto_discover
        self.registry = task_registry

    def find_and_execute_task(self, task_name, **kwargs):
        """
        Finds and execute tasks
        """
        func = self.registry.get(task_name)
        if func:
            func(**kwargs)

        if not func and self.auto_discover:
            func = get_discovered_task_by_name(task_name)
            func(**kwargs)

        if not func:
            logger.error("Task not found!")


class TaskQueueWorker(object):
    def __init__(self, connection, runner):
        self.slaves = []
        self.connection = connection
        self.socket = self.connection.socket
        self.runner = runner
        self.current_slave = 0

    def start(self):
        logger.info(f"starting worker on: {self.connection.socket_address}")
        try:
            while True:
                message = self.socket.recv_json()
                if self.number_of_slaves > 0:
                    logger.info("sending task to slave worker")
                    push_socket = self.slaves[self.current_slave]
                    push_socket.send_json(message)
                    self.increment_current_slave()
                else:
                    task_name = message.pop("task")
                    kwargs = message.pop("kwargs")
                    logger.info(f"received task: {task_name}")
                    self.runner.find_and_execute_task(task_name, **kwargs)
        except KeyboardInterrupt:
            self.stop()

    @property
    def number_of_slaves(self):
        return len(self.slaves)

    def increment_current_slave(self):
        self.current_slave += 1
        if self.current_slave == self.number_of_slaves:
            self.current_slave = 0

    def stop(self):
        self.current_slave = 0
        self.connection.close()

    def add_slave(self, worker):
        self.slaves.append(worker)


class WorkerInitializer(object):
    def __init__(self, number_of_slaves=0, auto_discover=False, task_registry=None):
        self.tasks = task_registry if task_registry else InMemoryTaskRegistry()
        self.runner = TaskRunner(self.tasks, auto_discover)
        self.number_of_slaves = number_of_slaves

    def register_task(self, task):
        """
        Registers tasks to in-memory task registry
        """
        self.tasks.register(task)

    def _initialize_workers(self):
        port, host = get_publisher_port_and_host()
        max_workers = self.number_of_slaves + 1
        master_socket = ZmqBindConnection(SocketType.ZmqPull, host, port)
        master_worker = TaskQueueWorker(master_socket, self.runner)

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            for i in range(self.number_of_slaves):
                slave_port = port + i + 1
                push_socket = ZmqBindConnection(
                    SocketType.ZmqPush, host, slave_port, master_socket.context
                )
                master_worker.add_slave(push_socket.socket)

                pull_socket_ = ZmqConnectTypeConnection(
                    SocketType.ZmqPull, host, slave_port
                )
                slave_worker = TaskQueueWorker(pull_socket_, self.runner)
                executor.submit(slave_worker.start)

            executor.submit(master_worker.start)

    def start(self):
        """
        Starts workers to be receiving incoming
        messages
        """
        self._initialize_workers()
