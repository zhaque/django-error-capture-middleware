# Copyright (c) 2009-2010, Steve 'Ashcrow' Milner
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials
#      provided with the distribution.
#    * Neither the name of the project nor the names of its
#      contributors may be used to endorse or promote products
#      derived from this software without specific prior written
#      permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.
"""
Error caprture middleware and default application.
"""

__docformat__ = 'restructuredtext'


try:
    from hashlib import sha1
except ImportError, e:
    import sha as sha1

import platform
import Queue
import socket
import sys

from django import http
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseServerError
from django.views import debug
from django.template import Context, loader

# Imports based on version
if platform.python_version() >= '2.6.0':
    threading = __import__('multiprocessing')
    thread_cls = threading.Process
    queue_mod = __import__('multiprocessing.queues', fromlist=[True])
else:
    threading = __import__('threading')
    thread_cls = threading.Thread
    queue_mod = __import__('Queue')


def exception_wrapper(func):
    """
    Wraps a method so that raised exception are returned
    instead of raising.
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception, ex:
            kwargs['queue'].put_nowait(ex)

    return wrapper


class ErrorCaptureMiddleware(object):
    """
    Middleware to capture exceptins and create a ticket/bug for it.
    """
    traceback = __import__('traceback')

    def process_exception(self, request, exception):
        """
        Process the exception.

        :Parameters:
           - `request`: request that caused the exception
           - `exception`: actual exception being raised
        """
        # If this is a 404 ...
        if isinstance(exception, http.Http404):
            raise exception

        # Snag the trace content since we will use it from here forward
        trace_content = self.traceback.format_exc()

        # If the type is blacklisted ...
        if getattr(settings, 'ERROR_CAPTURE_TRACE_CLASS_BLACKLIST', None):
            for ex in settings.ERROR_CAPTURE_TRACE_CLASS_BLACKLIST:
                if ex == type(exception):
                    raise exception
        # If we match the traceback content in a regular expression ...
        # Note that we import re in this scope so we only import if used
        elif getattr(settings, 'ERROR_CAPTURE_TRACE_CONTENT_BLACKLIST', None):
            import re
            for rx in settings.ERROR_CAPTURE_TRACE_CONTENT_BLACKLIST:
                try:
                    re.search(rx, trace_content).groups()
                    raise exception
                except AttributeError:
                    # didn't match
                    pass

        # If we get to this point, we will be processing the exception.
        exc_info = sys.exc_info()
        if settings.DEBUG and settings.ERROR_CAPTURE_NOOP_ON_DEBUG:
            return debug.technical_500_response(request, *exc_info)

        # generate a hash for this exception
        hash = sha1()
        hash.update(trace_content)
        exc_hash = hash.hexdigest()

        # check the cache to see if we have already handled it
        if cache.get(exc_hash) is not None:
            return

        cache.set(exc_hash, self.traceback.format_exc(),
                int(settings.ERROR_CAPTURE_IGNORE_DUPE_SEC))

        handler_count = len(settings.ERROR_CAPTURE_HANDLERS)
        count = 0
        for handler in settings.ERROR_CAPTURE_HANDLERS:
            module = '.'.join(handler.split('.')[:-1])
            cls = handler.split('.')[-1]
            handler_obj = getattr(__import__(module, fromlist=[True]), cls)
            count += 1
            func = handler_obj()
            if (settings.ERROR_CAPTURE_ENABLE_MULTPROCESS
                and count < handler_count):
                a_process = thread_cls(
                    target=func, args=(request, exception, exc_info))
                #a_process.daemon = True
                a_process.start()
            else:
                result = func(request, exception, sys.exc_info())
            # If it is the last item, then it will be what we return.
            if count >= handler_count:
                return result


class ErrorCaptureHandler(object):
    """
    Parent class for creating a handler.
    """

    __slots__ = ['traceback', 'required_settings', 'context']

    traceback = __import__('traceback')
    required_settings = []

    def __init__(self):
        """
        Creates an instance of this class.
        """
        for required_setting in self.required_settings:
            if not hasattr(settings, required_setting):
                raise ImproperlyConfigured('You must define the following ' +
                    'in your settings' +
                    ', '.join(self.required_settings)[:-2])
        # Create an empty context for use later.
        self.context = Context()

    def handle(self, request, exception, tb):
        """
        Must be defined in a subclass. Takes care of processing the
        exception.

        :Parameters:
           - `request`: request causing the exception
           - `exception`: actual exception raised
           - `tb`: traceback string
        """
        raise NotImplementedError('You must define handle')

    def background_call(self, callback, args=(), kwargs={}):
        """
        Provides a simple interface for doing background processing.
        An object providing a get method is returned along with the
        process or thread object.

        :Parameters:
           - `callback`: callable to execute
           - `args`: non-keyword arguments to pass to callback
           - `kwargs`: keyword arguments to pass to callback
        """
        a_queue = queue_mod.Queue()
        callback_wrapped = exception_wrapper(callback)
        kwargs.update({'queue': a_queue})
        if settings.ERROR_CAPTURE_ENABLE_MULTPROCESS:
            a_process = thread_cls(
                target=callback_wrapped, args=args, kwargs=kwargs)
            a_process.daemon = True
            a_process.start()
        else:
            a_process = callback_wrapped(*args, **kwargs)
        return a_queue, a_process

    def get_data(self, queue):
        """
        Gets the data from a queue or raises the proper exception if
        one exists.

        :Parameters:
           - `queue`: queue instance to use
        """
        try:
            data = queue.get_nowait()
        except Queue.Empty:
            return None
        if issubclass(Exception, data.__class__):
            raise data
        return data

    def __call__(self, request, exception, exc_info):
        """
        Actually gets called from the middleware and takes care of
        adding in the traceback information.

        :Parameters:
           - `request`: request causing the exception
           - `exception`: actual exception raised
           - `exc_info`: info from sys.exc_info
        """
        tb = self.traceback.format_exception(*exc_info)
        data = {'traceback': tb}
        data.update(request.META)
        data["GET"] = request.GET
        data["POST"] = request.POST
        data["SERVER_HOSTNAME"] = socket.gethostname()
        self.context.update(data)
        self.handle(request, exception, tb)

        if settings.DEBUG:
            return debug.technical_500_response(request, *exc_info)

        return HttpResponseServerError(
            loader.get_template('500.html').render(self.context))
