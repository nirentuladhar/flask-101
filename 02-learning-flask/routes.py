from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from flask_mysqldb import MySQL


app = Flask(__name__)

# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'journalapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#init MySQL
mysql = MySQL(app)


@app.route("/")
def index():
    return render_template("index.html")


class SignUpForm(Form):
    first_name = StringField("First Name", [validators.Length(min=1, max=50)])
    last_name = StringField("Last Name", [validators.Length(min=1, max=50)])
    email = StringField("Email", [validators.Length(min=6, max=50)])
    password = PasswordField("Password", [
        validators.DataRequired(),
        validators.EqualTo("confirm", message="Passwords do not match.")
    ])
    confirm = PasswordField("Confirm Password")


@app.route("/sign-up", methods=["GET", "POST"])
def signup():
    form = SignUpForm(request.form)
    if request.method == "POST" and form.validate():
        first_name = form.first_name.data
        last_name = form.last_name.data
        email = form.email.data
        password = sha256_crypt.encrypt(str(form.password.data))

        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users(first_name, last_name, email, password) VALUES (%s, %s, %s, %s)", (first_name, last_name, email, password))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for("index"))
    return render_template("sign-up.html", form=form)


    


@app.route("/sign-in", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        email = request.form["email"]
        password_candidate = request.form["password"]

        cur = mysql.connection.cursor()
        result = cur.execute("SELECT * FROM users WHERE email = %s", [email])
        if result > 0:
            data = cur.fetchone()
            password = data["password"]
            if sha256_crypt.verify(password_candidate, password):
                session["logged_in"] = True
                session["first_name"] = data["first_name"]
                session["user_id"] = data["id"]
                return redirect(url_for("index"))
        else:
            # username not found
            error = "Username not found"
            return render_template("sign-in.html", error=error)
    return render_template("sign-in.html")



@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))




@app.route("/journals")
def journals():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM journals WHERE user_id = %s", str(session["user_id"]))
    journals = cur.fetchall()
    cur.close()
    return render_template("journals.html", journals=journals)


# 1-JOURNAL       ->  2-JOURNAL-ENTRIES 
# 1-JOURNAL-ENTRY ->  2-VERSIONS

# query all journal-entries

# loop all journal-entries
#     query latest version 
#     store latest version
#     send latest version

@app.route("/journals/<string:id>", methods=["GET", "POST"])
def journal_entries(id):
    versions, hidden, deleted = [], [], []

    cur = mysql.connection.cursor()
    result = cur.execute("select * from journal_entries where journal_id = %s", id)
    journal_entries = cur.fetchall()
    cur.close()

    for journal_entry in journal_entries:
        cur = mysql.connection.cursor()
        if journal_entry["hidden"] == 0 and journal_entry["deleted"] == 0:
            # app.logger.info(journal_entry)
            query = "SELECT * FROM versions WHERE journal_entry_id = {}".format(int(journal_entry["id"]))
            result = cur.execute(query)
            ver = cur.fetchone()
            cur.close()
            versions.append(ver)
        elif journal_entry["hidden"] == 1 and journal_entry["deleted"] == 0: 
            query = "SELECT * FROM versions WHERE journal_entry_id = {}".format(int(journal_entry["id"]))
            result = cur.execute(query)
            ver = cur.fetchone()
            cur.close()
            hidden.append(ver)
        else:
            query = "SELECT * FROM versions WHERE journal_entry_id = {}".format(int(journal_entry["id"]))
            result = cur.execute(query)
            ver = cur.fetchone()
            cur.close()
            deleted.append(ver)
        # app.logger.info(ver)
        
    return render_template("journal_entries.html", versions=versions, hidden=hidden, deleted=deleted)







class AddJournalForm(Form):
    title = StringField("Title", [validators.Length(min=1, max=50)])

@app.route("/add-journal", methods=["GET", "POST"])
def addjournal():
    form = AddJournalForm(request.form)

    if request.method == "POST" and form.validate():
        title = form.title.data
        
        
        cur = mysql.connection.cursor()
        query = "INSERT INTO journals(user_id, name) VALUES ({},'{}');".format(session["user_id"], title)
        app.logger.info(query)
        cur.execute(query)
        mysql.connection.commit()
        cur.close()
        return redirect(url_for("journals"))

    return render_template("add-journal.html", form=form)




if __name__=="__main__":
    app.secret_key="secret123"
    app.run(debug=True)


