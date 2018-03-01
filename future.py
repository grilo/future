#!/usr/bin/env python

import logging

import signal
import multiprocessing as mp
import subprocess
import shlex

import copy_reg
import types

# Stolen from:
# https://stackoverflow.com/questions/11726809
# What this does is teaching python how to pickle an instance method
def _reduce_method(meth):
    return (getattr,(meth.__self__,meth.__func__.__name__))
copy_reg.pickle(types.MethodType,_reduce_method)


class Task(object):

    def __init__(self, callable, args=(), callback=None):
        self.sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
        self.pool = mp.Pool()
        signal.signal(signal.SIGINT, self.sigint_handler)
        self.result = self.pool.apply_async(callable, args, callback=callback)

    def ready(self):
        for worker in self.pool._pool:
            if worker.is_alive():
                return False
        return True

    def get(self):
        result = None
        try:
            result = self.result.get()
            self.pool.close()
        except KeyboardInterrupt:
            self.pool.terminate()
        else:
            self.pool.close()
        self.pool.join()
        return result


class Command(object):

    """
        promise.Command('ls') | promise.Command('wc -l')
        >>> 3
    """

    def __init__(self, command, output=False):
        self.command = command
        self.proc = None
        self.stdin = None
        self.stdout = subprocess.PIPE
        self.stderr = subprocess.PIPE
        self.run()

    def ready(self):
        if self.proc.poll():
            return True
        return False

    def get(self):
        out, err = self.proc.communicate()
        rc = self.proc.returncode
        return rc, out, err

    def run(self):
        self.proc = subprocess.Popen(shlex.split(self.command),
                                     stdout=self.stdout,
                                     stderr=self.stderr,
                                     stdin=self.stdin)

    def __or__(self, command):
        command.stdin = self.proc.stdout
        command.run()
        return command

    def __str__(self):
        return self.get()[1]

    def __repr__(self):
        return self.get()[1]
