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


import re
import time
import sys
import traceback

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from django.conf import settings
from django import http
from django.test import TestCase, client
from django.test.client import Client

from minimock import Mock

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

    def test_process_exception(self):
        """
        Tests processing of exceptions.
        """
        # Getting a 404 should raise it back
        self.assertRaises(http.Http404, self.instance.process_exception,
            None, http.Http404())

        # Test class blacklist
        exc = self._raise_and_get_exception()
        settings.ERROR_CAPTURE_TRACE_CLASS_BLACKLIST = (type(Exception), )
        self.assertRaises(
            Exception, self.instance.process_exception, None, exc)
        settings.ERROR_CAPTURE_TRACE_CLASS_BLACKLIST = tuple()

        # Test content blacklist
        settings.ERROR_CAPTURE_TRACE_CONTENT_BLACKLIST = (
            re.compile('.*test.*'), )
        self.assertRaises(
            Exception, self.instance.process_exception, None, exc)
        settings.ERROR_CAPTURE_TRACE_CONTENT_BLACKLIST = tuple()


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
        # Setup the mock
        send_mail = Mock('send_mail', returns=True, tracker=None)

        settings.ERROR_CAPTURE_ADMINS = 'user@localhost'
        settings.ERROR_CAPTURE_EMAIL_FAIL_SILENT = False
        super(EmailHandlerTestCase, self).setUp()
        self.instance.send_mail = send_mail


class GitHubHandlerTestCase(_ParentTicketHandlerMixIn, TestCasePlus):
    """
    Tests for GitHub handler.
    """

    test_cls = github.GitHubHandler

    def setUp(self):
        """
        Adds required temporary setting for the test.
        """
        # Setup the mock
        response = StringIO('issue:\n    number: 123')
        urllib = Mock('urllib', tracker=None)
        urllib.urlopen = Mock('urllib.urlopen', returns=response, tracker=None)

        settings.ERROR_CAPTURE_GITHUB_REPO = 'fake_repo'
        settings.ERROR_CAPTURE_GITHUB_TOKEN = 'fake_token'
        settings.ERROR_CAPTURE_GITHUB_LOGIN = 'fake_login'
        super(GitHubHandlerTestCase, self).setUp()
        self.instance.urllib = urllib


class GoogleCodeHandlerTestCase(_ParentTicketHandlerMixIn, TestCasePlus):
    """
    Tests for Google Code handler.
    """

    test_cls = google_code.GoogleCodeHandler

    def setUp(self):
        """
        Adds required temporary setting for the test.
        """
        # Setup the mock
        result_impl = Mock('result_impl', tracker=None)
        result_impl.find_html_link = Mock('find_html_link',
            returns='http://www.example.dom/123/?id=123', tracker=None)
        client_impl = Mock('gdata.projecthosting.client', tracker=None)
        client_impl.add_issue = Mock(
            'add_issue', returns=result_impl, tracker=None)
        client_impl.client_login = Mock(
            'client_login', returns=True, tracker=None)
        gdata_client = Mock(
            'ProjectHostingClient', returns=client_impl, tracker=None)

        settings.ERROR_CAPTURE_GOOGLE_CODE_PROJECT = 'fake_project'
        settings.ERROR_CAPTURE_GOOGLE_CODE_LOGIN = 'fake_login'
        settings.ERROR_CAPTURE_GOOGLE_CODE_PASSWORD = 'fake_password'
        settings.ERROR_CAPTURE_GOOGLE_CODE_TYPE = 'fake_type'
        super(GoogleCodeHandlerTestCase, self).setUp()
        self.instance.gdata.projecthosting.client.ProjectHostingClient = (
            gdata_client)


class BugzillaHandlerTestCase(_ParentTicketHandlerMixIn, TestCasePlus):
    """
    Tests for Google Code handler.
    """

    test_cls = bz.BugzillaHandler

    def setUp(self):
        """
        Adds required temporary setting for the test.
        """
        # Setup the mock
        BzImpl = Mock('bz.Bugzilla', tracker=None)
        BzImpl.createbug = Mock('BzImpl.createbug',
            returns=Jelly(bug_id=123, url='http'), tracker=None)
        Bugzilla = Mock('bz.Bugzilla', returns=BzImpl, tracker=None)

        settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_SERVICE = 'http://example.com/'
        settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_USERNAME = 'fake_user'
        settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_PASSWORD = 'fake_password'
        settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_PRODUCT = 'fake_product'
        settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_COMPONENT = 'fake_component'
        settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_VERSION = 'fake_version'
        settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_PLATFORM = 'fake_platform'
        settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_SEVERITY = 'fake_severity'
        settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_OS = 'fake_os'
        settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_LOC = 'fake_loc'
        settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_PRIORITY = 'fake_priority'
        super(BugzillaHandlerTestCase, self).setUp()
        self.instance.Bugzilla = Bugzilla
