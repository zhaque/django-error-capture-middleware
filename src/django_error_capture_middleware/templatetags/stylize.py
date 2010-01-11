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
Tags.
"""

__docformat__ = 'restructuredtext'


from django.template import Library, Node, resolve_variable
from django.template import mark_safe

register = Library()


class _StylizeNodeParent(Node):
    """
    Parent Stylize node class.
    """

    def __init__(self, nodelist, *varlist):
        """
        Creates an instance of a stylize node.
        """
        self.nodelist, self.vlist = (nodelist, varlist)


# Try to import and use pygments ...
try:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name
    from pygments.formatters import HtmlFormatter

    class StylizeNode(_StylizeNodeParent):
        """
        Pygments tag renderer.
        """

        def render(self, context):
            """
            Creates a renderable safe string for the tag.

            :Parameters:
               - `context`: current context information
            """
            style = 'text'
            if len(self.vlist) > 0:
                style = resolve_variable(self.vlist[0], context)
            result = "<style>%s</style>" % HtmlFormatter().get_style_defs(
                '.highlight')
            result += highlight(self.nodelist.render(context),
                get_lexer_by_name(
                    style, encoding='UTF-8'), HtmlFormatter())
            return mark_safe(result)

# Fail down to <pre> tags if we can't use pyugments.
except ImportError:

    class StylizeNode(_StylizeNodeParent):
        """
        Pre tag renderer.
        """

        def render(self, context):
            """
            Creates a renderable safe string for the tag.

            :Parameters:
               - `context`: current context information
            """
            style = 'text'
            if len(self.vlist) > 0:
                style = resolve_variable(self.vlist[0], context)
            result = "<pre>" + str(self.nodelist.render(context)) + "</pre>"
            return mark_safe(result)


def stylize(parser, token):
    """
    Actual tag function.

    :Parameters:
       - parser: template parser
       - token: token to map to the variable list
    """
    nodelist = parser.parse(('endstylize',))
    parser.delete_first_token()
    return StylizeNode(nodelist, *token.contents.split()[1:])


# Register the tag
stylize = register.tag(stylize)
