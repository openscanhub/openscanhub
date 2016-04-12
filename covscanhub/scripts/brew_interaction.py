#!/usr/bin/python
# -*- coding: utf-8 -*-

from pprint import pprint
import brew
import sys

try:
    nvr = sys.argv[1]
except IndexError:
    nvr = 'bind-9.8.2-0.17.rc1.el6.3'

session = brew.ClientSession('http://brewhub.engineering.redhat.com/brewhub')
build = session.getBuild(nvr)
print 'Build:'
pprint(build)
task = session.getTaskInfo(build['task_id'], request=True)
print '\nTask:'
pprint(task)
target_name = task['request'][1]
target = session.getBuildTarget(target_name)
print '\nTarget:'
pprint(target)
child_tasks = session.getTaskChildren(task['id'], request=True)
print '\nChild tasks:'
pprint(child_tasks)
for task in child_tasks:
    if task['method'] == 'buildArch' and task['arch'] == 'x86_64':
        build_task = task
print '\nx86_64 buildArch task:'
pprint(build_task)
print '\nRepo states:'
pprint(brew.REPO_STATES)
request = build_task['request']
repo_id = request[4]['repo_id']
old_repo = session.repoInfo(repo_id)
print '\nOld repo:'
pprint(old_repo)
new_repo = session.getRepo(target['build_tag'])
print '\nCurrent repo:'
pprint(new_repo)
old_builds = session.listTagged(target['build_tag'],
                                latest=True,
                                inherit=True,
                                event=old_repo['create_event'])
print '\nNumber of builds in old repo: ', len(old_builds)
new_builds = session.listTagged(target['build_tag'],
                                latest=True,
                                inherit=True,
                                event=new_repo['create_event'])
print '\nNumber of builds in current repo: ', len(new_builds)
