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
from flask import Flask, request, render_template, g, redirect, Response, flash
import re

from flask import Flask, request, render_template, g, redirect, Response, jsonify, url_for

from flask_wtf import FlaskForm
from wtforms import SelectField

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

SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
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

@app.route('/login', methods=['POST'])
def login_user():
  username = request.form['uname']
  password = request.form['psw']
  cmd = 'SELECT COUNT(*) FROM users WHERE user_id = (:username) AND first_name = (:password)';
  cnt = g.conn.execute(text(cmd), username = username, password = password);
  cnt = cnt.fetchall()
  cnt = cnt[0][0]
  print(cnt)
  if cnt == 0:
    flash('Invalid Username or Password')
    return redirect('/') ## Input next page link
  elif cnt == 1:
    flash('Redirecting')
    return redirect('/feed.html')



@app.route('/signup.html')
def signup():
  return render_template("signup.html")

@app.route('/feed.html')
def feed():
  cursor = g.conn.execute("SELECT first_name, last_name, description FROM users")
  first_name_lst = []
  last_name_lst = []
  desc = []
  for obj in cursor:
    first_name_lst.append(obj[0])
    last_name_lst.append(obj[1])
    desc.append(obj[2])
  cursor.close()
  
  first_name_lst = [re.sub('_', ' ', obj) for obj in first_name_lst]
  names = []
  for first, last in zip(first_name_lst, last_name_lst):
    names.append(first + " " + last)
  
  data = []
  for name, bio in zip(names, desc):
    data.append({'name': name, 'bio': bio, 'img': "https://xsgames.co/randomusers/assets/avatars/pixel/" + str(names.index(name))+ ".jpg"})

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
    return redirect('/student_signup.html') ## Input next page link
  elif user_group == 'Employee':
    return redirect('/employee_signup.html')


@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()


class PositionForm(FlaskForm):
    company_name = SelectField('company_name', choices = [])
    position_title = SelectField('position_title', choices=[])
    tool = SelectField('tools', choices=[])


def populate_form(form):
    skills_list = ['Python', 'Java', 'C++', 'C', 'C#', 'UI/UX design','Data Analysis',
                    'Machine Learning', 'Data Engineering', 'Data Visualization', 'Video Editing',
                    'CRMs','Cloud Computing','Big Data', 'Data Science']
    skills_list.sort()
    skills_list.insert(0,None)

    # get position data
    q="""
        SELECT a.position_title
        , a.company_id
        , b.company_name
        FROM Position a
        inner join Company b on a.company_id=b.company_id
        ;
        """

    cursor_p = g.conn.execute(q)
    positions_list = cursor_p.fetchall()

    company_set = set([(position_t['company_id'], position_t['company_name']) for position_t in positions_list])
    form.company_name.choices = [(0, None)] + sorted(list(company_set))
    form.position_title.choices = [None] + [(position_t['position_title']) for position_t in positions_list]
    form.tool.choices = skills_list

    return form

@app.route("/student_signup", methods=['GET','POST'])
def student_signup():

    user_id = request.args['user_id']
    
    form = PositionForm()
    form = populate_form(form)
    
    if request.method=='POST':
        pos = form.position_title.data
        company = form.company_name.data
        tool = form.tool.data

        q_insert_skill = f"""
        INSERT INTO StudentInterestTemp(user_id, position_title, company_id) VALUES (
            '{user_id}',
            '{pos}',
            {company}
        )
        """

        q_insert_interest = f"""
        INSERT INTO StudentTemp(user_id, skills) VALUES(
            '{user_id}',
            '{tool}'
        )
        """

        try:
            g.conn.execute(q_insert_skill)
        except:
            pass
        
        try:
            g.conn.execute(q_insert_interest)
        except:
            pass

        q_fetch_interest = f"""
        SELECT a.position_title, b.company_name
        FROM StudentInterestTemp a
        INNER JOIN Company b on a.company_id = b.company_id 

        where user_id = '{user_id}'
        ;
        """
        cursor = g.conn.execute(q_fetch_interest)
        recorded_interests= cursor.fetchall()


        return render_template("student_signup.html", form = form, recorded_interests=recorded_interests)

    return render_template("student_signup.html", form = form)


@app.route('/position_title/<company_id>')
def position_title(company_id):
    position =  q="""
                    SELECT 
                        a.position_title
                    FROM Position a
                    where company_id={}
                    ;
                    """.format(company_id)
    titles = g.conn.execute(q).fetchall()

    posArray = []
    for title in titles:
        title_elem = {}
        title_elem['title'] = title.position_title
        posArray.append(title_elem)

    return jsonify({'position_title': posArray})


