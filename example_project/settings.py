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
Example project settings.
"""

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('admin', 'root@localhost'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = 'database.db'
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''
DATABASE_PORT = ''

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '3al0c)ht(-9y-%lhom-innp5k@ujv3!h9w3m5vn-x^e*wuj5c4'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_error_capture_middleware.ErrorCaptureMiddleware',
)

ROOT_URLCONF = 'urls'

import os.path
TEMPLATE_DIRS = (
    os.path.sep.join(__file__.split(os.path.sep)[:-1] + ['templates']),
)

ERROR_CAPTURE_ENABLE_MULTPROCESS = True
ERROR_CAPTURE_HANDLERS = (
#    'django_error_capture_middleware.handlers.github.GitHubHandler',
#    'django_error_capture_middleware.handlers.email.EmailHandler',
    ('django_error_capture_middleware.handlers.'
        'simple_ticket.SimpleTicketHandler'),
#    'django_error_capture_middleware.handlers.google_code.GoogleCodeHandler',
#    'django_error_capture_middleware.handlers.bz.BugzillaHandler',
)


# regular expressions to block
#ERROR_CAPTURE_TRACE_CONTENT_BLACKLIST = (
#)

# (ACTUAL) classes to blacklist
#ERROR_CAPTURE_TRACE_CLASS_BLACKLIST = (
#)

ERROR_CAPTURE_GITHUB_REPO = ''
ERROR_CAPTURE_GITHUB_TOKEN = ''
ERROR_CAPTURE_GITHUB_LOGIN = ''

ERROR_CAPTURE_GOOGLE_CODE_PROJECT = ''
ERROR_CAPTURE_GOOGLE_CODE_LOGIN = ''
ERROR_CAPTURE_GOOGLE_CODE_PASSWORD = ''
ERROR_CAPTURE_GOOGLE_CODE_TYPE = ''

ERROR_CAPTURE_GOOGLE_BUGZILLA_SERVICE = ''
ERROR_CAPTURE_GOOGLE_BUGZILLA_USERNAME = ''
ERROR_CAPTURE_GOOGLE_BUGZILLA_PASSWORD = ''
ERROR_CAPTURE_GOOGLE_BUGZILLA_PRODUCT = ''
ERROR_CAPTURE_GOOGLE_BUGZILLA_COMPONENT = ''
ERROR_CAPTURE_GOOGLE_BUGZILLA_VERSION = ''
ERROR_CAPTURE_GOOGLE_BUGZILLA_PLATFORM = ''
ERROR_CAPTURE_GOOGLE_BUGZILLA_SEVERITY = ''
ERROR_CAPTURE_GOOGLE_BUGZILLA_OS = ''
ERROR_CAPTURE_GOOGLE_BUGZILLA_LOC = ''
ERROR_CAPTURE_GOOGLE_BUGZILLA_PRIORITY = ''


ERROR_CAPTURE_NOOP_ON_DEBUG = False

SERVER_EMAIL = 'me@localhost'
ERROR_CAPTURE_EMAIL_FAIL_SILENTLY = False
ERROR_CAPTURE_IGNORE_DUPE_SEC = False

import sys
sys.path.insert(0, '../src/')

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django_error_capture_middleware',
)
