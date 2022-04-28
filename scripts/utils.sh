check_host_os() {
  echo "$OSTYPE" | grep -q 'darwin'
  if test $? = 0; then
    shopt -s expand_aliases
    alias podman=docker
    alias podman-compose=docker-compose
  fi
}

check_host_os

wait_for_container() {
  filename="/$1_IS_READY"
  for _ in $(seq 60); do
    podman exec -i covscanhub bash -c "[[ -f $filename ]]"
    retval=$?
    if [[ $retval = 0 ]]; then
      podman exec -i covscanhub bash -c "rm $filename"
      break
    fi
    sleep 1
  done
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
