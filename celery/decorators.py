from inspect import getargspec

from celery.task.base import Task, PeriodicTask


def task(**options):
    """Make a task out of any callable.

        Examples:

            >>> @task()
            ... def refresh_feed(url):
            ...     return Feed.objects.get(url=url).refresh()


            >>> refresh_feed("http://example.com/rss") # Regular
            <Feed: http://example.com/rss>
            >>> refresh_feed.delay("http://example.com/rss") # Async
            <AsyncResult: 8998d0f4-da0b-4669-ba03-d5ab5ac6ad5d>

            # With setting extra options and using retry.

            >>> @task(exchange="feeds")
            ... def refresh_feed(url, **kwargs):
            ...     try:
            ...         return Feed.objects.get(url=url).refresh()
            ...     except socket.error, exc:
            ...         refresh_feed.retry(args=[url], kwargs=kwargs,
            ...                            exc=exc)


    """

    def _create_task_cls(fun):
        base = options.pop("base", Task)

        cls_name = fun.__name__

        def run(self, *args, **kwargs):
            return fun(*args, **kwargs)
        run.__name__ = fun.__name__
        run.argspec = getargspec(fun)

        cls_dict = dict(options)
        cls_dict["run"] = run
        cls_dict["__module__"] = fun.__module__

        task = type(cls_name, (base, ), cls_dict)()

        return task

    return _create_task_cls


def periodic_task(**options):
    """Task decorator to create a periodic task.

    **Usage**

    Run a task once every day:

    .. code-block:: python

        from datetime import timedelta

        @periodic_task(run_every=timedelta(days=1))
        def cronjob(**kwargs):
            logger = cronjob.get_logger(**kwargs)
            logger.warn("Task running...")

    """
    options["base"] = PeriodicTask
    return task(**options)
