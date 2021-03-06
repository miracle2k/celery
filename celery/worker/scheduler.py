import time
import heapq


class Scheduler(object):
    """ETA scheduler.

    :param ready_queue: Queue to move items ready for processing.

    """

    def __init__(self, ready_queue):
        self.ready_queue = ready_queue
        self._queue = []

    def enter(self, item, eta=None, priority=0, callback=None):
        """Enter item into the scheduler.

        :param item: Item to enter.
        :param eta: Scheduled time as a :class:`datetime.datetime` object.
        :param priority: Unused.
        :param callback: Callback called when the item is scheduled.
            This callback takes no arguments.

        """
        eta = time.mktime(eta.timetuple()) if eta else time.time()
        heapq.heappush(self._queue, (eta, priority, item, callback))

    def __iter__(self):
        """The iterator yields the time to sleep for between runs."""

        # localize variable access
        q = self._queue
        nowfun = time.time
        pop = heapq.heappop
        ready_queue = self.ready_queue

        while True:
            if q:
                eta, priority, item, callback = verify = q[0]
                now = nowfun()

                if now < eta:
                    yield eta - now
                else:
                    event = pop(q)

                    if event is verify: # pragma: no cover
                        ready_queue.put(item)
                        callback and callback()
                        yield 0
                    else:
                        heapq.heappush(q, event)
            yield None

    def empty(self):
        """Is the schedule empty?"""
        return not self._queue

    @property
    def queue(self):
        events = list(self._queue)
        return map(heapq.heappop, [events]*len(events))
