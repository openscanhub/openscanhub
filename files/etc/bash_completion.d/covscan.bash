_covscan_configs()
{
    local IFS=$'\n'
    configs=$(python -c "from covscan.utils.completion import main ; \
        main()" 2>/dev/null)
}

_covscan() 
{
    local cur prev prev2 opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    prev2="${COMP_WORDS[COMP_CWORD-2]}"
 
    # basic commands
    opts="list-mock-configs cancel-tasks mock-build diff-build version-diff-build"

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
    fi

   COMPREPLY=($(compgen -W "${opts}" -- ${cur}))  
   return 0
}
complete -F _covscan covscan
