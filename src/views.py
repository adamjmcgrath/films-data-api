#!/usr/bin/python

"""Main views for films data api."""

__author__ = 'adamjmcgrath@gmail.com (Adam McGrath)'

import os

import jinja2
import webapp2

jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class HomePage(webapp2.RequestHandler):

  def get(self):
    """Shows the homepage."""
    template = jinja_env.get_template('templates/index.html')
    return webapp2.Response(template.render({}))
