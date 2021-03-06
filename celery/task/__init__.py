"""

Working with tasks and task sets.

"""
from billiard.serialization import pickle

from celery.conf import AMQP_CONNECTION_TIMEOUT
from celery.execute import apply_async
from celery.registry import tasks
from celery.backends import default_backend
from celery.messaging import TaskConsumer, BroadcastPublisher, with_connection
from celery.task.base import Task, TaskSet, PeriodicTask
from celery.task.base import ExecuteRemoteTask, AsynchronousMapTask
from celery.task.rest import RESTProxyTask
from celery.task.builtins import DeleteExpiredTaskMetaTask, PingTask


def discard_all(connect_timeout=AMQP_CONNECTION_TIMEOUT):
    """Discard all waiting tasks.

    This will ignore all tasks waiting for execution, and they will
    be deleted from the messaging server.

    :returns: the number of tasks discarded.

    :rtype: int

    """

    def _discard(connection):
        consumer = TaskConsumer(connection=connection)
        try:
            return consumer.discard_all()
        finally:
            consumer.close()

    return with_connection(_discard, connect_timeout=connect_timeout)


def revoke(task_id, connection=None, connect_timeout=None):
    """Revoke a task by id.

    Revoked tasks will not be executed after all.

    """

    def _revoke(connection):
        broadcast = BroadcastPublisher(connection)
        try:
            broadcast.revoke(task_id)
        finally:
            broadcast.close()

    return with_connection(_revoke, connection=connection,
                           connect_timeout=connect_timeout)


def is_successful(task_id):
    """Returns ``True`` if task with ``task_id`` has been executed.

    :rtype: bool

    """
    return default_backend.is_successful(task_id)


def dmap(func, args, timeout=None):
    """Distribute processing of the arguments and collect the results.

    Example

        >>> from celery.task import dmap
        >>> import operator
        >>> dmap(operator.add, [[2, 2], [4, 4], [8, 8]])
        [4, 8, 16]

    """
    return TaskSet.map(func, args, timeout=timeout)


def dmap_async(func, args, timeout=None):
    """Distribute processing of the arguments and collect the results
    asynchronously.

    :returns: :class:`celery.result.AsyncResult` object.

    Example

        >>> from celery.task import dmap_async
        >>> import operator
        >>> presult = dmap_async(operator.add, [[2, 2], [4, 4], [8, 8]])
        >>> presult
        <AsyncResult: 373550e8-b9a0-4666-bc61-ace01fa4f91d>
        >>> presult.status
        'SUCCESS'
        >>> presult.result
        [4, 8, 16]

    """
    return TaskSet.map_async(func, args, timeout=timeout)


def execute_remote(func, *args, **kwargs):
    """Execute arbitrary function/object remotely.

    :param func: A callable function or object.

    :param \*args: Positional arguments to apply to the function.

    :param \*\*kwargs: Keyword arguments to apply to the function.

    The object must be picklable, so you can't use lambdas or functions
    defined in the REPL (the objects must have an associated module).

    :returns: class:`celery.result.AsyncResult`.

    """
    return ExecuteRemoteTask.delay(pickle.dumps(func), args, kwargs)


def ping():
    """Test if the server is alive.

    Example:

        >>> from celery.task import ping
        >>> ping()
        'pong'
    """
    return PingTask.apply_async().get()
