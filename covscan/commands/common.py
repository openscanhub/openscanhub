# -*- coding: utf-8 -*-


def add_cppcheck_option(parser):
    parser.add_option(
        "-c",
        "--cppcheck",
        default=False,
        action="store_true",
        help="run cppcheck before Coverity scan",
    )


def add_aggressive_option(parser):
    parser.add_option(
        "--aggressive",
        default=False,
        action="store_true",
        help="make Coverity to make more aggressive assumptions during \
analysis; it reports more defects"
    )


def add_concurrency_option(parser):
    parser.add_option(
        "--concurrency",
        default=False,
        action="store_true",
        help="turn on concurrency-related checkers"
    )


def add_download_results_option(parser):
    parser.add_option(
        "-d",
        "--download-results",
        dest="results_dir",
        help="directory for storing results (leave blank for working \
directory)"
    )


def add_clang_option(parser):
    parser.add_option(
        "-l",
        "--clang",
        default=False,
        action="store_true",
        help="enable clang analyzer (doesn't work on RHEL 5) [EXPERIMENTAL]"
    )


def add_no_cov_option(parser):
    parser.add_option(
        "-b",
        "--no-cov",
        default=False,
        action="store_true",
        help="do not use Coverity Static Analysis"
    )


def add_comp_warnings_option(parser):
    parser.add_option(
        "-w",
        "--warn-level",
        choices=['0', '1', '2', '3'],
        metavar="LEVEL",
        help="adjust compiler warning level: 0 (default), 1 (appends -Wall \
and -Wextra, 2 (more warnings), 3 (lot of warnings); 2 and 3 can cause build \
failures with older mock profiles and/or non-default compilers (such as clang)"
    )


def add_cov_ver_option(parser):
    parser.add_option(
        "--cov-version",
        choices=['6.5.3', '6.6.1'],
        default='6.5.3',
        help="use specific version of coverity: 6.5.3 or 6.6.1"
    )
