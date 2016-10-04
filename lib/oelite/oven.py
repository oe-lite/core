import oebakery
from oebakery import die, err, warn, info, debug
from oelite import *
from recipe import OEliteRecipe
from runq import OEliteRunQueue
import oelite.meta
import oelite.util
import oelite.arch
import oelite.parse
import oelite.task
import oelite.item
from oelite.parse import *
from oelite.cookbook import CookBook

import oelite.fetch

import bb.utils

import sys
import os
import glob
import shutil
import hashlib
import logging
import time

class OEliteOven:
    def __init__(self, baker, capacity):
        self.capacity = capacity
        self.baker = baker
        self.starttime = dict()
        self.failed_tasks = []
        self.total = baker.runq.number_of_tasks_to_build()
        self.count = 0

    # The tasks which are currently baking are the keys in the
    # .starttime member. Implementing __contains__ makes sense of
    # "task in oven".
    def __contains__(self, x):
        return x in self.starttime

    # Allow "for t in oven:"
    def __iter__(self):
        return iter(self.starttime)

    # Size of oven == number of currently baking tasks.
    def __len__(self):
        return len(self.starttime)

    def currently_baking(self):
        return list(self)

    def add(self, task):
        self.capacity -= task.weight
        self.starttime[task] = oelite.util.now()

    def remove(self, task):
        now = oelite.util.now()
        delta = now - self.starttime[task]
        del self.starttime[task]
        self.capacity += task.weight
        return delta

    def start(self, task):
        self.add(task)

        self.count += 1
        debug("")
        debug("Preparing %s"%(task))
        task.prepare()
        info("%s started - %d / %d "%(task, self.count, self.total))
        task.build_started()

        task.start()

    def wait_task(self, poll, task):
        """Wait for a specific task to finish baking. Returns pair (result,
        delta), or None in case poll=True and the task is not yet
        done.

        """
        assert(task in self)
        result = task.wait(poll)
        if result is None:
            return None
        delta = self.remove(task)

        if result:
            info("%s finished - %s s" % (task, delta))
            task.build_done(self.baker.runq.get_task_buildhash(task))
            self.baker.runq.mark_done(task)
        else:
            err("%s failed - %s s" % (task, delta))
            self.failed_tasks.append(task)
            task.build_failed()

        return (task, result, delta)

    def wait_any(self, poll):
        """Wait for any task currently in the oven to finish. Returns triple
        (task, result, time), or None.

        """
        if not poll and len(self) == 0:
            raise Exception("nothing in the oven, so you'd wait forever...")
        tasks = self.currently_baking()
        tasks.sort(key=lambda t: self.starttime[t])
        while True:
            for t in tasks:
                result = self.wait_task(True, t)
                if result is not None:
                    return result
            if poll:
                break
            time.sleep(0.1)
        return None

    def wait_all(self, poll):
        """Do wait_task once for every task currently in the oven once. With
        poll=False, this amounts to waiting for every current task to
        finish.

        """
        tasks = self.currently_baking()
        tasks.sort(key=lambda t: self.starttime[t])
        for t in tasks:
            self.wait_task(poll, t)
