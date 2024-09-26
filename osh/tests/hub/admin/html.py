# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.
"""Utilities that help to test the structure of HTML document."""

import functools

from django.test.html import Element, normalize_whitespace
from django.test.html import parse_html as django_parse_html


def normalize_spaces(text):
    """
    Ensure words in text are separated just by one space character.

    :param text: The text
    :return: the text where words are separated by only one space

    As a word is understood a consecutive sequence of non-white-space
    characters. Unlike :func:`~django.test.html.normalize_whitespace`, leading
    and trailing white space characters are stripped.
    """
    return normalize_whitespace(text.strip())


def normalize_attributes(attributes):
    """
    Normalize white spaces in attribute values.

    :param attributes: The sequence of attributes
    :return: the sequence of normalized attributes

    An attribute is a pair containing attribute name and attribute value,
    respectively. White space characters are normalized in attribute values.
    Attribute value can be also :obj:`None`.
    """
    return (
        (
            attr[0],
            normalize_spaces(attr[1]) if isinstance(attr[1], str) else attr[1]
        )
        for attr in attributes
    )


def extract_text(element):
    """
    Extract text elements from element.

    :param element: The HTML DOM element
    :return: the string containing text elements separated by the space
        character

    The order of text elements, as they appear in HTML code, is preserved.
    """
    text_elements = []
    stack = element.children[:]
    while stack:
        item = stack.pop(0)
        if isinstance(item, str):
            text_elements.append(normalize_spaces(item))
            continue
        stack[:0] = item.children
    return " ".join(text_elements)


def extract_links(element):
    """
    Extract all link (``<a ...>...</a>``) elements from element.

    :param element: The HTML DOM element
    :return: the generator yielding link elements

    The order of link elements, as they appear in HTML code, is preserved.
    """
    stack = [element]
    while stack:
        item = stack.pop(0)
        if hasattr(item, "name") and item.name.lower() == "a":
            yield item
        if hasattr(item, "children"):
            stack[:0] = item.children


@functools.lru_cache(maxsize=None)
def has_tag_match(element, name, attributes):
    """
    Test element for name and attributes.

    :param element: The HTML DOM element
    :param attributes: Requested attributes
    :return: true if the element name matches and attributes are contained in
        element's attributes

    The test passes if this two conditions are met:

    #. The element's name is same as ``name`` (case insensitive comparison).
    #. All attributes from ``attributes`` are included in normalized element's
       attributes.
    """
    if not hasattr(element, "name") or not hasattr(element, "attributes"):
        return False
    if element.name.lower() != name.lower():
        return False
    element_attributes = normalize_attributes(element.attributes)
    for attr in attributes:
        if attr not in element_attributes:
            return False
    return True


def not_found_error(name, attributes):
    """
    Raise :exc:`KeyError` with details about what is missing.

    :param name: The requested name of a tag
    :param attributes: Requested attributes
    :raises KeyError: with a detail that the tag with requested name and
        attributes was not found
    """
    detail = " and ".join([f'{attr[0]}="{attr[1]}"' for attr in attributes])
    if detail:
        detail = f" and attributes {detail}"
    detail = f"Element with tag '{name}'{detail} not found"
    # KeyError because (name, attributes) is a "key" under which we are trying
    # to find a specific object
    raise KeyError(detail)


@functools.lru_cache(maxsize=None)
def get_child_by_tag_name(element, name, attributes=()):
    """
    Get the element's child with specified tag name and attributes.

    :param element: The HTML DOM element
    :param name: The requested name of a tag
    :param attributes: Requested attributes
    :return: the element's child satisfying the requirements
    :raises KeyError: when the element has no such a child

    The first matching element's child is returned. To consult conditions under
    which a child is considered a match, see :func:`.has_tag_match`.
    """
    for child in element.children:
        if has_tag_match(child, name, attributes):
            return child
    not_found_error(name, attributes)


class Document(Element):
    """
    Wrapper around a document root element.

    The purpose of this wrapper is to provide a shortcuts to access the
    document's head and the document's body. It is assumed that the document
    root element has two children -- the first is the head and the second is
    the body.
    """

    def __init__(self, element):
        """
        Wrap the document root element.

        :param element: The document root element
        """
        super().__init__(element.name, element.attributes)
        self.children = element.children

    @property
    def head(self):
        """
        Get the document's head.

        :return: the document's head
        """
        return self.children[0]

    @property
    def body(self):
        """
        Get the document's body.

        :return: the document's body
        """
        return self.children[1]


def parse_html(html):
    """
    Parse HTML document.

    :param html: The HTML document to be parsed
    :return: the parsed HTML document with its root element wrapped in
        :class:`.Document`
    """
    return Document(django_parse_html(html))