@app.route("/employee_signup", methods=['GET','POST'])
def employee_signup():

    user_id = request.args['user_id']

    # fetch a list of available companies
    cursor = g.conn.execute('SELECT company_name, company_id FROM company;') 
    company_list = cursor.fetchall()

    if request.method=='POST':
        pos = request.form.get('position')
        company_id = request.form.get('company_list')

        q_insert_employee = f"""
        INSERT INTO EmployeeTemp(user_id, position, company_id) VALUES (
            '{user_id}',
            '{pos}',
            {company_id}
        )
        """        
        try:
            g.conn.execute(q_insert_employee)
        except:
            pass

        return redirect(url_for('index'))

    return render_template("employee_signup.html",company_list=company_list)



@app.route("/save_interest", methods=['POST'])
def save_interest():

    user_id = request.form.get('user_id')
    pos = request.form.get('position_title')
    company = request.form.get('company_name')

    q_insert_skill = f"""
        INSERT INTO Student_Interest(student_id, position_title, company_id)
            Select student_id,
            '{pos}',
            {company}
            from users u
            where user_id='{user_id}' 
    """

    try:
        g.conn.execute(q_insert_skill)
    except:
        pass

    return redirect(request.referrer)


@app.route("/save_profile", methods=['POST'])
def save_profile():

    user_id = request.form.get('user_id')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    contact_info = request.form.get('contact_info')
    description = request.form.get('description')
    # replace a single quote with double quote
    description = (description.replace("'","''")).strip()

    q_update_profile = f"""
        UPDATE Users
        SET first_name='{first_name}'
            , last_name='{last_name}'
            , contact_info='{contact_info}'
            , description='{description}'
        WHERE user_id='{user_id}'
        ;
    """

    try:
        g.conn.execute(q_update_profile)
    except:
        pass

    return redirect(request.referrer)


@app.route("/student_profile", methods=['GET','POST'])
def student_profile():

    user_id = request.args['user_id']

    form = PositionForm()
    form = populate_form(form)

    q_basic_info = f"""        
        select a.user_id
            , a.student_id
            , a.employee_id        
            , a.first_name
            , a.last_name
            , a.contact_info
            , b.school_name
            , s.skills
            , c.company_name
            , e.position
            , a.description
        from users a
        inner join school b on a.school_id = b.school_id
        left join student s on s.user_id = a.user_id
        left join employee e on e.user_id = a.user_id
        left join company c on c.company_id = e.company_id
        where a.user_id='{user_id}'
        ;
    """

    cursor = g.conn.execute(q_basic_info)
    profile_info = cursor.fetchall()

    q_refer_information = f"""
            select 
                c.position_title
                , co.company_name
            from users a 
            inner join student b on a.user_id = b.user_id
            inner join student_interest c on b.student_id = c.student_id
            inner join company co on co.company_id = c.company_id
            where a.user_id='{user_id}'
    """

    cursor = g.conn.execute(q_refer_information)
    job_info = cursor.fetchall()

    return render_template("student_profile.html", profile_info=profile_info, job_info=job_info, form=form, user_id=user_id)


@app.route("/employee_profile", methods=['GET','POST'])
def employee_profile():

    user_id = request.args['user_id']

    form = PositionForm()
    form = populate_form(form)

    q_basic_info = f"""        
        select a.user_id
            , a.student_id
            , a.employee_id        
            , a.first_name
            , a.last_name
            , a.contact_info
            , b.school_name
            , s.skills
            , c.company_name
            , e.position
            , a.description
        from users a
        inner join school b on a.school_id = b.school_id
        left join student s on s.user_id = a.user_id
        left join employee e on e.user_id = a.user_id
        left join company c on c.company_id = e.company_id
        where a.user_id='{user_id}'
        ;
    """

    cursor = g.conn.execute(q_basic_info)
    profile_info = cursor.fetchall()

    q_refer_information = f"""
            SELECT s.user_id as referred_user
            , r.position_title
            , c.company_name
        from refer r
        inner join employee e on r.employee_id = e.employee_id
        inner join users u_emp on u_emp.user_id = e.user_id
        inner join company c on r.company_id = c.company_id

        left join student s on s.student_id = r.student_id
        left join users u on u.user_id = s.user_id
        where u_emp.user_id='{user_id}'
        """
    cursor = g.conn.execute(q_refer_information)
    job_info = cursor.fetchall()


    return render_template("employee_profile.html", profile_info = profile_info, job_info = job_info, form=form, user_id=user_id)

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