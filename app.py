from flask import Flask, render_template, request,redirect, url_for,session,flash
import mysql.connector,random,smtplib,bcrypt
from email.message import EmailMessage
import os
from werkzeug.utils import secure_filename
import razorpay
import hmac
import hashlib
from flask import jsonify


app=Flask(__name__)
app.secret_key='your_secret_key'

RAZORPAY_KEY_ID="rzp_test_T3qg30s00oLBEF"
RAZORPAY_KEY_SECRET="RRYtBBUKT1swg4mcfS0YJvFa"

client=razorpay.Client(auth =(RAZORPAY_KEY_ID,RAZORPAY_KEY_SECRET))

app.config['UPLOAD_FOLDER'] = os.path.join(
    os.getcwd(),
    'static',
    'images'
)
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
            image.save(
                os.path.join(
                app.config['UPLOAD_FOLDER'],
                filename
            )
            )
        cursor.execute(
        """
        UPDATE admin
        SET name=%s,email=%s,image=%s
        WHERE id=%s
        """,
        (name,email,filename,admin_id)
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

#------------view item----------------#
@app.route('/view_item/<int:product_id>')
def view_item(product_id):

    if 'admin_id' not in session:
        flash("Please Login")
        return redirect('/admin_login')

    cursor.execute(
        "SELECT * FROM products WHERE id=%s",
        (product_id,)
    )

    product = cursor.fetchone()

    if not product:
        flash("Product Not Found")
        return redirect('/item_listing')

    return render_template(
        'view_item.html',
        product=product
    )

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
     
     cursor.execute(
     "DELETE FROM products WHERE id=%s",
     (product_id,)
     )
     
     conn.commit()
     flash("Product deleted succesfully")
     return redirect('/item_listing')


#USER SIGNUP
@app.route('/user_signup',methods=['GET','POST'])
def user_signup():
    if request.method == 'POST':
        name=request.form['name']
        email=request.form['email']
        password=request.form['password']

        cursor.execute(
            "SELECT * FROM users WHERE email=%s",(email,)
        )
        if cursor.fetchone():
            flash("Email Already Registered")
            return redirect('/user_signup')
        hashed_password = bcrypt.hashpw(password.encode('utf-8'),bcrypt.gensalt())
        cursor.execute(
            """ 
            INSERT INTO users (name,email,password) 
            VALUES (%s,%s,%s)
            """,
            (
                name,
                email,
                hashed_password.decode('utf-8'))
        )
        conn.commit()
        flash("signup successful")
        return redirect('/user_login')
    return render_template('user_signup.html')

#USER LOGIN
@app.route('/user_login',methods=['GET','POST'])
def user_login():
    if request.method == 'POST':
        email=request.form['email']
        password=request.form['password']

        cursor.execute(
            "select * from users where email=%s",(email,)
        )
        user=cursor.fetchone()
        if user:
            stored_password = user[3]
            if bcrypt.checkpw(password.encode('utf-8'),stored_password.encode('utf-8')):

                session['user_id'] = user[0]
                session['user_name'] = user[1]
                session['user_email'] = user[2]
                flash("Loggedd in successfully")
                return redirect('/user_dashboard')
            else:
                flash("Invalid Password")
        else:
            flash("Mail not Registered")
    return render_template('user_login.html')

#USER SIGNOUT
@app.route('/user_logout')
def user_logout():
    session.pop('user_id',None)
    session.pop('user_name',None)
    session.pop('user_email',None)
    
    flash("Logged out successfully")

    return redirect('/user_login')

#-------------USER DASHBOARD----#

@app.route('/user_dashboard')
def user_dashboard():

    if 'user_id' not in session:
        flash("Please Login First")
        return redirect('/user_login')

    cursor.execute(
        "SELECT * FROM products"
    )

    products = cursor.fetchall()

    return render_template(
        'user_dashboard.html',
        products=products
    )

# @app.route('/user_dashboard')
# def user_dashboard():
#     cursor.execute("SELECT * FROM products")
#     products=cursor.fetchall()
#     return render_template('user_dashboard.html',products=products)

#----------------checkout-----------------#
@app.route('/checkout')
def checkout():
    if 'user_id' not in session:
        return redirect ('/user_login')
    
    cart=session.get('cart',[])
    total=sum(item['price'] for item in cart)

    order=client.order.create({
        "amount":int(total*100),
        "currency":"INR",
        "payment_capture":1
    })
    session ['razorpay_order_id']=order['id']

    return render_template(
        'checkout.html',
        amount=total,
        order_id=order['id'],
        key_id=RAZORPAY_KEY_ID
    )

#------------verify payment----------#
@app.route('/verify_payment',methods=['POST'])
def verify_payment():
    data=request.get_json()

    razorpay_order_id=data['razorpay_order_id']
    razorpay_payment_id=data['razorpay_payment_id']
    razorpay_signature=data['razorpay_signature']

    generated_signature=hmac.new(
        bytes(RAZORPAY_KEY_SECRET,'utf-8'),

        bytes(
            razorpay_order_id +
            "|" + 
            razorpay_payment_id,
            'utf-8'
        ),
        hashlib.sha256

    ).hexdigest()

    if generated_signature==razorpay_signature:

        total=sum (
            item['price']
            for item in session.get('cart',[])
        )
        cursor.execute(
            """INSERT INTO payments 
            ( 
                user_id,
                order_id,
                payment_id,
                amount,status
            )
            VALUES
            (%s,%s,%s,%s,%s)
            """,(
                session['user_id'],
                razorpay_order_id,
                razorpay_payment_id,
                total,"Success"
            )
        )

        conn.commit()

        session['cart']=[]

        return jsonify({
            "status":"success"
        })
    
    return jsonify({
        "status":"failed"
    })

#----------------payment success-----------#

@app.route('/payment_success')
def payment_success():

    return render_template('payment_success.html')


#------------------REMOVE FROM CART----------------#
@app.route('/remove_from_cart/<int:product_id>')
def remove_cart(product_id):

    cart = session.get('cart', [])

    cart = [
        item for item in cart
        if item['id'] != product_id
    ]
    session['cart'] = cart

    flash("Item Removed from cart ")

    return redirect('/view_cart')




#user search
@app.route('/user_search',methods=['GET','POST'])
def user_search():
    if request.method == 'POST':
        keyword=request.form['keyword']
        cursor.execute(
            """
            select * from products where product_name LIKE %s OR description LIKE %s""",("%" + keyword + "%","%" + keyword + "%")
        )
        products = cursor.fetchall()
    else:
        cursor.execute("SELECT * from products")
        products = cursor.fetchall()
    return render_template('search_results.html',products=products)

# add to cart
@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    cursor.execute(
        "SELECT * FROM products WHERE id=%s",
        (product_id,)
    )
    product = cursor.fetchone()
    if product:
        cart = session.get('cart',[])

        cart.append({
            'id':product[0],
            'name':product[1],
            'price':float(product[3]),
            'image':product[4]
        })

        session['cart']=cart

        flash("product added to cart successfully")

        return redirect('/user_dashboard')
    # return render_template('view_cart.html',product = product)


@app.route('/view_cart')
def view_cart():
    if 'user_id' not in session:
        flash("Please login first")
        return redirect('/user_login')
    cart=session.get('cart',[])

    total=sum(item['price'] for item in cart)

    return render_template(
        'view_cart.html',cart=cart,total=total
    )



if __name__ == '__main__':
    app.run(debug=True)


