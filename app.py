from flask import Flask, render_template, request,redirect, url_for,session,flash
import mysql.connector,random,smtplib,bcrypt
from email.message import EmailMessage
import os
from werkzeug.utils import secure_filename

app=Flask(__name__)
app.secret_key='your_secret_key'
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'static', 'image')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

#DATABASE CONNECTION

conn=mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="e_commerce"
  )

cursor = conn.cursor(buffered=True)

# GENERATING OTP
def send_otp(email,otp):
    sender_email="chittimujudimple@gmail.com"
    sender_pass="pgmn iwuk qfbq vvsj"
    msg = EmailMessage()

    msg['Subject'] ="Admin Registration OTP"
    msg['From']=sender_email
    msg['To'] = email

    msg.set_content(f"""
    Hello Admin,

    your OTP for Admin Registration is: {otp}

    Please do not share this OTP with anyone.

    Regards,
    Ecommerce Team
    """
    )

    with smtplib.SMTP('smtp.gmail.com',587) as server:
        server.starttls()
        server.login(sender_email,sender_pass)
        server.send_message(msg)
    print('OTP sent successfully')

# ADMIN SIGNUP
@app.route('/admin_signup',methods=['GET','POST'])
def admin_signup():
    if request.method == 'POST':
        name=request.form['name']
        email=request.form['email']
        password=request.form['password']

        cursor.execute(
            "SELECT * FROM admin WHERE email=%s",(email,)
        )
        if cursor.fetchone():
            flash("Email Already Registered")
            return redirect('/admin_signup')
        otp = random.randint(1000,9999)
        print("Generated otp:", otp)
        session['otp'] = otp
        session['name'] = name
        session['email'] = email
        session['password'] = password
        send_otp(email,otp)
        flash("OTP sent successful")
        return redirect('/verify_otp')
    return render_template('admin_signup.html')

# VERIFY OTP
@app.route('/verify_otp',methods=['GET','POST'])
def verify_otp():
    if request.method == 'POST':
        entered_otp = request.form['otp']
        if int(entered_otp) == session.get('otp'):
            name=session.get('name')
            email=session.get('email')
            password=session.get('password')

            #hashed password

            hashed_password = bcrypt.hashpw(
                password.encode('utf-8'),
                bcrypt.gensalt()
            )

            cursor.execute("""
            INSERT INTO admin (name,email,password) VALUES (%s,%s,%s)
            """,(name,email,hashed_password.decode('utf-8'))
            )
            conn.commit()
            session.pop('otp',None)
            session.pop('name',None)
            session.pop('email',None)
            session.pop('password',None)

            flash("Registration Successfull")
            return redirect('/admin_login')
        else:
            flash("Invalid OTP")
    return render_template('verify_otp.html')

