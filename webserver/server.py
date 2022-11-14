#!/usr/bin/env python2.7
#%% 
"""

Columbia W4111 Intro to Databases Project Part 3
Author: Gyung Hyun Je, Shrey Kothari

"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, flash, session
import re

from flask import Flask, request, render_template, g, redirect, Response, jsonify, url_for

from flask_wtf import FlaskForm
from wtforms import SelectField
from datetime import timedelta

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


# Use the DB credentials you received by e-mail
DB_USER = "sk4819"
DB_PASSWORD = "1206"

DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/proj1part2"

SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
engine = create_engine(DATABASEURI)


# Here we create a test table and insert some values in it
# engine.execute("""DROP TABLE IF EXISTS user_tmp;""")
engine.execute("""CREATE TABLE IF NOT EXISTS user_tmp (
    user_id varchar PRIMARY KEY,
    password varchar,
    first_name text,
    last_name text,
    contact_info text,
    description text,
    school_id int,
    interests text,
    user_group text,
    skills varchar,
    position varchar,
    company_id int,
    FOREIGN KEY (company_id) REFERENCES Company(company_id),
    completed bool default false
);""")

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


@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=10)


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


@app.route('/')
def index():
  session.clear()
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
  cmd = 'SELECT COUNT(*) FROM users WHERE user_id = (:username) AND password = (:password)';
  cnt = g.conn.execute(text(cmd), username = username, password = password);
  cnt = cnt.fetchall()
  cnt = cnt[0][0]
  session['userid'] = username
  if cnt == 0:
    data = ["Invalid username or password!"]
    return render_template('index.html', data = data) ## Input next page link
  elif cnt == 1:
    return redirect('/feed.html')


@app.route('/signup.html')
def signup():
  school_q = 'SELECT school_id, school_name FROM school';
  school =  g.conn.execute(text(school_q));
  schools = []
  for obj in school:
      schools.append({'id':obj[0], 'name':obj[1]})
  return render_template("signup.html", schools = schools)


@app.route('/feed.html')
def feed():
    try:
        if session['user_group'] =='Student':
            user_group = [[1, None]]
        elif session['user_group'] =='Employee':
            user_group = [[None, 1]]
    except KeyError:
        q = 'SELECT student_id, employee_id FROM users WHERE user_id = (:userid)';
        user_group = g.conn.execute(text(q), userid = session['userid']); #session['userid']
        user_group = user_group.fetchall()
        
        
    data = []
    # If the user is a student
    if type(user_group[0][0]) == int:
        filter_lst = []
        filter_q = "SELECT DISTINCT company_name FROM company";
        filter_cursor = g.conn.execute(filter_q)
        for obj in filter_cursor:
            filter_lst.append(obj[0])
        
        session['user_group'] = 'Student'
        cursor = g.conn.execute("SELECT  u.first_name, u.last_name, u.description, e.position, c.company_name, u.user_id FROM employee e LEFT JOIN users u ON e.employee_id = u.employee_id LEFT JOIN company c ON e.company_id = c.company_id;")
        first_name_lst = []
        last_name_lst = []
        desc = []
        position = []
        company = []
        userid = []
        for obj in cursor:
            first_name_lst.append(obj[0])
            last_name_lst.append(obj[1])
            desc.append(obj[2])
            position.append(obj[3])
            company.append(obj[4])
            userid.append(obj[5])
        cursor.close()
        
        first_name_lst = [re.sub('_', ' ', obj) for obj in first_name_lst]
        names = []
        for first, last in zip(first_name_lst, last_name_lst):
         names.append(first + " " + last)
        pos_key = "Position"
        co_key = "Company"
        
        for name, bio, pos, co, id in zip(names, desc, position, company, userid):
            data.append({'name': name, 'bio': bio, 
                        'img': "https://xsgames.co/randomusers/assets/avatars/pixel/" + str(names.index(name))+ ".jpg",
                        'position': pos, 'company':co, 'pos_key': pos_key, 'co_key': co_key, 'id':id})
    
    # If user is an employee
    elif user_group[0][0] == None:
        filter_lst = []
        filter_q = "SELECT DISTINCT skills FROM student;";
        filter_cursor = g.conn.execute(filter_q)
        for obj in filter_cursor:
            filter_lst.append(obj[0])
        
        session['user_group'] = 'Employee'
        cursor = g.conn.execute("SELECT  u.first_name, u.last_name, u.description, s.skills, sl.school_name, u.user_id FROM student s LEFT JOIN users u ON s.student_id = u.student_id LEFT JOIN school sl ON u.school_id = sl.school_id;")
        first_name_lst = []
        last_name_lst = []
        desc = []
        position = []
        company = []
        userid = []
        for obj in cursor:
            first_name_lst.append(obj[0])
            last_name_lst.append(obj[1])
            desc.append(obj[2])
            company.append(obj[3])
            position.append(obj[4])
            userid.append(obj[5])
        cursor.close()
        
        first_name_lst = [re.sub('_', ' ', obj) for obj in first_name_lst]
        names = []
        for first, last in zip(first_name_lst, last_name_lst):
         names.append(first + " " + last)
        
        pos_key = "Skills"
        co_key = "School"
        
        for name, bio, pos, co, id in zip(names, desc, position, company, userid):
            data.append({'name': name, 'bio': bio, 
                        'img': "https://xsgames.co/randomusers/assets/avatars/pixel/" + str(names.index(name))+ ".jpg",
                        'position': pos, 'company':co, 'pos_key': co_key, 'co_key': pos_key, 'id':id})
    print(filter_lst)
    return render_template("feed.html", data  = data, filter_lst = filter_lst)


@app.route('/filter', methods=['POST'])
def filter():
    
    filter_val = request.form['filter-user']
    print(filter_val)
    if (filter_val != 'all') and (session['user_group'] == 'Student'):
        q = "SELECT  u.first_name, u.last_name, u.description, e.position, c.company_name, u.user_id FROM employee e LEFT JOIN users u ON e.employee_id = u.employee_id LEFT JOIN company c ON e.company_id = c.company_id WHERE c.company_name = (:filter_val)";
        cursor = g.conn.execute(text(q), filter_val = filter_val);
        print(("SELECT  u.first_name, u.last_name, u.description, e.position, c.company_name, u.user_id FROM employee e LEFT JOIN users u ON e.employee_id = u.employee_id LEFT JOIN company c ON e.company_id = c.company_id WHERE c.company_name ={}").format(filter_val))
        data = []
        first_name_lst = []
        last_name_lst = []
        desc = []
        position = []
        company = []
        userid = []
        for obj in cursor:
            first_name_lst.append(obj[0])
            last_name_lst.append(obj[1])
            desc.append(obj[2])
            position.append(obj[3])
            company.append(obj[4])
            userid.append(obj[5])
        cursor.close()
        
        first_name_lst = [re.sub('_', ' ', obj) for obj in first_name_lst]
        names = []
        for first, last in zip(first_name_lst, last_name_lst):
            names.append(first + " " + last)
        pos_key = "Position"
        co_key = "Company"
        
        for name, bio, pos, co, id in zip(names, desc, position, company, userid):
            data.append({'name': name, 'bio': bio, 
                        'img': "https://xsgames.co/randomusers/assets/avatars/pixel/" + str(names.index(name))+ ".jpg",
                        'position': pos, 'company':co, 'pos_key': pos_key, 'co_key': co_key, 'id':id})
                
            
        return render_template("feed.html", data  = data)
        
    elif (filter_val != 'all') and (session['user_group'] == 'Employee'):
        q = f"SELECT  u.first_name, u.last_name, u.description, s.skills, sl.school_name, u.user_id FROM student s LEFT JOIN users u ON s.student_id = u.student_id LEFT JOIN school sl ON u.school_id = sl.school_id WHERE s.skills = '{filter_val}'";
        cursor = g.conn.execute(text(q));
        print(q)
        data = []
        first_name_lst = []
        last_name_lst = []
        desc = []
        position = []
        company = []
        userid = []
        for obj in cursor:
            first_name_lst.append(obj[0])
            last_name_lst.append(obj[1])
            desc.append(obj[2])
            company.append(obj[3])
            position.append(obj[4])
            userid.append(obj[5])
        cursor.close()
        
        first_name_lst = [re.sub('_', ' ', obj) for obj in first_name_lst]
        names = []
        for first, last in zip(first_name_lst, last_name_lst):
          names.append(first + " " + last)
        
        pos_key = "Skills"
        co_key = "School"
        
        for name, bio, pos, co, id in zip(names, desc, position, company, userid):
            data.append({'name': name, 'bio': bio, 
                        'img': "https://xsgames.co/randomusers/assets/avatars/pixel/" + str(names.index(name))+ ".jpg",
                        'position': pos, 'company':co, 'pos_key': co_key, 'co_key': pos_key, 'id':id})
        return render_template("feed.html", data  = data)
    
    elif filter_val == 'all':
        print('ALL FILTER VALUE')
        return redirect("/feed.html")
        

# Example of adding new data to the database
@app.route('/add', methods=['POST'])
def add():
    school_q = 'SELECT school_id, school_name FROM school';
    school =  g.conn.execute(text(school_q));
    schools = []
    for obj in school:
        schools.append({'id':obj[0], 'name':obj[1]})
    username = request.form['username-user']
    password = request.form['password-user']
    verify_pass = request.form['verify-password-user']
    fname = request.form['firstname-user']
    lname = request.form['lastname-user']
    contact_info = request.form['contact-user']
    desc = request.form['bio-user']
    school = request.form['school-user']
    interests = request.form.getlist('userinterests')
    if password != verify_pass:
        data = ["Passwords do not match! Try again..."]
        return render_template('signup.html', data = data, schools = schools)
    else:
        user_group = request.form['user_group']
        # print(fname, lname, contact_info, desc, interests, user_group)
        cmd = 'INSERT INTO user_tmp(user_id, password, first_name, last_name, contact_info, description, school_id, interests, user_group, skills, position, company_id) VALUES ((:username), (:password), (:fname), (:lname), (:contact_info), (:desc), (:school), (:interests), (:user_group), (:skills), (:position), (:company))';
        g.conn.execute(text(cmd), username = username, password = password, fname = fname, lname = lname, contact_info = contact_info, desc = desc, school = school, interests = interests, user_group = user_group, skills = None, position = None, company = None);
        
        session['userid'] = username
        print("Session userid:", session['userid'])
        
        if user_group == 'Student':
            return redirect(url_for('student_signup')) ## Input next page link
        elif user_group == 'Employee':
            return redirect(url_for('employee_signup'))


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
    userid = session['userid']
    
    form = PositionForm()
    form = populate_form(form)
    
    if request.method=='POST':
        pos = form.position_title.data
        company = form.company_name.data
        tool = form.tool.data

        if company != None and pos != None:
            q_insert_skill = f"""
            INSERT INTO StudentInterestTemp(user_id, position_title, company_id) VALUES (
                '{userid}',
                '{pos}',
                {company}
            )
            """

            try:
                g.conn.execute(q_insert_skill)
            except:
                pass
            
        if tool != None:
            q_insert_interest = f"""
            UPDATE user_tmp
            SET skills = '{tool}'
            WHERE user_id='{userid}'
            """

            try:
                g.conn.execute(q_insert_interest)
            except:
                pass

        q_fetch_interest = f"""
        SELECT a.position_title, b.company_name
        FROM StudentInterestTemp a
        INNER JOIN Company b on a.company_id = b.company_id 
        where user_id = '{userid}'
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

    userid = session['userid']

    # fetch a list of available companies
    cursor = g.conn.execute('SELECT company_name, company_id FROM company;') 
    company_list = cursor.fetchall()

    if request.method=='POST':
        pos = request.form.get('position')
        company_id = request.form.get('company_list')

        q_insert_employee = f"""
        UPDATE user_tmp
        SET position='{pos}',
            company_id={company_id},
            completed=true
        WHERE user_id='{userid}'
        """

        try:
            g.conn.execute(q_insert_employee)
        except:
            pass

        return redirect(url_for('complete_signup'))

    return render_template("employee_signup.html",company_list=company_list)


