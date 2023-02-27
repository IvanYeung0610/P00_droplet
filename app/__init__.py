# <div ID="success"></div>: Daniel Yentin, Ivan Yeung
# SoftDev
# Nov 2022

import sqlite3

DB_FILE = "database.db"
db = sqlite3.connect(DB_FILE)
c = db.cursor()


from flask import *
# from flask import Flask             #facilitate flask webserving
# from flask import render_template   #facilitate jinja templating
# from flask import request           #facilitate form submission
# from flask import session           #facilitate form submission
# from flask import p_redirect           #facilitate form submission
# from flask import url_for

#the conventional way:
#from flask import Flask, render_template, request

app = Flask(__name__)    #create Flask object
app.secret_key = b"\xdcG4g\xebL\x98m\xacX\x03\x13\xef\xfeF0#\x07P\x07JN\xf1P|'\x9ak\x1f\xe2\xf2?"
NOTHING = ("", 204)


db = sqlite3.connect(DB_FILE, check_same_thread=False)
c = db.cursor()


def p_redirect(url: str):
    '''
    flask redirect using post (307)
    '''
    return redirect(url, 307)

#finds uid based on username passed in
def find_uid(username):
    '''
    returns uid of username
    '''
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    uid = c.fetchall()[0][0]
    return uid

#finds sid based on title passed in
def find_sid(title):
    c.execute("SELECT * FROM stories WHERE title = ?", (title,))
    sid = c.fetchall()[0][0]
    return sid

@app.route("/", methods=['GET', 'POST'])
def root():
    session.pop("error", "")
    print("\n\n\n"),
    print("***DIAG: this Flask obj ***")
    print(app)

    #checks if cookie has username and password stored
    if ('stay_logged_in' in session):
        if (session['stay_logged_in'] == True):
            c.execute("SELECT * FROM users WHERE username = ?", (session["username"],))
            users = c.fetchall()
            if (len(users) != 0):
                print("***DIAG: user has already logged and checked the button to stay logged in***")
                return p_redirect("/home")

    #returns login page if cookie does not have that information
    return p_redirect("/login")

@app.route("/login", methods=['GET', 'POST'])
def login():
    #Prevents errors from carrying over from register page
    if (session.get("error", "")) == "Username is not available":
        session.pop("error", "")
    return render_template('login.html', error=session.get("error", ""))

@app.route("/login/auth", methods=['GET', 'POST'])
def login_auth():
    session.pop("error", "")
    form_username = request.form["username"]
    form_password = request.form["password"]
    stay_logged_in = "stay_logged_in" in request.form #checks if box has been ticked or not
    print(f"stay_logged_in: {stay_logged_in}")

    print(form_username)
    c.execute("SELECT * FROM users WHERE username = ?", (form_username,))
    users = c.fetchall()

    if len(users) == 1:
        user = users[0]
        db_username = user[1]
        db_password = user[2]

        print("***DIAG: username matches ***")
        #checks if input for the password form matches with hardcoded password
        if (form_password == db_password):
            print("***DIAG: password matches ***")
            #when both coditions are met, password is stored in the cookie and the home page is
            session["username"] = form_username
            session["stay_logged_in"] = stay_logged_in
            session.pop("error", "")
            return p_redirect("/home")

        session["error"] = "Incorrect Password"
        print("***DIAG: Password did not match ***")
        return p_redirect("/login")


    session["error"] = "Username does not exist"
    print("***DIAG: account does not exist ***")
    return p_redirect("/login")


@app.route("/register", methods=['GET', 'POST'])
def register():
    #Prevents errors from carrying over from login page
    if (session.get("error", "")) == "Incorrect Password" or (session.get("error", "")) == "Username does not exist" :
        session.pop("error", "")
    return render_template('register.html', error=session.get("error", ""))

@app.route("/register/auth", methods=['GET', 'POST'])
def register_auth():
    session.pop("error", "")
    c.execute("SELECT * FROM users")
    next_available_uid = len(c.fetchall())
    print(next_available_uid)

    username = request.form["username"]
    password = request.form["password"]

    #checks if inputted username exists
    c.execute(f"SELECT username FROM users WHERE username = ?", (username,))
    usernames = c.fetchall()

    if len(usernames) == 0:
        print("***DIAG: username was available***")
        session.pop("error", "")
        c.execute("INSERT INTO users(uid, username, password) VALUES(?, ?, ?)", (next_available_uid, username, password))
        c.execute(f"CREATE TABLE uid_{next_available_uid}(title TEXT)")
        db.commit()
        return p_redirect("/login")

    session["error"] = "Username is not available"
    return p_redirect("/register")

@app.route("/logout", methods=['GET', 'POST'])
# this function is called by the logout button when it is pressed on the home page
def logout():
    #cookie holding username is removed
    if (session["stay_logged_in"] == False):
        session.pop("stay_logged_in")
        session.pop("username")
        print("***DIAG: username and password removed from cookie ***")
    session.pop("error", "")
    return p_redirect("/login")

