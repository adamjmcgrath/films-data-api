#!/usr/bin/python

"""Models for the films data API."""

__author__ = 'adamjmcgrath@gmail.com (Adam McGrath)'

import datetime

from google.appengine.ext import ndb



class CurrentYear(ndb.Model):
  """Store the current year as an int in the datastore. The current year is the year of films being processed.

  Attributes:
    year: The year.
  """
  year = ndb.IntegerProperty()

  @staticmethod
  def get_current_year():
    """ Get the current year stored in the datastore, if one isn't there - store the current year.

    Return:
      int
    """
    current_year = CurrentYear.query().get()
    if current_year:
      return current_year.year
    else:
      year = int(datetime.datetime.now().strftime('%Y'))
      CurrentYear.set_current_year(year)
      return year

  @staticmethod
  def set_current_year(year):
    """ Set the current year stored in the datastore.

    Args:
      year (int): The year to store.
    """
    current_year = CurrentYear.query().get()
    if current_year:
      current_year.year = year
    else:
      current_year = CurrentYear(year=year)
    current_year.put()

  @staticmethod
  def clear_current_year():
    """ Remove the current year from the datastore """
    current_year = CurrentYear.query().get(keys_only=True)
    if current_year:
      current_year.delete()


