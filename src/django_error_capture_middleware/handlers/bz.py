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


#from bugzilla import Bugzilla

from django.conf import settings
from django.template import loader

from django_error_capture_middleware import ErrorCaptureHandler


class BugzillaHandler(ErrorCaptureHandler):
    """
    Bugzilla handler.
    """

    from bugzilla import Bugzilla
    required_settings = [
        'ERROR_CAPTURE_GOOGLE_BUGZILLA_SERVICE',
        'ERROR_CAPTURE_GOOGLE_BUGZILLA_USERNAME',
        'ERROR_CAPTURE_GOOGLE_BUGZILLA_PASSWORD',
        'ERROR_CAPTURE_GOOGLE_BUGZILLA_PRODUCT',
        'ERROR_CAPTURE_GOOGLE_BUGZILLA_COMPONENT',
        'ERROR_CAPTURE_GOOGLE_BUGZILLA_VERSION',
        'ERROR_CAPTURE_GOOGLE_BUGZILLA_PLATFORM',
        'ERROR_CAPTURE_GOOGLE_BUGZILLA_SEVERITY',
        'ERROR_CAPTURE_GOOGLE_BUGZILLA_OS',
        'ERROR_CAPTURE_GOOGLE_BUGZILLA_LOC',
        'ERROR_CAPTURE_GOOGLE_BUGZILLA_PRIORITY',
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
            bz = self.Bugzilla(
                url=settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_SERVICE)
            bz.login(settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_USERNAME,
                settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_PASSWORD)
            # Setup the templates
            title_tpl = loader.get_template(
                'django_error_capture_middleware/bugzilla/title.txt')
            body_tpl = loader.get_template(
                'django_error_capture_middleware/bugzilla/body.txt')
            # Add the issue
            bug = bz.createbug(
                product=settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_PRODUCT,
                component=settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_COMPONENT,
                version=settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_VERSION,
                short_desc=str(title_tpl.render(self.context)),
                comment=str(body_tpl.render(self.context)),
                rep_platform=settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_PLATFORM,
                bug_severity=settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_SEVERITY,
                op_sys=settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_OS,
                bug_file_loc=settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_LOC,
                priority=settings.ERROR_CAPTURE_GOOGLE_BUGZILLA_PRIORITY)
            # pull the data we want out and throw it in the queue
            queue.put_nowait(bug.bug_id)

        # Execute the background call.
        queue, process = self.background_call(get_data)
        self.context['id'] = self.get_data(queue)
