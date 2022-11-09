"""Provides function for marking different parts of two NVRs."""

import itertools
import re

from django.utils.safestring import mark_safe

__all__ = (
    'get_compare_title',
)

CSS_CLASS_OTHER = "light_green_font"
CSS_CLASS_BASE = "red_font"


def parse_nvr(nvr):
    """
    Split NVR to name, version, and release.

    :param nvr: The NVR (name-version-release).
    :type nvr:

    :return: the `tuple` containing name, version, and release string
    :rtype: tuple

    In case NVR is ill-formed:
    * if it is in a form of ``X-Y``, return ``(X, Y, "")``;
    * otherwise, return ``(nvr, "", "")``.
    """
    nvr_parts = re.match("(.*)-(.*)-(.*)", nvr)
    if nvr_parts:
        return nvr_parts.group(1), nvr_parts.group(2), nvr_parts.group(3)
    # One of the NVR components is missing:
    nvr_parts = re.match("(.*)-(.*)", nvr)
    if nvr_parts:
        return nvr_parts.group(1), nvr_parts.group(2), ""
    # Two of the NVR components are missing:
    return nvr, "", ""


def mark(content, css_class):
    """
    Surround *content* with ``<span>`` using *css_class*.

    :param content: The content
    :type content: str
    :param css_class: The CSS class used in ``<span>``
    :type css_class: str

    :return: *content* surrounded with ``<span>`` styled with *css_class*
    :rtype: str
    """
    return f'<span class="{css_class}">{content}</span>'


def mark_other(content):
    """
    Render *content* in light green color using ``<span>``.

    :param content: The content
    :type content: str

    :return: *content* in light green color as a HTML string
    :rtype: str
    """
    return mark(content, CSS_CLASS_OTHER)


def mark_base(content):
    """
    Render *content* in red color using ``<span>``.

    :param content: The content
    :type content: str

    :return: *content* in red color as a HTML string
    :rtype: str
    """
    return mark(content, CSS_CLASS_BASE)


def compare_nvr_parts(other, base, prev_differ=False):
    """
    Compare two names, versions, or releases.

    :param other: Name, version, or release as a list of its parts to be
        compared against *base*
    :type other: list
    :param base: Name, version, or release as a list of its parts
    :type base: list
    :param prev_differ: `True` if the previous comparison of name, version, or
        release yielded a difference
    :type prev_differ: bool

    :return: the `tuple` containing a `bool` flag signaling whether *other* and
      *base* are different, a string with marked different parts of *other*,
      and a string with marked different parts of *base*
    :rtype: tuple

    If *prev_differ* is `True`, *base* and *other* are considered different and
    their parts are marked accordingly. Otherwise, *base* and *other* are
    considered different if and only if they are different in some *n*th part.
    In this case, all parts starting from *n*th part to the last part are
    marked different. Empty parts are not marked.

    Examples: Suppose that ``mark_other(x)`` yields ``f"({x})"`` and
    ``mark_base(x)`` yields ``f"[{x}]"``. Then
    * ``compare_nvr_parts(["1", "2", "3"], ["1", "2", "3"], True)`` yields
      ``(True, "(1).(2).(3)", "[1].[2].[3]")``;
    * ``compare_nvr_parts(["1", "2", "3"], ["1", "1", "3"], False)`` yields
      ``(True, "1.(2).(3)", "1.[1].[3]")``;
    * ``compare_nvr_parts(["1", "2"], ["1", "2", "3"], False)`` yields
      ``(True, "1.2", "1.2.[3]")``.
    """
    differ = prev_differ
    diff_other = []
    diff_base = []
    for elm1, elm2 in itertools.zip_longest(other, base, fillvalue=""):
        differ = differ or elm1 != elm2
        if elm1:
            diff_other.append(differ and mark_other(elm1) or elm1)
        if elm2:
            diff_base.append(differ and mark_base(elm2) or elm2)
    return differ, ".".join(diff_other), ".".join(diff_base)


def get_compare_title(nvr, base_nvr):
    """
    Compare two NVRs, mark different parts with ``<span>``.

    :param nvr: The name-version-release to be compared against base
    :type nvr: str
    :param base_nvr: The base name-version-release
    :type base_nvr: str

    :return: the comparison summary
    :rtype: str

    A name-version-release string, NVR for short, is a string matching the
    following format::

        <name> "-" <version> "-" <release>

    where ``<version>`` and ``<release>`` must not contain a dash (``-``),
    dashes in ``<name>`` are allowed. Additionally, ``<version>`` and
    ``<release>`` are composed from parts separated by a dot (``.``).

    Two NVRs are compared part-wise from the left to the right as follows:

    #. If ``<name>``s differ, everything in NVR is marked as different.
    #. Otherwise, if ``<version>``s differ in some part, the part and the
       remaining parts are marked as different.
    #. Otherwise, if ``<release>``s differ in some part, the part and the
       remaining parts are marked as different.
    #. Otherwise, NVRs are equal.

    For more clarity, let demonstrate it on several examples. For simplicity,
    ``<span class="light_green_font">X</span>`` and
    ``<span class="red_font">Y</span>`` will be abbreviated ``(X)`` and
    ``[Y]``, respectively.

    Examples:
    #. A comparison of ``foo-1.2.3-4.el8`` and ``bar-1.2.3-4.el8`` yields
       ``(foo)-(1).(2).(3)-(4).(el8) compared to [bar]-[1].[2].[3]-[4].[el8]``.
    #. A comparison of ``foo-2.2.3-4.el8`` and ``foo-1.2.3-4.el8`` yields
       ``foo-(2).(2).(3)-(4).(el8) compared to foo-[1].[2].[3]-[4].[el8]``.
    #. A comparison of ``foo-1.2.3-4.el8`` and ``foo-1.3.3-4.el8`` yields
       ``foo-1.(2).(3)-(4).(el8) compared to foo-1.[3].[3]-[4].[el8]``.
    #. A comparison of ``foo-1.2.3-4.el8`` and ``foo-1.2.2-4.el8`` yields
       ``foo-1.2.(3)-(4).(el8) compared to foo-1.2.[2]-[4].[el8]``.
    #. A comparison of ``foo-1.2.3-4.el8`` and ``foo-1.2.3-4.el9`` yields
       ``foo-1.2.3-4.(el8) compared to foo-1.2.3-4.[el8]``.
    #. A comparison of ``foo-1.2.3-4.el8`` and ``foo-1.2-4.el8`` yields
       ``foo-1.2.(3)-(4).(el8) compared to foo-1.2-[4].[el8]``.
    """
    name, version, release = parse_nvr(nvr)
    base_name, base_version, base_release = parse_nvr(base_nvr)

    differ, diff_name_other, diff_name_base = compare_nvr_parts(
        [name], [base_name]
    )
    differ, diff_version_other, diff_version_base = compare_nvr_parts(
        version.split("."), base_version.split("."), differ
    )
    _, diff_release_other, diff_release_base = compare_nvr_parts(
        release.split("."), base_release.split("."), differ
    )

    # Remove empty strings that were produced where some of NVR components are
    # missing:
    diff_other = list(
        filter(None, [diff_name_other, diff_version_other, diff_release_other])
    )
    diff_base = list(
        filter(None, [diff_name_base, diff_version_base, diff_release_base])
    )

    return mark_safe(f'{"-".join(diff_other)} compared to {"-".join(diff_base)}')
