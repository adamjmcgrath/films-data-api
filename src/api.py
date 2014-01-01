#!/usr/bin/python

"""Film data api handlers."""

__author__ = 'adamjmcgrath@gmail.com (Adam McGrath)'

import json
import logging
import re

import webapp2
from google.appengine.api import memcache, search, users

_SEARCH_LIMIT = 10
_VALID_CALLBACK = re.compile('^\w+(\.\w+)*$')
_AUTHORIZED_APPS = ['my-first-app', 'my-other-app']


def get_films_from_query(q, cursor):
  """docstring for get_films_from_query"""

  options = search.QueryOptions(
      limit=_SEARCH_LIMIT,
      cursor=cursor,
      returned_fields=['name', 'release_date'])

  query = search.Query(query_string=q, options=options)
  index = search.Index(name='films')

  return index.search(query)



class ApiHandler(webapp2.RequestHandler):
  """Returns JSON sugesting film titles given a starting string."""

  def get(self):
    # When using urlfetch, make sure you set follow_redirects=False or the header does not get added.
    app_id = self.request.headers.get('X-Appengine-Inbound-Appid', None)
    if app_id not in _AUTHORIZED_APPS and not users.is_current_user_admin():
      self.abort(403)

    debug = self.request.get('debug')
    callback = self.request.get('callback')
    q = self.request.get('q')
    cursor = self.request.get('cursor') or None
    add_callback = callback and _VALID_CALLBACK.match(callback)
    if not q:
      return webapp2.Response('')

    q = q.strip()
    memcached = memcache.get(q)

    self.response.headers['Content-Type'] = 'application/json; charset=utf-8'
    if memcached and not debug and not cursor:
      if add_callback:
        memcached = '%s(%s)' % (callback, memcached)
      return webapp2.Response(memcached)

    results = get_films_from_query(q, cursor).results

    if results:
      response_list = []
      for result in results:
        response_list.append({
          'key': result.doc_id,
          'title': result.fields[0].value, # TODO(adamjmcgrath) Get fields by name.
          'year': result.fields[1].value.year,
          'rank': result.rank
        })

      indent = 2 if debug else None
      response = json.dumps(response_list, indent=indent)
      if not debug:
        memcache.set(q, response)
      if add_callback:
        response = '%s(%s)' % (callback, response)

      return webapp2.Response(response)

    else:
      return webapp2.Response('')
