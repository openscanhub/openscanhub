{
    "scan":
    {
        "analyzer": "coverity",
        "analyzer-args": "--wait-for-license --security",
        "analyzer-version": "6.5.0",
        "compilation-unit-count": 266,
        "compilation-unit-ratio": 100,
        "host": "dell-per610-03.lab.eng.brq.redhat.com",
        "mock-config": "fedora-rawhide-cscan",
        "project-name": "systemd-191-2.fc18",
        "time-created": "2012-09-24 09:13:17",
        "time-finished": "2012-09-24 09:26:08",
        "tool": "cov-mockbuild",
        "lines-processed": 123456,
        "time-elapsed-analysis": 00:01:45,
        "tool-args": "fedora-rawhide-cscan /tmp/covscan_2shiDI/systemd-191-2.fc18.src.rpm --security",
        "tool-version": "cov-mockbuild-0.20120803_8ab033d-1.el6.noarch csdiff-0.20120904_92afa5d-1.el6.x86_64"
    },
    "defects":
    [
        {
            "checker": "ARRAY_VS_SINGLETON",
            "annotation": " (CWE-119)",
            "key_event_idx": 4,
            "events":
            [
                {
                    "file_name": "/builddir/build/BUILD/systemd-191/src/login/loginctl.c",
                    "line": 431,
                    "event": "address_of",
                    "message": "Taking address with \"&i->leader\" yields a singleton pointer."
                },
                {
                    "file_name": "/builddir/build/BUILD/systemd-191/src/login/loginctl.c",
                    "line": 431,
                    "event": "callee_ptr_arith",
                    "message": "Passing \"&i->leader\" to function \"show_cgroup_and_extra_by_spec\" which uses it as an array. This might corrupt or misinterpret adjacent memory locations."
                },
                {
                    "file_name": "/builddir/build/BUILD/systemd-191/src/shared/cgroup-show.c",
                    "line": 342,
                    "event": "callee_ptr_arith",
                    "message": "Performing pointer arithmetic on \"extra_pids\" in callee \"show_cgroup_and_extra\"."
                },
                {
                    "file_name": "/builddir/build/BUILD/systemd-191/src/shared/cgroup-show.c",
                    "line": 329,
                    "event": "callee_ptr_arith",
                    "message": "Performing pointer arithmetic on \"extra_pids\" in callee \"show_extra_pids\"."
                },
                {
                    "file_name": "/builddir/build/BUILD/systemd-191/src/shared/cgroup-show.c",
                    "line": 301,
                    "event": "ptr_arith",
                    "message": "Performing pointer arithmetic on \"pids\" in expression \"pids + i\"."
                }
            ]
        },
        {
            "checker": "BUFFER_SIZE_WARNING",
            "annotation": " (CWE-170)",
            "key_event_idx": 1,
            "events":
            [
                {
                    "file_name": "/builddir/build/BUILD/systemd-191/src/shared/utmp-wtmp.c",
                    "line": 225,
                    "event": "buffer_size_warning",
                    "message": "Calling strncpy with a maximum size argument of 4 bytes on destination array \"store.ut_id\" of size 4 bytes might leave the destination string unterminated."
                },
                {
                    "file_name": "/builddir/build/BUILD/systemd-191/src/shared/utmp-wtmp.c",
                    "line": 228,
                    "event": "buffer_size_warning",
                    "message": "Calling strncpy with a maximum size argument of 32 bytes on destination array \"store.ut_line\" of size 32 bytes might leave the destination string unterminated."
                }
            ]
        }
   ]
}
