# Copyright 2022 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Custom HTML translator for Firesite reference docs."""

from sphinx.writers import html

_DESCTYPE_NAMES = {
    "class": "Classes",
    "data": "Constants",
    "function": "Functions",
    "method": "Methods",
    "attribute": "Attributes",
    "exception": "Exceptions",
}

# Use the default translator for these node types
_RENDER_WITH_DEFAULT = ["method", "staticmethod", "attribute"]


class FiresiteHTMLTranslator(html.HTMLTranslator):
    """Custom HTML translator that produces output suitable for Firesite.

    - Inserts H2 tags around object signatures
    - Uses tables instead of DLs
    - Inserts hidden H3 elements for right-side nav
    - Surrounds notes and warnings with <aside> tags
    """

    def __init__(self, builder, *args, **kwds):
        html.HTMLTranslator.__init__(self, builder, *args, **kwds)
        self.current_section = "intro"

        # This flag gets set to True at the start of a new 'section' tag, and then
        # back to False after the first object signature in the section is processed
        self.insert_header = False

    def visit_desc(self, node):
        if node.parent.tagname == "section":
            self.insert_header = True
            if node["desctype"] != self.current_section:
                self.body.append(f"<h2>{_DESCTYPE_NAMES[node['desctype']]}</h2>")
                self.current_section = node["desctype"]
        if node["desctype"] in _RENDER_WITH_DEFAULT:
            html.HTMLTranslator.visit_desc(self, node)
        else:
            self.body.append(self.starttag(node, "table", CLASS=node["objtype"]))

    def depart_desc(self, node):
        if node["desctype"] in _RENDER_WITH_DEFAULT:
            html.HTMLTranslator.depart_desc(self, node)
        else:
            self.body.append("</table>\n\n")

    def visit_desc_signature(self, node):
        if node.parent["desctype"] in _RENDER_WITH_DEFAULT:
            html.HTMLTranslator.visit_desc_signature(self, node)
        else:
            self.body.append("<tr>")
            self.body.append(self.starttag(node, "th"))
            if self.insert_header:
                self.body.append(f'<h3 class="sphinx-hidden">{node["fullname"]}</h3>')
                self.insert_header = False

    def depart_desc_signature(self, node):
        if node.parent["desctype"] in _RENDER_WITH_DEFAULT:
            html.HTMLTranslator.depart_desc_signature(self, node)
        else:
            self.body.append("</th></tr>")

    def visit_desc_content(self, node):
        if node.parent["desctype"] in _RENDER_WITH_DEFAULT:
            html.HTMLTranslator.visit_desc_content(self, node)
        else:
            self.body.append("<tr>")
            self.body.append(self.starttag(node, "td"))

    def depart_desc_content(self, node):
        if node.parent["desctype"] in _RENDER_WITH_DEFAULT:
            html.HTMLTranslator.depart_desc_content(self, node)
        else:
            self.body.append("</td></tr>")

    def visit_title(self, node):
        if node.parent.tagname == "section":
            self.body.append('<h1 class="page-title">')
        else:
            html.HTMLTranslator.visit_title(self, node)

    def depart_title(self, node):
        if node.parent.tagname == "section":
            self.body.append("</h1>")
        else:
            html.HTMLTranslator.depart_title(self, node)

    def visit_note(self, node):
        self.body.append(self.starttag(node, "aside", CLASS="note"))

    def depart_note(self, node):
        # pylint: disable=unused-argument
        self.body.append("</aside>\n\n")

    def visit_warning(self, node):
        self.body.append(self.starttag(node, "aside", CLASS="caution"))

    def depart_warning(self, node):
        # pylint: disable=unused-argument
        self.body.append("</aside>\n\n")
