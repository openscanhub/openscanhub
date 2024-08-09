import re


def parse_dist_git_url(git_url):
    # RE pattern to match a dist-git URL with named groups
    regex = r'^(?P<scheme>git\+https?|git|https?|ssh)://(?P<host>[^/]+)(?P<path>/[^#]*)(#(?P<commit_hash>[^#]+))?$'

    match = re.match(regex, git_url)

    if not match:
        raise ValueError(f"Invalid dist-git URL: {git_url}")

    scheme = match.group('scheme')
    host = match.group('host')
    path = match.group('path')
    commit_hash = match.group('commit_hash')

    # Check whether the scheme is valid
    if scheme not in ['git', 'git+https', 'git+http', 'https', 'http', 'ssh']:
        raise ValueError(f"Invalid scheme in dist-git URL: {scheme}")

    # Check whether the host is a valid
    if not re.match(r'^[a-zA-Z0-9.-]+$', host):
        raise ValueError(f"Invalid host in dist-git URL: {host}")

    # Check that the path does not contain any invalid characters
    if not re.match(r'^/[a-zA-Z0-9./_-]+$', path):
        raise ValueError(f"Invalid path in dist-git URL: {path}")

    # we expect a non-null fragment(commit hash) in a valid dist-dist-git URL
    if commit_hash is None:
        raise ValueError("Missing commit hash in dist-git URL")
    elif not re.match(r'^[a-fA-F0-9]{40}$', commit_hash):
        # Check that the commit_hash does not contain any invalid characters
        raise ValueError(f"Invalid commit_hash in dist-git URL: {commit_hash}")

    # Extract the repo name from the path
    repo_name = path.split('/')[-1]

    return (scheme + '://' + host, path, repo_name, commit_hash)
