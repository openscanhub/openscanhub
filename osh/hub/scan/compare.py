# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright contributors to the OpenScanHub project.

"""Provides function for marking different parts of two NVRs."""

import itertools

from django.utils.safestring import mark_safe
from kobo.rpmlib import parse_nvr

__all__ = (
    'get_compare_title',
)

CSS_CLASS_OTHER = "light_green_font"
CSS_CLASS_BASE = "red_font"


def parse_nevr(nevr):
    """
    Split NEVR to name, epoch, version, and release.

    :param nevr: The NEVR (name-epoch:version-release).
    :type nevr: str

    :return: the `tuple` containing name, epoch, version, and release string
    :rtype: tuple

    ``parse_nvr`` from ``kobo.rpmlib`` accepts three forms of NEVR:
    * ``name-epoch:version-release``
    * ``epoch:name-version-release``
    * ``name-version-release:epoch``

    ``epoch`` is optional (missing ``epoch`` is treated as 0 in many tools).
    Since ``kobo.rpmlib.parse_nvr`` return a dictionary the information where
    the ``epoch`` is placed is lost. As a convention, we stick with the
    ``name-epoch:version-release`` form as this form is nowadays used in vast
    majority of tools.

    If NEVR is ill-formed, return ``(nevr, "", "", "")``.
    """
    try:
        nevr_parts = parse_nvr(nevr)
    except ValueError:
        return nevr, "", "", ""
    return (
        nevr_parts["name"],
        nevr_parts.get("epoch", ""),
        nevr_parts["version"],
        nevr_parts["release"],
    )


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


def compare_nevr_parts(other, base, prev_differ=False):
    """
    Compare two names, epochs, versions, or releases.

    :param other: Name, epoch, version, or release as a list of its parts to be
        compared against *base*
    :type other: list
    :param base: Name, epoch, version, or release as a list of its parts
    :type base: list
    :param prev_differ: `True` if the previous comparison of name, epoch,
        version, or release yielded a difference
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
            diff_other.append(mark_other(elm1) if differ else elm1)
        if elm2:
            diff_base.append(mark_base(elm2) if differ else elm2)
    return differ, ".".join(diff_other), ".".join(diff_base)


def make_nevr(name, epoch, version, release):
    """
    Assemble NEVR parts (possibly marked) back to NEVR string.

    :param name: The name
    :type name: str
    :param epoch: The epoch
    :type epoch: str
    :param version: The version
    :type version: str
    :param release: The release
    :type release: str

    :return: the assembled NEVR
    :rtype: str

    Assuming NEVR is of the form ``name-epoch:version-release``, this function
    aims to be the inverse of :func:`parse_nevr`. That is, ``nevr ==
    make_nevr(*parse_nevr(nevr))`` yields `True`, even if ``nevr`` is
    ill-formed.
    """
    # Empty version/release means that NEVR is ill-formed and stored in name.
    # Note that version and release are either both empty or both non-empty.
    if not release:
        return name
    if epoch:
        version = f"{epoch}:{version}"
    return "-".join([name, version, release])


def get_compare_title(nevr, base_nevr):
    """
    Compare two NEVRs, mark different parts with ``<span>``.

    :param nevr: The name-epoch:version-release to be compared against base
    :type nevr: str
    :param base_nevr: The base name-epoch:version-release
    :type base_nevr: str

    :return: the comparison summary
    :rtype: str

    A name-epoch:version-release string, NEVR for short, is a string matching
    the following format::

        <name> "-" <epoch> ":" <version> "-" <release>

    where ``<version>`` and ``<release>`` must not contain a dash (``-``),
    dashes in ``<name>`` are allowed. Additionally, ``<version>`` and
    ``<release>`` are composed from parts separated by a dot (``.``).
    ``<epoch>`` is a non-negative number and it is optional. If missing, it is
    treated as zero.

    Two NEVRs are compared part-wise from the left to the right as follows:

    #. If ``<name>``s differ, everything in NEVR is marked as different.
    #. Otherwise, if ``<epoch>``s differ, the epoch and the rest of NEVR is
       marked as different.
    #. Otherwise, if ``<version>``s differ in some part, that part, the
       remaining parts and the rest of NEVR are marked as different.
    #. Otherwise, if ``<release>``s differ in some part, that part, the
       remaining parts and the rest of NEVR are marked as different.
    #. Otherwise, NEVRs are equal.

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
    #. A comparison of ``foo-1.2.3-4.el8`` and ``foo-1:1.2.3-4.el8`` yields
       ``foo-(1).(2).(3)-(4).(el8) compared to foo-[1]:[1].[2].[3]-[4].[el8]``.
    #. A comparison of ``foo-0:1.2.3-4.el8`` and ``foo-1:1.2.3-4.el8`` yields
       ``foo-(0):(1).(2).(3)-(4).(el8) compared to foo-[1]:[1].[2].[3]-[4].[el8]``.
    """
    name, epoch, version, release = parse_nevr(nevr)
    base_name, base_epoch, base_version, base_release = parse_nevr(base_nevr)

    differ, diff_name_other, diff_name_base = compare_nevr_parts(
        [name], [base_name]
    )
    differ, diff_epoch_other, diff_epoch_base = compare_nevr_parts(
        [epoch], [base_epoch], differ
    )
    differ, diff_version_other, diff_version_base = compare_nevr_parts(
        version.split("."), base_version.split("."), differ
    )
    _, diff_release_other, diff_release_base = compare_nevr_parts(
        release.split("."), base_release.split("."), differ
    )

    return mark_safe(
        f"{make_nevr(diff_name_other, diff_epoch_other, diff_version_other, diff_release_other)}"
        " compared to "
        f"{make_nevr(diff_name_base, diff_epoch_base, diff_version_base, diff_release_base)}"
    )
