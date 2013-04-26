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
        help="directory for storing results (leave blank for working directory)"
    )
