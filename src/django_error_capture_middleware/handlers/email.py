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


from django.conf import settings
from django.template import loader

from django_error_capture_middleware import ErrorCaptureHandler


class EmailHandler(ErrorCaptureHandler):
    """
    Replacement email handler.
    """

    from django.core.mail import send_mail

    required_settings = ['ERROR_CAPTURE_ADMINS',
        'ERROR_CAPTURE_EMAIL_FAIL_SILENTLY']

    def handle(self, request, exception, tb):
        """
        Turns the resulting traceback into something emailed back to admins.

        :Parameters:
           - `request`: request causing the exception
           - `exception`: actual exception raised
           - `tb`: traceback string
        """

        def get_data(context, queue, send_mail):
            subject_tpl = loader.get_template(
                'django_error_capture_middleware/email/subject.txt')
            body_tpl = loader.get_template(
                'django_error_capture_middleware/email/body.txt')
            # The render function appends a \n character at the end. Subjects
            # can't have newlines.
            subject = subject_tpl.render(context).replace('\n', '')
            body = body_tpl.render(context)

            try:
                subject = settings.EMAIL_SUBJECT_PREFIX + subject
            except:
                pass

            try:
                from_email = settings.SERVER_EMAIL
            except AttributeError, e:
                from_email = None

            datatuple = (subject, body, from_email,
                    settings.ERROR_CAPTURE_ADMINS)

            send_mail(subject, body, from_email, settings.ERROR_CAPTURE_ADMINS,
                fail_silently=settings.ERROR_CAPTURE_EMAIL_FAIL_SILENTLY)

        queue, process = self.background_call(get_data,
            kwargs={'context': self.context, 'send_mail': self.send_mail})
