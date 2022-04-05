_covscan_configs()
{
    local IFS=$'\n'
    configs=$(python -c "from covscancommon.utils.completion import main ; \
        main()" 2>/dev/null)
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

_covscan()
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
    if [ "${prev2}" == "--config" -a "${prev}" == "=" ] ; then
        #local configs=$(for x in `covscan list-mock-configs 2>&1 | egrep "^[_[:alnum:]\-\.]+.+True" | awk '{ print $1 }'` ; do echo "$x" ; done )
        _covscan_configs
        COMPREPLY=( $(compgen -W "${configs}" -- ${cur}) )
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
complete -F _covscan covscan