@app.route("/save_interest", methods=['POST'])
def save_interest():

    user_id = request.form.get('user_id')
    pos = request.form.get('position_title')
    company = request.form.get('company_name')

    q_insert_skill = f"""
        INSERT INTO Student_Interest(student_id, position_title, company_id)
            select student_id,
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


@app.route("/complete_signup", methods=['GET','POST'])
def complete_signup():

    userid = session['userid']

    # drop records in the user_tmp at various points in the funnel
    q_drop_check = f"""
        delete from user_tmp
        where user_id = '{userid}'
        ;
    """

    q_user_info = f"""
      UPDATE user_tmp
      SET completed=true
      where user_id = '{userid}'
    """
    try:
        g.conn.execute(q_user_info)
    except:
        g.conn.execute(q_drop_check)
        flash("Registration did not go through :( ", "error")
        return redirect(request.referrer)


    # write everything in the user_temp to perm user table
    q_user_info = f"""
      INSERT INTO USERS
      SELECT
        user_id
        , first_name
        , last_name
        , contact_info
        , case when user_group='Student' then (select max(student_id)+1 from student) else null end
        , case when user_group='Employee' then (select max(employee_id)+1 from employee) else null end
        , school_id
        , description
        , interests
        , password
      FROM user_tmp a
      WHERE user_id = '{userid}' and completed=true
      ;
    """

    try:
        g.conn.execute(q_user_info)
    except:
        g.conn.execute(q_drop_check)
        flash("Registration did not go through :( ", "error")
        return redirect(request.referrer)

    q_group = f"""
        SELECT
            user_group
        FROM user_tmp
        WHERE user_id='{userid}' and completed=true
    """

    user_group = dict((g.conn.execute(q_group).fetchall())[0])['user_group']

    if user_group=='Student':
        # first insert the record into student table
        q_student = f"""
            INSERT INTO student
            SELECT 
                a.student_id
                , b.skills
                , a.user_id
            FROM USERS a
            INNER JOIN user_tmp b on a.user_id=b.user_id and b.completed=true
            WHERE a.user_id='{userid}'
            ;
        """
        try:
            g.conn.execute(q_student)
        except:
            g.conn.execute(q_drop_check)
            flash("Registration did not go through :( ", "error")
            return redirect(request.referrer)

        # record student interest in the student_interest table
        q_student_interst = f"""
            INSERT INTO student_interest
            SELECT
                s.student_id
                , a.position_title
                , a.company_id
            FROM studentinteresttemp a
            INNER join student s on s.user_id=a.user_id
            WHERE a.user_id='{userid}'
            ;
        """
        try:
            g.conn.execute(q_student_interst)
        except:
            g.conn.execute(q_drop_check)
            flash("Registration did not go through :( ", "error")
            return redirect(request.referrer)


    elif user_group=='Employee':
        # insert the value into the employee table

        # first insert the record into student table
        q_employee = f"""
            INSERT INTO employee
            SELECT 
                a.employee_id
                , b.position
                , a.user_id
                , b.company_id
            FROM USERS a
            INNER JOIN user_tmp b on a.user_id=b.user_id and b.completed=true
            WHERE a.user_id='{userid}'
            ;
        """
        try:
            g.conn.execute(q_employee)
        except:
            g.conn.execute(q_drop_check)
            flash("Registration did not go through :( ", "error")
            return redirect(request.referrer)

    # drop records in the user_tmp
    g.conn.execute(q_drop_check)

    # finally check if the record has successfully been inserted to user table AND (student OR employee table)
    q_check_success=f"""
    select user_id
    from users
    where user_id in (
                select u.user_id
                from users u
                left join student s on u.user_id = s.user_id
                left join employee e on u.user_id = e.user_id
                where (s.user_id is not null or e.user_id is not null)
                )
        and user_id = '{userid}'
    """

    try:
        g.conn.execute(q_check_success)
        flash("Registration success!", "info")
    except:
        pass

    return redirect(url_for('index'))


@app.route('/profile/<user_id>', methods=['GET', 'POST'])
def view_profile(user_id):

    q_profile = f"""
        select
            a.user_id
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
            , trim(trim(a.interests, '}}'), '{{') as interests
        from users a
        inner join school b on a.school_id = b.school_id
        left join student s on s.user_id = a.user_id
        left join employee e on e.user_id = a.user_id
        left join company c on c.company_id = e.company_id
        where a.user_id='{user_id}'
        ;
    """

    cursor = g.conn.execute(q_profile)
    data = dict(cursor.fetchall()[0])
    

    is_student = data['student_id']
    user_group=""
    if is_student:
        data['user_group']="student"
        
        q_student_interest = f"""
        select 
            c.position_title
            , co.company_name as interested_company
            , co.company_id
        from users a 
        inner join student b on a.user_id = b.user_id
        inner join student_interest c on b.student_id = c.student_id
        inner join company co on co.company_id = c.company_id
        where a.user_id='{user_id}' and c.require_referral = true
        """

        cursor = g.conn.execute(q_student_interest)
        student_data = cursor.fetchall()

        data['interested_position'] = [(i[0],i[1],i[2]) for i in student_data]
   
        print(data)
        return render_template("profile_view_student.html", data = data)

    else:
        data['user_group']="employee"

        print(data)
        return render_template("profile_view_employee.html", data = data)


@app.route('/like', methods=['POST'])
def send_like():

    userid = session['userid']
    employee_liked_userid = request.form.get('employee_liked')

    q_like=f"""
        INSERT INTO student_like
        select 
            u.student_id
            , (select employee_id from users where user_id='{employee_liked_userid}')
        from users u
        where u.user_id='{userid}'
    """

    try:
        g.conn.execute(q_like)
        flash('Like successfully sent!', 'info')

    except:
        print("Did not save the like information successfully!")
        flash('You already sent the like!', 'error')


    return redirect(request.referrer)


@app.route('/refer', methods=['POST'])
def refer():

    referee_user_id = request.form.get('refer_user_id')
    company_interested = request.form.get('company_interested')
    position_interested = request.form.get('position_interested')
    referrer_user_id = session['userid']

    #check if the employee works at the same company as the interested company
    q_check = f"""select company_id from employee where user_id='{referrer_user_id}'"""
    referrer_company = g.conn.execute(q_check).fetchall()[0][0]

    if int(referrer_company) != int(company_interested):
        flash(f"You can only refer students for positions in your company", "error")
        return redirect(request.referrer) 

    q_refer = f"""
        INSERT INTO refer
        SELECT
            e.employee_id
            , (select student_id from student where user_id = '{referee_user_id}')
            , '{position_interested}'
            , {company_interested}
        FROM users u
        INNER join employee e on u.user_id = e.user_id
        WHERE u.user_id='{referrer_user_id}'
        ;
    """

    try:
        g.conn.execute(q_refer)

        q_reset_refer_require = f"""
            UPDATE student_interest
            SET require_referral = false
            WHERE student_id in (select student_id from student where user_id = '{referee_user_id}')
                and position_title = '{position_interested}'
                and company_id = {company_interested}
        """

        g.conn.execute(q_reset_refer_require)

        flash("Your contact information has been sent to the student!", "info")
    except:
        flash("System error: message not sent to the student.", "error")

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
    
    print("__________________")
    print('student_profile')
    print("__________________")
    user_id = session['userid']
    # request.args['user_id']

    form = PositionForm()
    form = populate_form(form)

    q_basic_info = f"""        
        select a.user_id
            , a.student_id
            , a.employee_id        
            , a.first_name
            , a.last_name
            , a.contact_info
            , trim(trim(a.interests, '}}'), '{{') as interests
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

    q_refer_info = f"""
            select 
                i.position_title
                , co.company_name
                , case when i.require_referral=true then false else true end as received_referral
                , u.contact_info as employee_contact_info
                , u.user_id
            from student s
            inner join student_interest i on s.student_id = i.student_id
            inner join company co on co.company_id = i.company_id
            left join refer r on r.position_title=i.position_title and
                r.company_id=i.company_id and
                r.student_id=i.student_id
            left join users u on u.employee_id=r.employee_id
            where s.user_id='{user_id}'
    """

    cursor = g.conn.execute(q_refer_info)
    job_info = cursor.fetchall()

    return render_template("student_profile.html", profile_info=profile_info, job_info=job_info, form=form, user_id=user_id)


@app.route("/employee_profile", methods=['GET','POST'])
def employee_profile():

    user_id = session['userid']

    form = PositionForm()
    form = populate_form(form)

    q_basic_info = f"""        
        select a.user_id
            , a.student_id
            , a.employee_id        
            , a.first_name
            , a.last_name
            , a.contact_info
            , trim(trim(a.interests, '}}'), '{{') as interests
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

    q_refer_info = f"""
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
    cursor = g.conn.execute(q_refer_info)
    job_info = cursor.fetchall()


    q_like_info = f"""
        SELECT
            u2.first_name
            , u2.last_name
            , u2.user_id
            , u2.contact_info
            , us.skills
        FROM users u
        INNER JOIN student_like s on u.employee_id = s.employee_id
        INNER JOIN student us on us.student_id = s.student_id
        INNER JOIN users u2 on us.student_id = u2.student_id
        WHERE u.user_id='{user_id}'
        """
    cursor = g.conn.execute(q_like_info)
    like_info = cursor.fetchall()

    return render_template("employee_profile.html", profile_info = profile_info, job_info = job_info,
                            form=form, like_info=like_info, user_id=user_id)

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