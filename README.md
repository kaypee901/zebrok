# zebrok
Brokerless task queue for python based on 0Mq

### - How to use zebrok
========================

* Configuring Env Vars:
    - PUBLISHER_HOST=
    - PUBLISHER_PORT=

    -- `If not set defaults to localhost:5690`

* Creating A Task [tasks.py]
```
from zebrok import app

@app.Task
def long_running_task(param):
    do_some_time_consuming_task(param)
```

* Configuring a worker and registering the task [start.py]
    - NB: `A task can also be discovered automatically if placed in a tasks.py file in the root folder of the project.`
    `- You can also set number of slave worker threads to be running by passing number_of_slaves argument`
```
from zebrok.worker import WorkerInitializer
from tasks import long_running_task


worker = WorkerInitializer(number_of_slaves=1, auto_discover=True)
worker.register_task(long_running_task)
worker.start()
```

* Starting the Zebrok Worker to listen for tasks -
`python start.py` where start.py is the file in which you configured the worker

* Executing a task [client.py]
```
from tasks import long_running_task

long_running_task.run(param="dowork")
```

- This library comes with the benefits of 0Mq
     - Low Latency
     - Lightweight
     - No broker required
     - Fast
     - Open source
