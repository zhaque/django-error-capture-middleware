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
Unittests.
"""

__docformat__ = 'restructuredtext'


import time
import sys
import traceback

from django.conf import settings
from django.test import TestCase, client
from django.test.client import Client

from django_error_capture_middleware import (ErrorCaptureMiddleware,
    ErrorCaptureHandler, threading, thread_cls, Queue, queue_mod)

from django_error_capture_middleware.handlers import (
    bz, email, github, simple_ticket, google_code)


class Jelly(object):
    """
    Simple moldable class.
    """

    def __init__(self, **kwargs):
        """
        Creates an instance of jelly.

        :Parameters:
           - `kwargs`: keyward arguments to turn into variables.
        """
        for key in kwargs:
            setattr(self, key, kwargs[key])


class TestCasePlus(TestCase):
    """
    TestCase with functionality that helps aid in our testing. All tests
    should subclass this directly or indirectly.
    """

    client = Client()

    def _raise_and_get_exception(self, data="test", exception=Exception):
        """
        Raises, captures and returns an exception and it's traceback.

        :Parameters:
           - `data`: text to be in the exception message. Defaults to 'test'.
           - `exception`: exception class to raise. Defaults to Exception.
        """
        try:
            raise exception(data)
        except Exception, ex:
            tb = traceback.format_exception(*sys.exc_info())
            return ex, tb


class ErrorCaptureMiddlewareTestCase(TestCasePlus):
    """
    Tests for the middleware.
    """

    def setUp(self):
        """
        How to start up each test.
        """
        self.instance = ErrorCaptureMiddleware()

    def tearDown(self):
        """
        How to end each test.
        """
        del self.instance

    def test_structure(self):
        """
        Verifies the object is created in the way expected.
        """
        self.assertEquals(self.instance.traceback, traceback)
        self.assertTrue(hasattr(self.instance, 'process_exception'))


class _ParentTicketHandlerMixIn(object):
    """
    Parent class for all handlers.
    """

    test_cls = None
    dummy_request = Jelly(user=None, META={}, GET={}, POST={})

    def setUp(self):
        """
        How to start up each test.
        """
        self.instance = self.test_cls()

    def tearDown(self):
        """
        How to end each test.
        """
        del self.instance

    def test_structure(self):
        """
        Verifies the object is created in the way expected.
        """
        self.assertEquals(self.instance.traceback, traceback)
        self.assertTrue(hasattr(self.instance, 'handle'))
        self.assertTrue(hasattr(self.instance, 'background_call'))
        self.assertTrue(hasattr(self.instance, '__call__'))

    def test_handle(self):
        """
        Verify the handle method works as it should.
        """
        ex, tb = self._raise_and_get_exception()
        result = self.instance.handle(self.dummy_request, ex, tb)
        # We should not get a return from the handler.
        self.assertEquals(result, None)

    def test__call__(self):
        """
        Tests the __call__ functionality.
        """
        ex = self._raise_and_get_exception()
        original_debug = settings.DEBUG
        result = self.instance(self.dummy_request, ex, sys.exc_info())
        self.assertEquals(result.status_code, 500)

    def test_simple_background_call(self):
        """
        Tests the ability to do simple background calls.
        """

        def simple(queue):
            queue.put_nowait('simple')

        queue, prc = self.instance.background_call(simple)
        self.assertTrue(isinstance(queue, queue_mod.Queue))
        if settings.ERROR_CAPTURE_ENABLE_MULTPROCESS:
            self.assertTrue(isinstance(prc, thread_cls))
        self.assertEquals(queue.get(), 'simple')

    def test_background_call(self):
        """
        Tests the ability to do a background calls.
        """

        def less_simple(data, to, queue, append="append"):
            queue.put_nowait(" ".join([data, to, append]))

        queue, prc = self.instance.background_call(
            less_simple, ('data', ), {'to': 'to'})
        self.assertTrue(isinstance(queue, queue_mod.Queue))
        if settings.ERROR_CAPTURE_ENABLE_MULTPROCESS:
            self.assertTrue(isinstance(prc, thread_cls))
        self.assertEquals(queue.get(), "data to append")

        queue, prc = self.instance.background_call(
            less_simple, ('data', ), {'to': 'to'})

        # We wait a bit to make sure we get the data in the test
        time.sleep(0.05)
        result = self.instance.get_data(queue)
        self.assertEquals(result, "data to append")

        def raise_ex(queue):
            raise Exception('test')

        queue, process = self.instance.background_call(raise_ex)
        # Again, we wait a bit to make sure we get the data in the test
        time.sleep(0.05)
        self.assertRaises(Exception, self.instance.get_data, queue)


class ErrorCaptureHandlerTestCase(_ParentTicketHandlerMixIn, TestCasePlus):
    """
    Tests for the handler parent class.
    """

    test_cls = ErrorCaptureHandler

    def test_handle(self):
        """
        Verify the handle method works as it should.
        """
        ex, tb = self._raise_and_get_exception()
        self.assertRaises(
            NotImplementedError, self.instance.handle,
            self.dummy_request, ex, tb)

    def test__call__(self):
        """
        Tests the __call__ functionality.
        """
        ex, tb = self._raise_and_get_exception()
        original_debug = settings.DEBUG
        self.assertRaises(
            NotImplementedError, self.instance.__call__,
            self.dummy_request, ex, sys.exc_info())
        settings.DEBUG = False


class SimpleTicketHandlerTestCase(_ParentTicketHandlerMixIn, TestCasePlus):
    """
    Tests for Simple Ticket handler.
    """

    test_cls = simple_ticket.SimpleTicketHandler


class EmailHandlerTestCase(_ParentTicketHandlerMixIn, TestCasePlus):
    """
    Tests for Email handler.
    """

    test_cls = email.EmailHandler

    def setUp(self):
        """
        Adds required temporary setting for the test. We are testing
        with fail silent since we are testing the handler and not
        the ability of the system to send email.
        """
        settings.ERROR_CAPTURE_ADMINS = tuple('user@localhost')
        settings.ERROR_CAPTURE_EMAIL_FAIL_SILENT = True
        super(EmailHandlerTestCase, self).setUp()


class GitHubHandlerTestCase(_ParentTicketHandlerMixIn, TestCasePlus):
    """
    Tests for GitHub handler.

    TODO: flesh this test out more.
    """

    test_cls = github.GitHubHandler

    def setUp(self):
        """
        Adds required temporary setting for the test.
        """
        settings.ERROR_CAPTURE_GITHUB_REPO = ''
        settings.ERROR_CAPTURE_GITHUB_TOKEN = ''
        settings.ERROR_CAPTURE_GITHUB_LOGIN = ''
        super(GitHubHandlerTestCase, self).setUp()


class GoogleCodeHandlerTestCase(_ParentTicketHandlerMixIn, TestCasePlus):
    """
    Tests for Google Code handler.

    TODO: flesh this test out more.
    """

    test_cls = google_code.GoogleCodeHandler

    def setUp(self):
        """
        Adds required temporary setting for the test.
        """
        settings.ERROR_CAPTURE_GOOGLE_CODE_PROJECT = ''
        settings.ERROR_CAPTURE_GOOGLE_CODE_LOGIN = ''
        settings.ERROR_CAPTURE_GOOGLE_CODE_PASSWORD = ''
        settings.ERROR_CAPTURE_GOOGLE_CODE_TYPE = ''
        super(GoogleCodeHandlerTestCase, self).setUp()


class BugzillaHandlerTestCase(_ParentTicketHandlerMixIn, TestCasePlus):
    """
    Tests for Google Code handler.

    TODO: flesh this test out more.
    """

    test_cls = bz.BugzillaHandler

    def setUp(self):
        """
        Adds required temporary setting for the test.
        """
        settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_SERVICE = 'http://example.com/'
        settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_USERNAME = ''
        settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_PASSWORD = ''
        settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_PRODUCT = ''
        settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_COMPONENT = ''
        settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_VERSION = ''
        settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_PLATFORM = ''
        settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_SEVERITY = ''
        settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_OS = ''
        settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_LOC = ''
        settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_PRIORITY = ''
        super(BugzillaHandlerTestCase, self).setUp()
