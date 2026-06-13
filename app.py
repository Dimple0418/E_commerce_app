from flask import Flask, render_template, request, redirect, session, flash
import mysql.connector
import random
import smtplib
import bcrypt
import os

from email.message import EmailMessage
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "your_secret_key"

# ==========================
# UPLOAD FOLDER CONFIG
# ==========================

UPLOAD_FOLDER = "static/uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ==========================
# DATABASE CONNECTION
# ==========================

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="e_commerce"
)

cursor = conn.cursor()

# ==========================
# SEND OTP FUNCTION
# ==========================

def send_otp(email, otp):

    sender_email = "chittimujudimple@gmail.com"
    sender_password = "YOUR_APP_PASSWORD"

    msg = EmailMessage()

    msg["Subject"] = "Admin Registration OTP"
    msg["From"] = sender_email
    msg["To"] = email

    msg.set_content(
        f"""
Hello Admin,

Your OTP is: {otp}

Please do not share it with anyone.

Regards,
E-Commerce Team
"""
    )

    with smtplib.SMTP("smtp.gmail.com", 587) as server:

        server.starttls()

        server.login(
            sender_email,
            sender_password
        )

        server.send_message(msg)

# ==========================
# ADMIN SIGNUP
# ==========================

@app.route("/admin_signup", methods=["GET", "POST"])
def admin_signup():

    if request.method == "POST":

        name = request.form["name"]

        email = request.form["email"]

        password = request.form["password"]

        cursor.execute(
            "SELECT * FROM admin WHERE email=%s",
            (email,)
        )

        existing_admin = cursor.fetchone()

        if existing_admin:

            flash("Email already registered")

            return redirect("/admin_signup")

        otp = str(random.randint(1000, 9999))

        session["otp"] = otp
        session["name"] = name
        session["email"] = email
        session["password"] = password

        send_otp(email, otp)

        flash("OTP Sent Successfully")

        return redirect("/verify_otp")

    return render_template("admin_signup.html")

# ==========================
# OTP VERIFICATION
# ==========================

@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():

    if request.method == "POST":

        entered_otp = request.form["otp"]

        if entered_otp == session.get("otp"):

            name = session.get("name")

            email = session.get("email")

            password = session.get("password")

            hashed_password = bcrypt.hashpw(
                password.encode("utf-8"),
                bcrypt.gensalt()
            )

            cursor.execute(
                """
                INSERT INTO admin
                (
                    name,
                    email,
                    password
                )
                VALUES
                (
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    name,
                    email,
                    hashed_password.decode("utf-8")
                )
            )

            conn.commit()

            session.pop("otp", None)
            session.pop("name", None)
            session.pop("email", None)
            session.pop("password", None)

            flash("Registration Successful")

            return redirect("/admin_login")

        else:

            flash("Invalid OTP")

    return render_template("verify_otp.html")

# ==========================
# ADMIN LOGIN
# ==========================

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        email = request.form["email"]

        password = request.form["password"]

        cursor.execute(
            "SELECT * FROM admin WHERE email=%s",
            (email,)
        )

        admin = cursor.fetchone()

        if admin:

            stored_password = admin[3]

            if bcrypt.checkpw(
                password.encode("utf-8"),
                stored_password.encode("utf-8")
            ):

                session["admin_id"] = admin[0]

                session["admin_name"] = admin[1]

                session["admin_email"] = admin[2]

                flash("Login Successful")

                return redirect("/admin_dashboard")

            else:

                flash("Invalid Password")

        else:

            flash("Email Not Registered")

    return render_template("admin_login.html")

# ==========================
# ADMIN DASHBOARD
# ==========================

@app.route("/admin_dashboard")
def admin_dashboard():

    if "admin_id" not in session:

        flash("Please Login First")

        return redirect("/admin_login")

    return render_template(
        "admin_dashboard.html",
        admin_name=session["admin_name"],
        admin_email=session["admin_email"]
    )

# ==========================
# LOGOUT
# ==========================

@app.route("/admin_logout")
def admin_logout():

    session.clear()

    flash("Logged Out Successfully")

    return redirect("/admin_login")

# ==========================
# ADD PRODUCT
# ==========================

@app.route("/add_item", methods=["GET", "POST"])
def add_item():

    if "admin_id" not in session:

        flash("Please Login First")

        return redirect("/admin_login")

    if request.method == "POST":

        product_name = request.form["product_name"]

        description = request.form["description"]

        price = request.form["price"]

        image = request.files["image"]

        filename = ""

        if image and image.filename != "":

            filename = secure_filename(
                image.filename
            )

            image_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                filename
            )

            image.save(image_path)

        cursor.execute(
            """
            INSERT INTO products
            (
                product_name,
                description,
                price,
                image
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                product_name,
                description,
                price,
                filename
            )
        )

        conn.commit()

        flash("Product Added Successfully")

        return redirect("/add_item")

    return render_template("add_item.html")

# ==========================
# RUN APPLICATION
# ==========================

if __name__ == "__main__":

    app.run(debug=True)


























# from flask import Flask, render_template, request,redirect, url_for,session,flash
# import mysql.connector,random,smtplib,bcrypt
# from email.message import EmailMessage
# import os
# from werkzeug.utils import secure_filename

