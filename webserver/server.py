#!/usr/bin/env python2.7
#%% 
"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response
import re

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)



# XXX: The Database URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/<DB_NAME>
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# For your convenience, we already set it to the class database

# Use the DB credentials you received by e-mail
DB_USER = "sk4819"
DB_PASSWORD = "1206"

DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/proj1part2"

#%% 
#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


# Here we create a test table and insert some values in it
engine.execute("""DROP TABLE IF EXISTS test;""")
engine.execute("""CREATE TABLE IF NOT EXISTS user_tmp (
  first_name text,
  surname text,
  contact_info text,
  description text,
  interests text,
  user_group text
);""")
# engine.execute("""INSERT INTO test(first_name, surname,contact_info,description,interests,user_group) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")


#%% 

@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """
  print(request.args)

  return render_template("index.html")


@app.route('/signup.html')
def signup():
  return render_template("signup.html")

@app.route('/feed.html')
def feed():
  cursor = g.conn.execute("SELECT first_name, last_name, contact_info FROM users")
  first_name_lst = []
  last_name_lst = []
  contact = []
  for obj in cursor:
    first_name_lst.append(obj[0])
    last_name_lst.append(obj[1])
    contact.append(obj[2])
  cursor.close()
  
  first_name_lst = [re.sub('_', ' ', obj) for obj in first_name_lst]
  names = []
  for first, last in zip(first_name_lst, last_name_lst):
    names.append(first + " " + last)
  
  data = []
  for name, email in zip(names, contact):
    data.append({'name': name, 'email': email, 'img': "https://randomuser.me/api/portraits/men/" + str(names.index(name))+ ".jpg"})

  return render_template("feed.html", data  = data)


# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
  fname = request.form['firstname-user']
  lname = request.form['lastname-user']
  contact_info = request.form['contact-user']
  desc = request.form['bio-user']
  interests = request.form.getlist('userinterests')
  print("______________")
  print(interests)
  print("______________")
  user_group = request.form['user_group']
  print(fname, lname, contact_info, desc, interests, user_group)
  cmd = 'INSERT INTO user_tmp(first_name, surname, contact_info, description, interests, user_group) VALUES ((:fname), (:lname), (:contact_info), (:desc), (:interests), (:user_group))';
  g.conn.execute(text(cmd), fname = fname, lname = lname, contact_info = contact_info, desc = desc, interests = interests, user_group = user_group);

  if user_group == 'Student':
    return redirect('/student_signup.thml') ## Input next page link
  elif user_group == 'Employee':
    return redirect('/employee_signup.thml')


@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()