@app.route("/home", methods=['GET', 'POST'])
def home():
    # view
    uid = find_uid(session["username"])
    c.execute(f"SELECT title FROM uid_{uid}")
    view = c.fetchall()

    for i in range(len(view)):
        title = view[i][0]
        view[i] = title

    # add
    c.execute(f"SELECT title FROM stories")
    add = c.fetchall()

    for i in range(len(add)):
        title = add[i][0]
        add[i] = title

    #filters out stories that user has contributed to from all the stories
    add = list(filter(lambda i: i not in view, add))

    return render_template('home.html', add=add, view=view, error=session.get("error", ""))

@app.route("/create", methods=['GET', 'POST'])
def create():
    return render_template('create.html', error=session.get("error", ""), title=session.get("title", ""), body=session.get("body", ""))

@app.route("/publish", methods=['GET', 'POST'])
def publish():
    session.pop("error", "")
    session.pop("title", "")
    session.pop("body", "")
    c.execute("SELECT * FROM stories")
    next_available_sid = len(c.fetchall())
    print(f"next_available_sid: {next_available_sid}") #sid = story id

    title = request.form["title"]

    c.execute("SELECT title FROM stories WHERE title = ?", (title,))
    titles = c.fetchall()
    if (len(titles) == 0):
        print("***DIAG: title was available***")

        body = request.form["body"]
        if (len(body) == 0):
            print("***DIAG: body cannot be empty***")
        if (len(body) > 200):
            print("***DIAG: body cannot be greater than 200 characters***")

        publisher = session["username"]

        # store story in stories table'
        c.execute(f"INSERT INTO stories(sid, title, body, publisher) VALUES(?, ?, ?, ?)", (next_available_sid, title, body, publisher))
        print("***DIAG: story inserted into database***")

        # store story history in story table
        c.execute(f"CREATE TABLE sid_{next_available_sid}(contributor TEXT, contribution TEXT)")
        c.execute(f"INSERT INTO sid_{next_available_sid}(contributor, contribution) VALUES(?, ?)", (publisher, body))
        print("***DIAG: story's history inserted into database***")

        uid = find_uid(session["username"])
        print(uid)
        c.execute(f"INSERT INTO uid_{uid}(title) VALUES(?)", (title,))

        db.commit()
        return p_redirect("/home")

    print("***DIAG: title was not available***")
    session["error"] = "Title has already been taken"
    session["title"] = request.form["title"]
    session["body"] = request.form["body"]
    return p_redirect("/create")
    # display error syaing title is not unique


@app.route("/add", methods=['GET', 'POST'])
def add():
    session.pop("error", "")
    title = request.form["title"] #passed in from the hidden form

    c.execute("SELECT * FROM stories WHERE title = ?", (title,))
    info = c.fetchall()[0]
    print(f"info: {info}")
    title = info[1]
    print(f"title: {title}")
    sid = find_sid(title)
    c.execute(f"SELECT contribution FROM sid_{sid}")
    latest_contribution = c.fetchall()[-1][0]

    print("publisher: {publisher}")
    publisher = info[3]
    return render_template('add.html', title=title, latest_contribution=latest_contribution, publisher=publisher, error=session.get("error", ""))

@app.route("/save", methods=['GET', 'POST'])
def save():
    session.pop("error", "")
    contributor = session["username"]
    title = request.form["title"]
    contribution = request.form["contribution"]
    if (len(contribution) == 0):
        print("***DIAG: body cannot be empty***")
    if (len(contribution) > 200):
        print("***DIAG: body cannot be greater than 200 characters***")

    uid = find_uid(session["username"])
    c.execute(f"INSERT INTO uid_{uid}(title) VALUES(?)", (title,))
    print(f"title {title}")
    sid = find_sid(title)
    c.execute(f"INSERT INTO sid_{sid}(contributor, contribution) VALUES(?, ?)", (contributor, contribution))

    c.execute("SELECT body FROM stories WHERE title = ?", (title,))
    body = c.fetchall()[0][0]
    c.execute("UPDATE stories SET body = ? WHERE title = ?", (body+" "+contribution, title))

    db.commit()
    return p_redirect("/home")


@app.route("/view", methods=['GET', 'POST'])
def view():
    title = request.form["title"] #passed in from the hidden form
    c.execute("SELECT * FROM stories WHERE title = ?", (title,))
    info = c.fetchall()[0]
    print(info)

    title = info[1]
    body = info[2]
    publisher = info[3]
    return render_template('view.html', title=title, body=body, publisher=publisher, error=session.get("error", ""))

if __name__ == "__main__": #false if this file imported as module
    #enable debugging, auto-restarting of server when this file is modified
    # session.pop("username", None)
    #table storing usernames and passwords
    c.execute("CREATE TABLE IF NOT EXISTS users(uid INT, username TEXT, password TEXT)")
    #table storing info on stories
    c.execute("CREATE TABLE IF NOT EXISTS stories(sid INT, title TEXT, body TEXT, publisher TEXT)")

    db.commit()

    app.debug = True
    app.run()

    db.close()
