#!/usr/bin/python

"""Main views for films data api."""

__author__ = 'adamjmcgrath@gmail.com (Adam McGrath)'

import logging
import os

import jinja2
import webapp2


jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class HomePage(webapp2.RequestHandler):
  """Shows the homepage."""

  def get(self):
    logging.info(self.request.headers.get('X-Appengine-Inbound-Appid', None))

    template = jinja_env.get_template('templates/index.html')
    return webapp2.Response(template.render({}))
