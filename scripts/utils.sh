check_host_os() {
  echo "$OSTYPE" | grep -q 'darwin'
  if test $? = 0; then
    alias podman=docker
    alias podman-compose=docker-compose
  fi
}

# wait until something listens on the specified port
wait_for_port() (
  set +x
  set +e
  port=$1
  cnt=256
  while ((--cnt)); do
    curl -fo/dev/null --no-progress-meter "http://localhost:${port}"
    case $? in
      # we get `curl: (52) Empty reply from server`
      # when we speak HTTP to psql db port
      0|52)
        break
        ;;
      *)
        # wait for the container to become ready
        sleep 1
        ;;
    esac
  done
)

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

check_host_os
