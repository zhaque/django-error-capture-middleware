#!/usr/bin/env python
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
Standard build script.
"""

__docformat__ = 'restructuredtext'

import os.path
import sys

from setuptools import setup, find_packages, findall, Command

sys.path.insert(0, 'src')

#from example_project.manage import execute_manager, settings


class TestCommand(Command):
    """
    Execute Django unittests.
    """

    description = __doc__[1:-1]

    # Required but unused items.
    user_options = []
    initialize_options = finalize_options = lambda s: None

    def run(self):
        """
        Execute the unittests and run coverage if available.
        """
        try:
            import coverage
            cov = coverage.coverage()
            cov.start()
        except ImportError:
            coverage = None
        execute_manager(settings)
        if coverage:
            cov.stop()
            cov.report(show_missing=False,
                omit_prefixes=[os.path.sep + 'usr',
                os.path.expanduser('~' + os.path.sep + '.local')])


setup(
    name="django_error_capture_middleware",
    version='0.0.1',
    description="sends tracebacks in Django to bugtrackers or services",
    long_description=("Middleware for the Django framework that allows you "
        "to send tracebacks to bugtrackers or other services through the use "
        "of handlers. Helpful for keeping track of issues and avoiding the "
        "flood of error emails that most frameworks default with."),
    author="Steve 'Ashcrow' Milner",
    author_email='stevem@gnulinux.net',
    url="http://bitbucket.org/ashcrow/django-error-capture-middleware/",
    download_url=("http://bitbucket.org/ashcrow/"
        "django-error-capture-middleware/downloads/"),

    license="New BSD",

    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    # Add in all the template data using a bit of map/finall magic
    package_data={
        'django_error_capture_middleware': map(lambda s: s[36:],
            findall(os.path.sep.join(
                ['src', 'django_error_capture_middleware', 'templates']))),
    },

    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Programming Language :: Python',
    ],
#    cmdclass={
#        'test': TestCommand,
#    },
)
