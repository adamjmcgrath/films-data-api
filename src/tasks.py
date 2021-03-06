#!/usr/bin/python

"""Task handlers for films data api."""

__author__ = 'adamjmcgrath@gmail.com (Adam McGrath)'

import datetime
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
import json
import logging
import urllib

import webapp2
from google.appengine.api import search, taskqueue, urlfetch

import models
import secrets


LANG = '/lang/en'
BASE_URL = 'https://www.googleapis.com/freebase/v1/mqlread/'
ISO_DATE_FORMAT = '%Y-%m'
MIN_YEAR = 1960
DEFAULT_DATE = datetime.date(2000, 1, 1)
MQL = '''[{
  "ns0:initial_release_date": [{
    "type": "/type/datetime",
    "value": null,
    "value>=": "%s"
  }],
  "ns1:initial_release_date": [{
    "type": "/type/datetime",
    "value": null,
    "value<": "%s"
  }],
  "id": null,
  "initial_release_date": null,
  "limit": 100,
  "name": null,
  "type": "/film/film",
  "gross_revenue": {
      "amount": null,
      "optional": true
  },
  "imdb_id": {
      "value": null,
      "limit": 1,
      "optional": true
  },
  "forbid:genre": {
    "id|=": [
      "/en/gay_pornography",
      "/en/pornographic_movie"
    ],
    "optional": "forbidden"
  }
}]'''


def tokenize(phrase):
  """ Create a list of partial tokens from s string. eg
  dog -> [d, do, dog]

  Args:
    phrase (str): The phrase to tokenize

  Return:
    list The list of tokens.
  """
  a = []
  for word in phrase.lower().split():
    j = 1
    while True:
      for i in range(len(word) - j + 1):
        a.append(word[i:i + j])
      if j == len(word):
        break
      j += 1
  return a


def create_film_document(film):
  """ Creates a film document from a json dictionary of film data from Freebase.

  Args:
    film (dict): The film dictionary.

  Return:
    search.Document
  """
  tokens = ','.join(tokenize(film['name']))
  imdb_id = film['imdb_id'] and film['imdb_id']['value']
  gross_revenue = int(film['gross_revenue'] and film['gross_revenue']['amount'] or 0)
  release_date = parse(film['initial_release_date'], default=DEFAULT_DATE)
  film_name = film['name']

  return search.Document(doc_id=film['id'],
                         # Rank films by gross revenue, then by length of name desc.
                         rank=max(gross_revenue, 1000 - len(film_name)),
                         language='en',
                         fields=[
                             search.TextField(name='name', value=film_name),
                             search.TextField(name='tokens', value=tokens),
                             search.TextField(name='imdb_id', value=imdb_id),
                             search.NumberField(name='gross_revenue', value=gross_revenue),
                             search.DateField(name='release_date', value=release_date)
                         ])


def index_films(films):
  """ Add the films JSON to the index.

  Args:
    films (list): A list of film data from Freebase.
  """
  docs = []

  for film in films:
    if not film['name']:
      continue
    try:
      docs.append(create_film_document(film))
    except Exception as e:
      logging.error('Error creating film: %s, %s', film['id'], e)

  index = search.Index(name='films')
  index.put(docs)


class GetYear(webapp2.RequestHandler):

  def get(self):
    """Get the next year to scrape films from freebase."""
    year = models.CurrentYear.get_current_year()
    previous_year = year - 1
    if previous_year < MIN_YEAR:
      models.CurrentYear.clear_current_year()
    else:
      models.CurrentYear.set_current_year(previous_year)
      taskqueue.add(url='/tasks/getfilms/%d' % year, method='GET', queue_name='films')


class GetFilmsByYear(webapp2.RequestHandler):

  def get(self, year):
    """Get films from the Freebase API."""
    cursor = self.request.get('cursor', default_value='')
    first_day = datetime.date(int(year), 1, 1)
    last_day = datetime.date(int(year), 12, 31)
    now = datetime.datetime.now().date()
    from_date_param = self.request.get('from_date', default_value=first_day.strftime(ISO_DATE_FORMAT))

    from_date = parse(from_date_param, default=DEFAULT_DATE)
    to_date = from_date + relativedelta(months=+1)

    if from_date > last_day or from_date > now:
      logging.info('Got films for: %s' % year)
      return

    from_date_str = from_date.strftime(ISO_DATE_FORMAT)
    to_date_str = to_date.strftime(ISO_DATE_FORMAT)

    mql = MQL % (from_date_str, to_date_str)

    logging.info('Getting films from %s to %s', from_date_str, to_date_str)

    params = urllib.urlencode({
      'lang': LANG,
      'cursor': cursor,
      'query': json.dumps(json.loads(mql)),
      'key': secrets.API_KEY
    })
    response = urlfetch.fetch('%s?%s' % (BASE_URL, params), deadline=30)
    films_json = json.loads(response.content)

    try:
      index_films(films_json['result'])
    except KeyError:
      logging.error('Freebase response error: ', json.dumps(films_json, indent=2))

    next_cursor = films_json.get('cursor', '')

    if next_cursor:
      params = {'from_date': from_date, 'cursor': next_cursor}
    else:
      params = {'from_date': to_date}

    taskqueue.add(url='/tasks/getfilms/%s' % year, params=params, method='GET', queue_name='films')
