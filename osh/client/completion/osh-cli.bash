# shellcheck shell=bash

_osh_cli_complete()
{
    # do not complete when --hub is used since the script will return
    # stale cached results
    [[ "${COMP_WORDS[*]}" == *'--hub'* ]] && return

    local ret
    ret="$(python3 -m "osh.client.completion.main" "$1")"
    COMPREPLY=( $(compgen -W "${ret}" -- "${cur##*,}") )
}

_osh_cli()
{
    local cur prev opts
    _init_completion -s || return

    # basic commands
    opts=({{version-,}diff,mock}-build download-results help{,-admin,-rst}
          {cancel,find,resubmit,watch}-tasks task-info watch-log
          list-{analyzers,mock-configs,profiles,tasks,workers})

    # no command selected
    if [[ ${#COMP_WORDS[@]} -lt 3 ]]; then
        COMPREPLY+=( $(compgen -W "${opts[*]} -h --help" -- "${cur}") )
        return
    fi

    # add opts that are always available
    COMPREPLY=( $(compgen -W '-h --help --username= --password=' -- "${cur}") )

    # add --hub conditionally
    if "${COMP_WORDS[0]}" --help | grep -q -- --hub=HUB; then
        COMPREPLY+=( $(compgen -W '--hub=' -- "${cur}") )
    fi

    case "${prev}" in
    --username|--password|--hub)
        COMPREPLY=()
        return
    esac

    case "${COMP_WORDS[1]}" in
    -h|--help)
        COMPREPLY=()
        return
        ;;

    # these do not have any extra options
    cancel-tasks|list-analyzers|list-mock-configs|list-profiles|help*|\
    task-info|watch-tasks)
        ;;

    download-results)
        case "${prev}" in
        -d|--dir)
            COMPREPLY=()
            _filedir -d
            return
            ;;
        *)
            COMPREPLY+=( $(compgen -W '-d --dir=' -- "${cur}") )
            ;;
        esac
        ;;

    find-tasks)
        COMPREPLY+=( $(compgen -W '-l --latest ' -- "${cur}") )
        COMPREPLY+=( $(compgen -W '-r --regex  ' -- "${cur}") )
        COMPREPLY+=( $(compgen -W '-p --package' -- "${cur}") )
        COMPREPLY+=( $(compgen -W '-n --nvr    ' -- "${cur}") )
        ;;

    list-tasks)
        COMPREPLY+=( $(compgen -W '--running --free' -- "${cur}") )
        COMPREPLY+=( $(compgen -W '--verbose --json' -- "${cur}") )
        ;;

    list-workers)
        COMPREPLY+=( $(compgen -W '--show-disabled' -- "${cur}") )
        ;;

    resubmit-tasks)
        case "${prev}" in
        --priority)
            COMPREPLY=()
            return
            ;;
        *)
            COMPREPLY+=( $(compgen -W '--force --nowait --priority=' -- "${cur}") )
            ;;
        esac
        ;;

    watch-log)
        case "${prev}" in
        --type|--poll)
            COMPREPLY=()
            return
            ;;
        *)
            COMPREPLY+=( $(compgen -W '--type= --poll= --nowait' -- "${cur}") )
            ;;
        esac
        ;;

    mock-build|diff-build|version-diff-build)
        # handle common flags
        case "${prev}" in
        --config)
            _osh_cli_complete mock-configs
            return
            ;;
        -d|--download-results)
            COMPREPLY=()
            _filedir -d
            return
            ;;
        -w|--warn-results)
            COMPREPLY=( $(compgen -W "1 2 3" -- "${cur}") )
            return
            ;;
        -a|--analyzer)
            # can be specified repeatedly
            local tmp
            [[ "${cur}" == *,* ]] && tmp="${cur%,*},"

            _osh_cli_complete analyzers
            COMPREPLY=( ${COMPREPLY[@]/#/$tmp} )

            # append ',' if there is only one match
            [[ ${#COMPREPLY[@]} -eq 1 ]] && COMPREPLY[0]+=","

            compopt -o nospace
            return
            ;;
        -p|--profile)
            _osh_cli_complete profiles
            return
            ;;
        --csmock-args|--comment|--email-to|--priority)
            COMPREPLY=()
            return
            ;;
        --task-id-file|--cov-custom-model)
            COMPREPLY=()
            _filedir
            return
            ;;
        *)
            COMPREPLY+=( $(compgen -W "-w --warn-levels=" -- "${cur}") )
            COMPREPLY+=( $(compgen -W "-a --analyzer=" -- "${cur}") )
            COMPREPLY+=( $(compgen -W "-p --profile=" -- "${cur}") )
            COMPREPLY+=( $(compgen -W "--csmock-args=" -- "${cur}") )
            COMPREPLY+=( $(compgen -W "--cov-custom-model=" -- "${cur}") )
            COMPREPLY+=( $(compgen -W "--config=" -- "${cur}") )
            COMPREPLY+=( $(compgen -W "--comment= --task-id-file=" -- "${cur}") )
            COMPREPLY+=( $(compgen -W "--nowait --email-to=" -- "${cur}") )
            COMPREPLY+=( $(compgen -W "--priority=" -- "${cur}") )
            COMPREPLY+=( $(compgen -W "--nvr" -- "${cur}") )
            ;;
        esac

        # handle remaining flags
        case "${COMP_WORDS[1]}" in
        diff-build|mock-build)
            case "${prev}" in
            -d|--download-results)
                COMPREPLY=()
                _filedir -d
                return
                ;;
            --install)
                COMPREPLY=()
                _filedir
                return
                ;;
            *)
                COMPREPLY+=( $(compgen -W "-d --download-results=" -- "${cur}") )
                COMPREPLY+=( $(compgen -W "--install=" -- "${cur}") )
                ;;
            esac

            if [[ "${COMP_WORDS[1]}" == 'mock-build' ]]; then
                case "${prev}" in
                --tarball-build-script)
                    COMPREPLY=()
                    _filedir
                    return
                    ;;
                *)
                    COMPREPLY+=( $(compgen -W "--tarball-build-script=" -- "${cur}") )
                    ;;
                esac
            fi
            ;;

        version-diff-build)
            case "${prev}" in
            --base-config)
                _osh_cli_complete mock-configs
                return
                ;;
            --base-nvr)
                COMPREPLY=()
                return
                ;;
            --base-srpm|--srpm)
                COMPREPLY=()
                _filedir
                return
                ;;
            *)
                COMPREPLY+=( $(compgen -W "--base-config=" -- "${cur}") )
                COMPREPLY+=( $(compgen -W "--base-nvr=" -- "${cur}") )
                COMPREPLY+=( $(compgen -W "--srpm= --base-srpm=" -- "${cur}") )
                ;;
            esac
            ;;
        esac
        ;;
    esac

    # complete files if ${cur} is empty and ${prev} is not an option
    if [[ -z "${cur}" ]]; then
        COMPREPLY=()
        _filedir
        return
    fi

    # do not append an extra space for options ending with '='
    [[ "${COMPREPLY[*]}" == *= ]] && compopt -o nospace
}

complete -F _osh_cli osh-cli
