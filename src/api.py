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
_AUTHORIZED_APPS = ['dev~ffc-app', 'ffc-app']


def get_films_from_query(q, cursor):
  """Create a search query for films from a query string.

  Args:
    q (str): The query string.
    cursor (str): The cursor.

  Return:
    SearchResults
  """

  query = search.Query(query_string=q)
  index = search.Index(name='films')

  return index.search(query)



class ApiHandler(webapp2.RequestHandler):

  def get(self):
    """Returns films JSON given a from partial string."""

    # When using urlfetch, make sure you set follow_redirects=False or the header does not get added.
    app_id = self.request.headers.get('X-Appengine-Inbound-Appid', None)
    logging.info('Access from addId: ', app_id)
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
        fields = {}
        for f in result.fields:
          fields[f.name] = f.value
        response_list.append({
          'key': result.doc_id,
          'title': fields['name'],
          'year': fields['release_date'].year,
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
