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
Views for the SimpleTicketHandler
"""

__docformat__ = 'restructuredtext'


from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User
from django.core.serializers import serialize
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.template import mark_safe
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter

from django_error_capture_middleware.models import Error


@permission_required('error.view_error')
def list(request):
    """
    Lists all tickets.
    """
    errors = Error.objects.all()
    return render_to_response(
        'django_error_capture_middleware/simpleticket/list.html', locals())


@permission_required('error.view_error')
def user_list(request, name):
    """
    Lists all *my* tickets.
    """
    errors = Error.objects.filter(owner=get_object_or_404(User, username=name))
    return render_to_response(
        'django_error_capture_middleware/simpleticket/list.html', locals())


@permission_required('error.view_error')
def ticket(request, id):
    """
    Shows a specific ticket.
    """
    error = get_object_or_404(Error, id=id)
    return render_to_response(
        'django_error_capture_middleware/simpleticket/ticket.html', locals())


@permission_required('error.change_error')
@permission_required('error.view_error')
def take_ticket(request, id):
    """
    Takes ownership of a specific ticket.
    """
    error = get_object_or_404(Error, id=id)
    error.owner = request.user
    error.save()
    return HttpResponse(serialize('json', [error]), mimetype="text/json")


@permission_required('error.change_error')
@permission_required('error.view_error')
def resolve_ticket(request, id):
    """
    Resolves or unresolves a specific ticket.
    """
    error = get_object_or_404(Error, id=id)
    if error.resolved:
        error.resolved = False
    else:
        error.resolved = True
    error.save()
    return HttpResponse(serialize('json', [error]), mimetype="text/json")
