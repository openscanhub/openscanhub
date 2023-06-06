# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.
"""
Set of test cases to help with the OpenScanHub unit testing.

A short summary of test cases provided by this module:

* :class:`.OshTestCase` -- a base class of (almost) all test cases and test
  suites.
"""

from django.test import TestCase
from django.test.html import parse_html as django_parse_html

from osh.testing.html import (extract_links, extract_text,
                              get_child_by_tag_name, normalize_attributes,
                              parse_html)


class OshTestCase(TestCase):
    """
    A base class of OpenScanHub test cases and test suites.

    This class extends the Django's :class:`~django.test.TestCase` about
    following features:

    * Enhanced ways of views verification. A content rendered from templates
      can be tested for the requested structure and appearance. Links can be
      validated if they refer to the expected location (only links with static
      URLs that are rendered directly into HTML code; for more complex user
      interface interactions the :mod:`selenium` framework need to be enabled).
    """

    def setUp(self):
        """Set up the test."""
        super().setUp()
        # Disable diff clipping so we can see entire diffs
        self.maxDiff = None

    def assertInParsedHTML(self, snippet, element):
        """
        Assert that HTML snippet is a part of element.

        :param snippet: The HTML code snippet
        :param element: The HTML DOM element
        :raises AssertionError: when snippet is not a part of element

        First parse the snippet to get its DOM object and then check whether
        this object is included in the element.
        """
        parsed = django_parse_html(snippet)
        self.assertGreater(element.count(parsed), 0)

    def verify_html_title(self, document, text):
        """
        Verify that the text is a part of the document title.

        :param document: The parsed HTML document
        :param text: The text
        :raises AssertionError: when text is not a part of the document title
        """
        title = get_child_by_tag_name(document.head, "title")
        self.assertIn(text, title.children[0])

    def verify_html_link(self, link, text):
        """
        Verify that the HTML link is working.

        :param link: The HTML link DOM object
        :param text: The text that should be a part of the title of the
            document which the link refers to
        :raises AssertionError: when the status code of the response is not 200
            or the text is not included in the requested document title
        """
        response = self.client.get(dict(link.attributes)["href"], follow=True)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode(encoding=response.charset)

        self.verify_html_title(parse_html(content), text)

    def verify_change_links(self, html):
        """
        Verify that *change links* from HTML snippet are working.

        :param html: The HTML code snippet
        :raises AssertionError: when some of links is not working or is not
            referring to the *Change ...* page

        First, links are extracted from the provided HTML code snippet. Then
        every link is tested if its URL refers to the *Change ...* page (these
        pages contain ``Change `` in their titles).
        """
        parsed = django_parse_html(html)
        for link in extract_links(parsed):
            self.verify_html_link(link, "Change ")

    def verify_body_class(self, document, class_attribute_value):
        """
        Verify that ``<body ...>`` has a ``class`` with requested attributes.

        :param document: The parsed HTML document
        :param class_attribute_value: The value of the ``class`` attribute
        :raises AssertionError: when the body class has not the requested value

        When HTML document is parsed, the words in a ``class`` attribute are
        alphabetically ordered and spaces are normalized, so to get a match
        keep words in ``class_attribute_value`` alphabetically ordered and
        separated with only one space character.
        """
        self.assertIn(
            ("class", class_attribute_value),
            normalize_attributes(document.body.attributes),
        )

    def verify_changelist_breadcrumbs(self, document, text):
        """
        Verify the change list's breadcrumbs.

        :param document: The parsed HTML document
        :param text: The text that appears in breadcrumbs
        :raises AssertionError: when breadcrumbs do not contain requested text

        In change list page, a breadcrumbs is a panel on the top of the page
        showing where we are in pages hierarchy, e.g. ::

            Home > Scan > Scans
        """
        element = get_child_by_tag_name(
            document.body, "div", (("id", "container"),)
        )
        breadcrumbs = get_child_by_tag_name(
            element, "div", (("class", "breadcrumbs"),)
        )
        self.assertEqual(extract_text(breadcrumbs), text)

    def verify_changelist_heading(self, document, text):
        """
        Verify the change list's heading.

        :param document: The parsed HTML document
        :param text: The text that should be a part of the ``<h1>`` element
        :raises AssertionError: when the text is not a part of the ``<h1>``
            element

        Test whether the change list's heading (``<h1>``) contains the
        requested text.
        """
        element = get_child_by_tag_name(
            document.body, "div", (("id", "container"),)
        )
        element = get_child_by_tag_name(element, "div", (("id", "main"),))
        element = get_child_by_tag_name(
            element, "div", (("class", "content"),)
        )
        element = get_child_by_tag_name(
            element, "div", (("id", "content"),)
        )
        heading = get_child_by_tag_name(element, "h1")
        self.assertIn(text, heading.children[0])

    def verify_changelist_add_link(self, document, text):
        """
        Verify that the change list's *Add ...* link works.

        :param document: The parsed HTML document
        :param text: The text that should appear in *Add ...* string both in
            the add button label and in the title of the page with a form
        :raises AssertionError: when the *Add ...* does not work or is not
            rendered properly

        This test checks whether the *Add ...* button is present with the
        expected label and its URL refers to the *Add ...* page (this check is
        done by checking the response status code and the title of the
        *Add ...* page).
        """
        element = get_child_by_tag_name(
            document.body, "div", (("id", "container"),)
        )
        element = get_child_by_tag_name(element, "div", (("id", "main"),))
        element = get_child_by_tag_name(
            element, "div", (("class", "content"),)
        )
        element = get_child_by_tag_name(
            element, "div", (("id", "content"),)
        )
        element = get_child_by_tag_name(
            element, "div", (("id", "content-main"),)
        )
        element = get_child_by_tag_name(
            element, "ul", (("class", "object-tools"),)
        )
        element = get_child_by_tag_name(element, "li")
        link = get_child_by_tag_name(element, "a")
        text = f"Add {text}"
        self.verify_html_link(link, text)
        self.assertIn(text, link.children[0])

    def verify_changelist_select_action(
        self, document, item_plural, items_per_page, items_total
    ):
        """
        Verify the layout of change list's select action.

        :param document: The parsed HTML document
        :param item_plural: The item name in the plural form
        :param items_per_page: The number of items displayed on the change list
            page
        :param items_total: The total number of items stored in the database
        :raises AssertionError: when the layout differs from what is expected

        In the top of the change list page is a select element with a *Go*
        button and the number of selected items message. This test looks up
        into the HTML document structure and checks that:

        #. The select element has *Delete selected I* option.
        #. The text on the right of the *Go* button shows *0 of N selected*.
        #. The ``<span>`` with *All I selected* is present.
        #. The ``<span>`` with *Select all M I* is present.

        where *I* is ``item_plural``, *N* is ``items_per_page``, and *M* is
        ``items_total``.
        """
        element = get_child_by_tag_name(
            document.body, "div", (("id", "container"),)
        )
        element = get_child_by_tag_name(element, "div", (("id", "main"),))
        element = get_child_by_tag_name(
            element, "div", (("class", "content"),)
        )
        element = get_child_by_tag_name(element, "div", (("id", "content"),))
        element = get_child_by_tag_name(
            element, "div", (("id", "content-main"),)
        )
        element = get_child_by_tag_name(
            element, "div", (("id", "changelist"),)
        )
        element = get_child_by_tag_name(
            element, "div", (("class", "changelist-form-container"),)
        )
        element = get_child_by_tag_name(
            element, "form", (("id", "changelist-form"),)
        )
        actions = get_child_by_tag_name(
            element, "div", (("class", "actions"),)
        )

        # Verify the select option "Delete selected ..." is present
        self.assertInParsedHTML(
            (
                '<option value="delete_selected">'
                f"Delete selected {item_plural}"
                "</option>"
            ),
            actions,
        )
        # Verify the action counter is present
        self.assertInParsedHTML(
            (
                '<span class="action-counter"'
                f' data-actions-icnt="{items_per_page}">'
                f"0 of {items_per_page} selected"
                "</span>"
            ),
            actions,
        )
        # Verify the "All ... selected" is present
        self.assertInParsedHTML(
            f'<span class="all hidden">All {items_total} selected</span>',
            actions,
        )
        # Verify the "Select all ..." is present
        self.assertInParsedHTML(
            (
                '<span class="question hidden">'
                '<a href="#"'
                ' title="Click here to select the objects across all pages">'
                f"Select all {items_total} {item_plural}"
                "</a>"
                "</span>"
            ),
            actions,
        )

    def verify_changelist_results_table(
        self, document, header, max_rows, *rows
    ):
        """
        Verify the change list's table with results.

        :param document: The parsed HTML document
        :param header: The expected table header
        :param max_rows: The maximal number of rows in the table
        :param rows: Rows that are expected to be in the table
        :raises AssertionError: when the change list's results table does not
            meet expectations

        The test checks

        * whether the ``header`` matches the header of the results table
        * whether the number of rows of the results table does not exceed the
          limit given by ``max_rows``
        * whether every row from ``rows`` is included in the results table and
          all links from the row are working
        """
        element = get_child_by_tag_name(
            document.body, "div", (("id", "container"),)
        )
        element = get_child_by_tag_name(element, "div", (("id", "main"),))
        element = get_child_by_tag_name(
            element, "div", (("class", "content"),)
        )
        element = get_child_by_tag_name(element, "div", (("id", "content"),))
        element = get_child_by_tag_name(
            element, "div", (("id", "content-main"),)
        )
        element = get_child_by_tag_name(
            element, "div", (("id", "changelist"),)
        )
        element = get_child_by_tag_name(
            element, "div", (("class", "changelist-form-container"),)
        )
        element = get_child_by_tag_name(
            element, "form", (("id", "changelist-form"),)
        )
        element = get_child_by_tag_name(
            element, "div", (("class", "results"),)
        )
        table = get_child_by_tag_name(
            element, "table", (("id", "result_list"),)
        )

        # Check if the number of rows does not exceed the given limit
        self.assertLessEqual(
            len(get_child_by_tag_name(table, "tbody").children), max_rows
        )

        self.assertInParsedHTML(header, table)
        for row in rows:
            self.assertInParsedHTML(row, table)
            self.verify_change_links(row)
