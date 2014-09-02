#!/usr/bin/python

"""Film data api handlers."""

__author__ = 'adamjmcgrath@gmail.com (Adam McGrath)'

import json
import re

import webapp2
from google.appengine.api import memcache, search, users

_SEARCH_LIMIT = 10
_VALID_CALLBACK = re.compile('^\w+(\.\w+)*$')
_AUTHORIZED_APPS = ['dev~ffc-app', 'ffc-app']


def get_films_from_query(q, limit=None):
  """Create a search query for films from a query string.

  Args:
    q (str): The query string.
    cursor (str): The cursor.

  Return:
    SearchResults
  """
  limit = int(limit or _SEARCH_LIMIT)
  query = search.Query(query_string=q,
                       options=search.QueryOptions(limit=limit))
  index = search.Index(name='films')

  return index.search(query)


def get_film_from_id(id):
  """Get films by their id.

  Args:
    id (str): The doc id.
  """

  index = search.Index(name='films')

  return index.get(id)


def doc_to_dict(doc):
  """Create a dictionary for json conversion from a search document.

  Args:
    SearchDocument

  Return:
    dict
  """
  fields = {}
  for f in doc.fields:
    fields[f.name] = f.value
  return {
    'key': doc.doc_id,
    'title': fields['name'],
    'year': fields['release_date'].year,
    'rank': doc.rank
  }


class ApiHandler(webapp2.RequestHandler):

  def get(self):
    """Returns films JSON given a from partial string."""
    self.response.headers['Content-Type'] = 'application/json; charset=utf-8'

    debug = self.request.get('debug')
    indent = 2 if debug else None
    response = ''

    callback = self.request.get('callback')
    q = self.request.get('q').strip()
    id = self.request.get('id').strip()
    limit = self.request.get('limit').strip()
    add_callback = callback and _VALID_CALLBACK.match(callback)

    if not q and not id:
      return webapp2.Response('')

    memcached = memcache.get(q)
    if memcached and not debug:
      if add_callback:
        memcached = '%s(%s)' % (callback, memcached)
      return webapp2.Response(memcached)

    if q:
      results = get_films_from_query(q, limit=limit).results

      if results:
        response_list = []
        for result in results:
          response_list.append(doc_to_dict(result))


        response = json.dumps(response_list, indent=indent)

    if id:
      result = get_film_from_id(id)
      response = json.dumps(doc_to_dict(result), indent=indent)

    if not debug:
      memcache.set(q or id, response)

    if add_callback:
      response = '%s(%s)' % (callback, response)

    return webapp2.Response(response)

