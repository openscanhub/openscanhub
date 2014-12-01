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
        help="enable clang analyzer (doesn't work on RHEL 5)"
    )


def add_no_cov_option(parser):
    parser.add_option(
        "-b",
        "--no-cov",
        default=False,
        action="store_true",
        help="do not use Coverity Static Analysis (HAS NO EFFECT -- use --analyzers option)"
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


def add_analyzers_option(parser):
    parser.add_option(
        "-a",
        "--analyzer",
        dest="analyzers",
        action="store",
        help="list of analyzers to use (see command 'list-analyzers'); use \
comma as a separator: e.g. \"--analyzer=clang,cov-6.6.1\""
    )


def add_profile_option(parser):
    parser.add_option(
        "-p",
        "--profile",
        dest="profile",
        action="store",
        help="use predefined scanning profile (for list of profiles see command list-profiles)"
    )


def add_csmock_args_option(parser):
    parser.add_option(
        "--csmock-args",
        dest="csmock_args",
        action="store",
        help="pass additional arguments to csmock (EXPERIMENTAL, USE WISELY)"
    )


def add_config_option(parser):
    parser.add_option(
        "--config",
        help="specify mock config name (use default one from config files \
if not specified)"
    )


def add_keep_covdata_option(parser):
    parser.add_option(
        "-i",
        "--keep-covdata",
        default=False,
        action="store_true",
        help="keep coverity data in final archive",
    )


def add_comment_option(parser):
    parser.add_option(
        "--comment",
        help="a task description",
    )


def add_task_id_file_option(parser):
    parser.add_option(
        "--task-id-file",
        help="task id is written to this file",
    )


def add_nowait_option(parser):
    parser.add_option(
        "--nowait",
        default=False,
        action="store_true",
        help="don't wait until tasks finish",
    )


def add_email_to_option(parser):
    parser.add_option(
        "--email-to",
        action="append",
        help="send notification to this address (can be used multiple times)"
    )


def add_priority_option(parser):
    parser.add_option(
        "--priority",
        type="int",
        help="task priority (20+ is admin only), default is 10"
    )


def add_brew_build_option(parser):
    parser.add_option(
        "--brew-build",
        action="store_true",
        default=False,
        help="use a brew build (specified by NVR) instead of a local file"
    )


def add_all_option(parser):
    parser.add_option(
        "--all",
        action="store_true",
        default=False,
        help="turn all checkers on"
    )


def add_security_option(parser):
    parser.add_option(
        "--security",
        action="store_true",
        default=False,
        help="turn security checkers on"
    )
