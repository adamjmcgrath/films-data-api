#!/usr/bin/python
#
# Copyright 2011 Friday Film Club. All Rights Reserved.

"""Deploy the Friday Film Club application."""

from __future__ import with_statement

__author__ = 'adamjmcgrath@gmail.com (Adam McGrath)'

import functools
import operator
import os
import sys
from fabric.api import *
from fabric.colors import green, red, yellow
import datetime
import re

APPENGINE_PATH = os.path.abspath(os.environ['APPENGINE_SRC'])
APPENGINE_DEV_APPSERVER =  os.path.join(APPENGINE_PATH, 'dev_appserver.py')
APPENGINE_APP_CFG =  os.path.join(APPENGINE_PATH, 'appcfg.py')
PYTHON = '/usr/bin/python'

env.gae_email = 'adamjmcgrath@gmail.com'
env.gae_src = './src'

def fix_appengine_path():
  EXTRA_PATHS = [
    APPENGINE_PATH,
    os.path.join(APPENGINE_PATH, 'lib', 'antlr3'),
    os.path.join(APPENGINE_PATH, 'lib', 'django'),
    os.path.join(APPENGINE_PATH, 'lib', 'fancy_urllib'),
    os.path.join(APPENGINE_PATH, 'lib', 'ipaddr'),
    os.path.join(APPENGINE_PATH, 'lib', 'webob'),
    os.path.join(APPENGINE_PATH, 'lib', 'yaml', 'lib'),
  ]

  sys.path = EXTRA_PATHS + sys.path

fix_appengine_path()
from google.appengine.api import appinfo



def include_appcfg(func):
  """Decorator that ensures the current Fabric env has a GAE app.yaml config
  attached to it."""
  @functools.wraps(func)
  def decorated_func(*args, **kwargs):
    if not hasattr(env, 'app'):
      try:
        appcfg = appinfo.LoadSingleAppInfo(open('%s/app.yaml' % env.gae_src))
      except IOError:
        abort('You must be in the App Engine application root.')
      env.app = appcfg
    return func(*args, **kwargs)
  return decorated_func


def last_tag():
  print yellow('Last tag: %s' % get_last_tag_match())


@include_appcfg
def deploy(tag=None, prod=False):
  if not is_working_directory_clean():
    abort('Working directory should be clean before deploying.')

  prepare_deploy(tag=tag, prod=prod)
  local('%s %s -A %s -V %s --email=%s update %s' % (PYTHON, APPENGINE_APP_CFG,
      env.app.application, env.app.version, env.gae_email, env.gae_src))
  end_deploy()
  commit()


@include_appcfg
def shell():
  with lcd(env.gae_src):
    local('%s %s/remote_api_shell.py -s films-data.appspot.com' %
            (PYTHON, APPENGINE_PATH))


def run(port='8080', clear_datastore=False, send_mail=True):
  command = '%s --port %s'

  if clear_datastore:
    command += ' --clear_datastore'
  if send_mail:
    command += ' --enable_sendmail=yes'

  command += ' %s'
  local(command % (APPENGINE_DEV_APPSERVER, port, env.gae_src))


def commit(branch='master'):
  if not is_working_directory_clean():
    abort('Working directory should be clean before pushing.')
  print yellow('Updating remote repository.')
  local('git push --tags origin %s' % branch)


def prepare_deploy(tag=None, prod=False):
  print yellow('Preparing the deployment.')

  if tag != None:
    env.deployment_tag = tag
  else:
    do_tag()

  # Set the app version to the git tag.
  print 'env.deployment_tag:%s' % env.deployment_tag

  if not prod:
    env.app.version += '-test'

  # Check out a clean copy.
  deploy_path = local('mktemp -d -t %s' % env.app.application, capture=True)
  local('git clone . %s' % deploy_path)

  with lcd(deploy_path):
    local('git checkout %s' % env.deployment_tag)
    local('find . -name ".git*" | xargs rm -rf')
    print yellow('App: %s' % env.app.application)
    print yellow('Ver: %s' % env.app.version)

  env.deploy_path = deploy_path


def end_deploy():
  print yellow('Cleaning up after the deploy.')
  local('rm -rf %s' % env.deploy_path)


def check_if_last_version():
  branch = local('git branch --no-color 2> /dev/null | '
    'sed -e "/^[^*]/d"', capture=True).replace('* ', '').strip()
  local_sha = local('git log --pretty=format:%H HEAD -1', capture=True).strip()
  origin_sha = local(
      'git log --pretty=format:%%H %s -1' % branch, capture=True).strip()
  if local_sha != origin_sha:
    abort("""
    Your %s branch is not up to date with origin/%s.
    Please make sure you have pulled and pushed all code before deploying:

    git pull origin %s
    #run tests, etc
    git push origin %s

    """ % (branch, branch, branch, branch))


def get_last_tag_match():
  tags = local('git tag -l', capture=True)
  if len(tags) == 0:
    return None
  tags = [(int(x.split('-')[0]), int(x.split('-')[1])) for x in tags.split()]
  tag = sorted(tags, key=operator.itemgetter(0, 1))[-1]
  return '-'.join([str(x) for x in tag])


def do_tag():
  (last_tag_name, next_tag_name) = get_tags_name()

  if need_to_tag('HEAD', last_tag_name):
    local('git tag -a -m "tagging code for deployment" %s' % next_tag_name)
    env.deployment_tag = next_tag_name
  else:
    env.deployment_tag = last_tag_name


def need_to_tag(version1, version2):
  sha_version1 = local(
      'git log --pretty=format:%%H %s -1' % version1, capture=True)
  if version2:
    sha_version2 = local(
        'git log --pretty=format:%%H %s -1' % version2, capture=True)
    if sha_version1 == sha_version2:
      print yellow('No need to tag, the last %s tag is the same as the current')
      return False
  return True


def is_working_directory_clean():
  status = local('git status --short --ignore-submodules=untracked',
      capture=True)
  if status: # There are pending files.
    print red('Working directory not clean.')
    return False
  print yellow('Working directory clean.')
  return True


@include_appcfg
def get_tags_name():
  last_tag_name = get_last_tag_match()
  next = 0
  if last_tag_name:
    next = int(last_tag_name.split('-')[-1]) + 1
  next_tag_name = '%s-%d' % (env.app.version, next)
  print yellow('Last tag name: %s' % last_tag_name)
  print yellow('Next tag name: %s' % next_tag_name)
  return (last_tag_name, next_tag_name)
