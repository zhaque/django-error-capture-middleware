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
Super simple ticket handler that uses the admin interface.
"""

__docformat__ = 'restructuredtext'


import gdata.projecthosting.client

from django.conf import settings
from django.template import loader

from django_error_capture_middleware import ErrorCaptureHandler


class GoogleCodeHandler(ErrorCaptureHandler):
    """
    Google Code handler.
    """

    required_settings = [
        'ERROR_CAPTURE_GOOGLE_CODE_PROJECT',
        'ERROR_CAPTURE_GOOGLE_CODE_PASSWORD',
        'ERROR_CAPTURE_GOOGLE_CODE_LOGIN',
        'ERROR_CAPTURE_GOOGLE_CODE_TYPE',
    ]

    def handle(self, request, exception, tb):
        """
        Pushes the traceback to a github ticket system.

        :Parameters:
           - `request`: request causing the exception
           - `exception`: actual exception raised
           - `tb`: traceback string
        """

        def get_data(queue):
            # Create a client and login
            client = gdata.projecthosting.client.ProjectHostingClient()
            client.client_login(
                settings.ERROR_CAPTURE_GOOGLE_CODE_LOGIN,
                settings.ERROR_CAPTURE_GOOGLE_CODE_PASSWORD,
                source='error-capture-middleware',
                service='code',
            )
            # Setup the templates
            title_tpl = loader.get_template(
                'django_error_capture_middleware/googlecode/title.txt')
            body_tpl = loader.get_template(
                'django_error_capture_middleware/googlecode/body.txt')
            # Add the issue
            result = client.add_issue(
                settings.ERROR_CAPTURE_GOOGLE_CODE_PROJECT,
                title_tpl.render(self.context),
                body_tpl.render(self.context),
                settings.ERROR_CAPTURE_GOOGLE_CODE_LOGIN, 'open',
                labels=[settings.ERROR_CAPTURE_GOOGLE_CODE_TYPE])
            # pull the data we want out and throw it in the queue
            issue_url = result.find_html_link()
            id = issue_url.rpartition('=')[-1]
            queue.put_nowait([id, issue_url])

        # Execute the background call.
        queue, process = self.background_call(get_data)
        try:
            # Get the results
            self.context['id'], self.context['bug_url'] = self.get_data(queue)
        except TypeError:
            # If we get None we can't split ... sadly it seems that
            # it's very rare to get a fast enough response back.
            pass
