_osh_cli_configs()
{
    local IFS=$'\n'
    configs="$(python3 -m "osh.client.completion.main" mock-configs)"
}

#function contains() {
#    local n=$#
#    local value=${!n}
#    for ((i=1;i < $#;i++)) {
#        if [ "${!i}" == "${value}" ]; then
#            echo "y"
#            return 0
#        fi
#    }
#    echo "n"
#    return 1
#}
#
#function is_build_scan() {
#    local build_opts=("mock-build" "diff-build" "version-diff-build")
#    for $opt in $build_opts ; do
#        if [ $(contains "$#" "${opt}") == "y" ]; then
#            return 0
#        fi
#    done
#    return 1
#}

_osh_cli()
{
    local cur prev prev2 opts
    COMPREPLY=()
    {
        cur="${COMP_WORDS[COMP_CWORD]}"
        prev="${COMP_WORDS[COMP_CWORD-1]}"
        prev2="${COMP_WORDS[COMP_CWORD-2]}"
    } 2>/dev/null

    # basic commands
    opts="cancel-tasks diff-build download-results find-tasks list-mock-configs mock-build task-info version-diff-build"

    # complete for --config=<mock_config>
    if [ "${prev}" == "--config" -o "${prev2}" == "--config" ] ; then
        _osh_cli_configs
        COMPREPLY=( $(compgen -W "${configs}" -- ${cur#=}) )
        return 0
    elif [ "${prev}" == "mock-build" -o "${prev}" == "diff-build" ] ; then
        COMPREPLY=( $(compgen -W "--config=" -- ${cur}) )
        compopt -o nospace
        return 0
    elif [[ ${#COMP_WORDS[@]} < 3 ]] ; then
        COMPREPLY=($(compgen -W "${opts}" -- ${cur}))
        return 0
    #elif [ $( is_build_scan "${COMP_WORDS[@]}" ) ] ; then
    fi
    COMPREPLY=( $( compgen -f -- "$cur") )
    compopt -o filenames
    return 0
}
complete -F _osh_cli osh-cli
# This is kept here for backward compatibility reasons
complete -F _osh_cli covscan
