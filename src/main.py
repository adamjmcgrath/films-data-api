#!/usr/bin/python

"""Main handlers for films data api."""

__author__ = 'adamjmcgrath@gmail.com (Adam McGrath)'

import webapp2
import api
import tasks
import views


app = webapp2.WSGIApplication([
    ('/', views.HomePage),
    ('/tasks/getfilms/(\d{4})', tasks.GetFilmsByYear),
    ('/tasks/getyear', tasks.GetYear),
    ('/api/?', api.ApiHandler),
], debug=True)
