import socket

from celery import log
from celery.registry import tasks
from celery.worker.revoke import revoked


def expose(fun):
    """Expose method as a celery worker control command, allowed to be called
    from a message."""
    fun.exposed = True
    return fun


class Control(object):
    """The worker control panel.

    :param logger: The current logger to use.

    """

    def __init__(self, logger, hostname=None):
        self.logger = logger
        self.hostname = hostname or socket.gethostname()

    @expose
    def revoke(self, task_id, **kwargs):
        """Revoke task by task id."""
        revoked.add(task_id)
        self.logger.warn("Task %s revoked." % task_id)

    @expose
    def rate_limit(self, task_name, rate_limit, **kwargs):
        """Set new rate limit for a task type.

        See :attr:`celery.task.base.Task.rate_limit`.

        :param task_name: Type of task.
        :param rate_limit: New rate limit.

        """
        try:
            tasks[task_name].rate_limit = rate_limit
        except KeyError:
            return

        if not rate_limit:
            self.logger.warn("Disabled rate limits for tasks of type %s" % (
                                task_name))
        else:
            self.logger.warn("New rate limit for tasks of type %s: %s." % (
                                task_name, rate_limit))


class ControlDispatch(object):
    """Execute worker control panel commands."""

    panel_cls = Control

    def __init__(self, logger, hostname=None):
        self.logger = logger or log.get_default_logger()
        self.hostname = hostname
        self.panel = self.panel_cls(self.logger, hostname=self.hostname)

    def dispatch_from_message(self, message):
        """Dispatch by using message data received by the broker.

        Example:

            >>> def receive_message(message_data, message):
            ...     control = message_data.get("control")
            ...     if control:
            ...         ControlDispatch().dispatch_from_message(control)

        """
        message = dict(message) # don't modify callers message.
        command = message.pop("command")
        destination = message.pop("destination", None)
        if not destination or destination == self.hostname:
            return self.execute(command, message)

    def execute(self, command, kwargs):
        """Execute control command by name and keyword arguments.

        :param command: Name of the command to execute.
        :param kwargs: Keyword arguments.

        """
        control = None
        try:
            control = getattr(self.panel, command)
        except AttributeError:
            pass
        if control is None or not control.exposed:
            self.logger.error("No such control command: %s" % command)
        else:
            return control(**kwargs)