# app=Flask(__name__)
# app.secret_key='your_secret_key'

# #DATABASE CONNECTION

# conn=mysql.connector.connect(
#     host="localhost",
#     user="root",
#     password="root",
#     database="e_commerce"
#   )

# cursor = conn.cursor()

# # GENERATING OTP
# def send_otp(email,otp):
#     sender_email="chittimujudimple@gmail.com"
#     sender_pass="wmud zagz ywnf hpfm"
#     msg = EmailMessage()

#     msg['Subject'] ="Admin Registration OTP"
#     msg['From']=sender_email
#     msg['To'] = email

#     msg.set_content(f"""
#     Hello Admin,

#     your OTP for Admin Registration is: {otp}

#     Please do not share this OTP with anyone.

#     Regards,
#     Ecommerce Team
#     """
#     )

#     with smtplib.SMTP('smtp.gmail.com',587) as server:
#         server.starttls()
#         server.login(sender_email,sender_pass)
#         server.send_message(msg)
#     print('OTP sent successfully')

# # ADMIN SIGNUP
# @app.route('/admin_signup',methods=['GET','POST'])
# def admin_signup():
#     if request.method == 'POST':
#         name=request.form['name']
#         email=request.form['email']
#         password=request.form['password']

#         cursor.execute(
#             "SELECT * FROM admin WHERE email=%s",(email,)
#         )
#         if cursor.fetchone():
#             flash("Email Already Registered")
#             return redirect('/admin_signup')
#         otp = random.randint(1000,9999)
#         print("Generated otp:", otp)
#         session['otp'] = otp
#         session['name'] = name
#         session['email'] = email
#         session['password'] = password

#         send_otp(email,otp)
#         flash("OTP sent successful")
#         return redirect('/verify_otp')
#     return render_template('admin_signup.html')

# # VERIFY OTP
# @app.route('/verify_otp',methods=['GET','POST'])
# def verify_otp():
#     if request.method == 'POST':
#         entered_otp = request.form['otp']
#         if int(entered_otp) == session.get('otp'):
#             name=session.get('name')
#             email=session.get('email')
#             password=session.get('password')

#             #hashed password

#             hashed_password = bcrypt.hashpw(
#                 password.encode('utf-8'),
#                 bcrypt.gensalt()
#             )

#             cursor.execute("""
#             INSERT INTO admin (name,email,password) VALUES (%s,%s,%s)
#             """,(name,email,hashed_password.decode('utf-8'))
#             )
#             conn.commit()

#             session.pop('otp',None)
#             session.pop('name',None)
#             session.pop('email',None)
#             session.pop('password',None)

#             flash("Registration Successfull")
#             return redirect('/admin_login')
#         else:
#             flash("Invalid OTP")
#     return render_template('verify_otp.html')

# # ADMIN LOGIN
# @app.route('/admin_login',methods=['GET','POST'])
# def admin_login():
#     if request.method == 'POST':
#         email=request.form['email']
#         password=request.form['password']

#         cursor.execute(
#             "select * from admin where email=%s",(email,)
#         )
#         admin=cursor.fetchone()
#         if admin:
#             stored_password = admin[3]
#         if bcrypt.checkpw(password.encode('utf-8'),stored_password.encode('utf-8')):
#             session['admin_id'] = admin[0]
#             session['admin_name'] = admin[1]
#             session['admin_email']=admin[2]

#             flash("Loggedd in successfully")
#             return redirect('/admin_dashboard')
#         else:
#             flash("Invalid Password")
#     else:
#         flash("Mail not Registered")
#     return render_template('admin_login.html')

# # DASHBOARD
# @app.route('/admin_dashboard')
# def admin_dashboard():
#     if 'admin_id' not in session :
#         flash('Please login first')
#         return redirect('/admin_login')
    
#     return render_template(
#         'admin_dashboard.html',
#         admin_name=session['admin_name'],
#         admin_email=session['admin_email']
#     ) 

# # LOGOUT
# @app.route('/admin_logout')
# def admin_logout():
#     session.pop('admin_id',None)
#     session.pop('admin_name',None)
#     session.pop('admin_email',None)

#     flash("Logged out")
#     return redirect('/admin_login')

# #add item
# @app.route('/add_item',methods=['GET','POST'])
# def add_item():
#     if 'admin_id' not in session:
#         flash('Please login first')
#         return redirect('/admin_login')
    
#     if request.method=='POST':

#         product_name=request.form['product_name']
#         description=request.form['description']
#         price=request.form['price']
#         image=request.files.get('image')

#         filename=""
#         if image and image.filename!="":
#             filename=secure_filename(image.filename)

#             image_path=os.path.join(
#                 app.config['UPLOAD_FOLDER'],
#                 filename
#             )

#             image.save(image_path)

#         cursor.execute (
#             """INSERT INTO products (product_name,description,price,image) VALUES (%s,%s,%s,%s) """,(product_name,description,price,filename)
#         )
#         conn.commit()
#         # cursor.close()
#         # conn.close()
#         flash("product added successfully!")
#         return redirect('/add_item')
#     return render_template('add_item.html')


# if __name__ == '__main__':
#     app.run(debug=True)