# ADMIN LOGIN
@app.route('/admin_login',methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        email=request.form['email']
        password=request.form['password']

        cursor.execute(
            "select * from admin where email=%s",(email,)
        )
        admin=cursor.fetchone()
        if admin:
            stored_password = admin[3]
            if isinstance(stored_password, str):
                stored_password = stored_password.encode('utf-8')
            if bcrypt.checkpw(password.encode('utf-8'), stored_password):
                session['admin_id'] = admin[0]
                session['admin_name'] = admin[1]
                session['admin_email'] = admin[2]

                flash("Loggedd in successfully")
                return redirect('/admin_dashboard')
            else:
                flash("Invalid Password")
        else:
            flash("Mail not Registered")
    return render_template('admin_login.html')

# DASHBOARD
@app.route('/admin_dashboard')
def admin_dashboard():
    if 'admin_id' not in session :
        flash('Please login first')
        return redirect('/admin_login')
    return render_template('admin_dashboard.html',admin_name=session['admin_name'],admin_email=session['admin_email'])

#ADMIN PROFILE 
@app.route('/admin_profile',methods=['GET','POST'])
def admin_profile():
    if 'admin_id' not in session:
        flash("Please login in first")
        return redirect('/admin_login')
    admin_id = session['admin_id']
    cursor.execute(
        "SELECT * FROM admin WHERE id=%s",(admin_id,)
    )
    admin=cursor.fetchone()
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        image = request.files.get('image')
    #existing file image name
        filename = admin[4] if admin else ""
    #upload new image name
        if image and image.filename != "":
            filename = secure_filename(image.filename)
            image_save(
                os.path.join(
                app.config['UPLOAD_FOLDER'],
                filename
            )
            )
        cursor.execute(
            """
            update admin set name=%s,email=%s,image=%s where id=%s """,(name,email,image,admin_id)
        )
        conn.commit()
        session['admin_email'] = email
        session['admin_name'] = name
        flash("Admin profile updated successfully")
        return redirect('/admin_profile')
    return render_template('/admin_profile.html',admin=admin)

# LOGOUT
@app.route('/logout')
def logout():
    session.pop('admin_id',None)
    session.pop('admin_name',None)
    session.pop('admin_email',None)
    session.pop('admin_password',None)
    flash("Logged out Successfully")
    return redirect('/admin_login')

# ADD PRODUCT

@app.route('/add_item',methods=['GET','POST'])
def add_item():
    if 'admin_id' not in session:
        flash('Please login first')
        return redirect('/admin_login')
    if request.method=='POST':  
        product_name=request.form['product_name']
        description=request.form['description']
        price=request.form['price']
        image=request.files.get('image')

        filename=""

        if image and image.filename != "":
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'],filename)
            image.save(image_path)
        
        cursor.execute(
        """
INSERT INTO products(product_name,description,price,image) VALUES(%s,%s,%s,%s)""",
        (product_name,description,price,filename))
        conn.commit()
        flash("Item added successfully!")
        return redirect('/add_item')
    return render_template('add_item.html') 

#item_listing
@app.route('/item_listing',methods=['GET','POST'])
def item_listing():
    if 'admin_id' not in session:
        flash('Pls login first')
        return redirect("/admin_login")
    keyword=""
    if request.method=='POST':
        keyword=request.form['keyword']
        cursor.execute("""SELECT * FROM products WHERE product_name LIKE %s OR description LIKE %s""",('%' + keyword+'%','%' + keyword+'%'))
    else:
        cursor.execute("SELECT*FROM products")
    products = cursor.fetchall()

    return render_template('item_listing.html',products=products,keyword=keyword)

@app.route('/view_item/<int:product_id>')
def view_item(product_id):
    if 'admin_id' not in session:
        flash("PLease login first")
        return redirect("/admin_login")
    cursor.execute("SELECT * FROM products WHERE id=%s",(product_id,))
    product = cursor.fetchone()
@app.route('/update_item/<int:product_id>',methods=['GET','POST'])

def update_item(product_id):
    if 'admin_id' not in session:
        flash("Please login")
        return redirect("/admin_login")
    cursor.execute("SELECT * FROM products where id=%s",(product_id,))
    product=cursor.fetchone()

    if not product:
        flash("Product not found")
        return redirect("/item_listing")

    if request.method == 'POST':
        product_name = request.form['product_name']
        description = request.form['description']
        price = request.form['price']
        image = request.files.get('image')
        filename = product[4]
        if image and image.filename !="":
            filename=secure_filename(image.filename)
            image_path=os.path.join(
                app.config['UPLOAD_FOLDER'],
                filename
            )
            image.save(image_path)
        cursor.execute(
            """UPDATE products 
               SET product_name=%s,
               description=%s,
               price=%s,
               image=%s
               WHERE id=%s
               """,(product_name,description,price,filename,product_id))
        conn.commit()
        flash("Product Updated Successfully")
        return redirect('/item_listing')
    return render_template('update_item.html',product=product)

#DELETE ITEM
@app.route('/delete_item/<int:product_id>')
def delete_item(product_id):
     if 'admin_id' not in session:
        flash("Please login")
        return redirect("/admin_login")
     cursor.execute("DELETE FROM products WHERE id=%s",(product_id),)
     conn.commit()
     flash("Product deleted succesfully")
     return redirect('/item_listing')



if __name__ == '__main__':
    app.run(debug=True)