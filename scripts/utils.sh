check_host_os() {
  echo "$OSTYPE" | grep -q 'darwin'
  if test $? = 0; then
    shopt -s expand_aliases
    alias podman=docker
    alias podman-compose=docker-compose
  fi
}

check_host_os

#This function checks container status
#
# @param $1 container name (e.g. hub, worker, client)
#
# Returns:
# 0 if container is running, 1 if it isn't started in 60s
wait_for_container() {
  filename="$(echo "$1" | tr '[:lower:]' '[:upper:]')"
  filename+="_IS_READY"

  containername="osh-"
  containername+="$(echo "$1" | tr '[:upper:]' '[:lower:]')"

  for _ in $(seq 60); do
    podman exec -i "$containername" bash -c "[[ -f /$filename ]]"
    retval=$?
    if [[ $retval = 0 ]]; then
      return 0
    fi
    sleep 1
  done
  return 1
}

#This function checks against a program version
#
# @currentver Current software version
# @requiredver Minimum required version
#
# Returns:
# 0 if @currentver >= @requiredver and 1 otherwise
version_compare() {
  currentver="$1"
  requiredver="$2"

  test "$(printf '%s\n' "$requiredver" "$currentver" | sort -V | head -n1)" = "$requiredver"
}
