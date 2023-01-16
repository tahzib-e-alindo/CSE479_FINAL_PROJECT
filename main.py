from flask import Flask, request, render_template, redirect, session
from copy import deepcopy
from bson.objectid import ObjectId
import pymongo
import json
import ast
import itertools

app = Flask(__name__)
app.secret_key = 'super secret key'

db_client = pymongo.MongoClient("mongodb://localhost:27017")
db = db_client["479project"]
user_table = db["users"]
admin_table = db["product_upload"]
cart_table = db["user_cart"]


@app.route("/register", methods=['GET', 'POST'])
def register():
    if "logged_in" in session:
        return redirect("/")
    else:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            cpassword = request.form['confirm_password']
            mail = request.form['mail']
            phone = request.form['phone']
            message = None
            if password != cpassword:
                message = "Password didn't match"
            elif len(password) < 8:
                message = "Password too short"
            elif len(phone) < 11:
                message = "invalid phone"
            elif phone[0]!="0" or phone[1]!="1":
                message = "invalid phone"
            else:
                match = user_table.find_one({"username": username})
                match_mail = user_table.find_one({"mail": mail})
                match_phone = user_table.find_one({"phone": phone})
                if match is not None:
                    message = "User already exists."
                elif match_mail is not None:
                    message = "Mail Already In Use"
                elif match_phone is not None:
                    message = "Phone is use"
                else:
                    user_table.insert_one(dict(request.form))
                    message = "success"
            return message

    return render_template("register.html", **locals())


@app.route("/login", methods=["GET", "POST"])
def login():
    if "logged_in" in session:
        return redirect("/")
    else:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            message = None
            match = user_table.find_one({"username": username})
            if match is None:
                message = "User does not exist"
            elif password != match["password"]:
                message = "Wrong Password"
            elif match is not None:
                message = "success"
                session["logged_in"] = True
                session["username"] = username
            return message
        return render_template("login.html", **locals())


@app.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    return redirect("/login")


@app.route('/account', methods=['GET', "POST"])
def account():
    user = user_table.find_one({"username": session["username"]})
    if request.method == "POST":
        if request.form.get('firstname') is not None:
            form_data = request.form
            firstname = form_data["firstname"]
            lastname = form_data["lastname"]
            city = form_data["city"]
            address = form_data["address"]
            mail = form_data["mail"]
            phone = form_data["phone"]
            user_table.update_one({"username": session["username"]}, {"$set": {
                                "firstname": firstname, "lastname": lastname, "city": city, "address": address, "mail": mail, "phone": phone}})
        else:
            form_data = request.form
            message = None
            old_password = form_data["old_password"]
            new_password = form_data["new_password"]
            confirm_password = form_data["confirm_password"]
            if old_password != user["password"]:
                message = "Old Password Didn't Match"
            elif new_password != confirm_password:
                message = "Wrong Password"
            else:
                message = "success"
                user_table.update_one({"username": session["username"]}, {"$set": {
                                "password": new_password, "confirm_password": confirm_password}})
            return message
            
    return render_template("account.html", **locals())

@app.route('/cart', methods=['GET', "POST"])
def cart():
    user = user_table.find_one({"username": session["username"]})
    l1 = list()
    item = list()
    items = list()
    price = list()
    total_price = 0
    for i in cart_table.find({"username": session["username"]}):
        l1.append(i)
    print(l1)
    for i in l1:
        x = i['item']
        n = ObjectId(x)
        m = admin_table.find_one({"_id": n})
        items.append(m)
    for i in items:
        t = i['price'].replace(",", "")
        t = t[:len(t) - 1]
        t = int(t)
        total_price = total_price + t
    return render_template("cart.html", **locals())

@app.route("/product/<string:n>", methods=['GET', "POST"])
def products(n):
    loggedin = "logged_in" in session
    l = []
    brand_list = []
    product_list = []
    brand_filter = []
    for pd in admin_table.find({"category": n}):
        l.append(pd)
        if pd["brand"] not in brand_list:
            brand_list.append(pd["brand"])
    x = len(l)
    ispost = False
    if request.method == "POST":
        ispost = True
        form_data = request.form
        if request.form.get('price_from'):
            price_from = form_data['price_from']
            price_to = form_data['price_to']
            for pd in l:
                t = pd['price'].replace(",", "")
                t = t[:len(t) - 1]
                t = int(t)
                if t < int(price_to) and t > int(price_from):
                    product_list.append(pd)

            print(product_list)
        for i in brand_list:
            if request.form.get(i):
                for pd in product_list:
                    if pd['brand'] == i:
                        brand_filter.append(pd)
        product_list = brand_filter
        print(product_list)
        x = len(product_list)
        return render_template("product_filter.html", **locals())
    if "logged_in" in session:
        user = user_table.find_one({"username": session["username"]})
        return render_template("product.html", **locals())
    else:
        return render_template("product.html", **locals())

@app.route("/product-details/<string:n>", methods=['GET', "POST"])
def product_details(n):
    n = ObjectId(n)
    i = admin_table.find_one({"_id": n})
    loggedin = "logged_in" in session
    print(i)
    nonspec = ['_id','productname','category','price','brand','img','description']
    speclist = {}
    for k in i:
        if k not in nonspec:
            speclist[k] = i[k]
    key_features = dict(itertools.islice(speclist.items(), 4))
    print(key_features)
    if "logged_in" in session: 
        user = user_table.find_one({"username": session["username"]})
        if request.method == "POST":
            message = None
            username = user["username"]
            item = request.form['item']
            match = cart_table.find_one({"item": item, "username": username})
            if match is not None:
                message = "Item Already In Cart"
            else:
                message = "Item Added To Cart"
                dic = {"username": username,
                        "item": item}
                cart_table.insert_one(dic)
            return message
        return render_template("singleproduct.html", **locals())
    else:
        return render_template("singleproduct.html", **locals())

@app.route("/admin", methods=['GET', "POST"])
def admin():
    category_list = admin_table.distinct('category')
    if request.method == "POST":
        form_data = request.form
        product_info = {}
        product_info["productname"] = form_data["productname"]
        product_info["category"] = form_data["category"]
        product_info["brand"] = form_data["brand"]
        product_info["price"] = form_data["price"]
        product_info["description"] = form_data["description"]
        product_info["img"] = form_data["img"]
        print(form_data)
        for i in form_data:
            if "key" in i:
                print(i[3:])
                print(type(i[3:]))
                print(f'{form_data[i]} = {form_data["value" + i[3:]]}')
                product_info[form_data[i]] = form_data["value" + i[3:]]
        admin_table.insert_one(product_info)
        return render_template("admin.html", **locals())
    return render_template("admin.html", **locals())

@app.route("/searched", methods=['GET', "POST"])
def searched():
    if request.method == "POST":
        form_data = request.form
        print(form_data)
        searchlist = []
        for i in admin_table.find():
            if request.form.get('search') in i["productname"]:
                searchlist.append(i)
            print(searchlist)
    return render_template("searched.html", **locals())

@app.route("/search", methods=['GET', "POST"])
def search():
    loggedin = "logged_in" in session
    search_list = []
    if request.method == "POST":
        if request.form.get('search_bar') is not None:
            searches = request.form.get('search_bar')
            search_list = searches.split(" ")

            for i in range(len(search_list)):
                search_list.append(search_list[i].lower())
            print(search_list)
            search_list = search_list[1:]
            found_items = []
            product_list = []
            for k in search_list:
                for i in admin_table.find():
                    t = i["productname"].lower()
                    if k in t:
                        if i not in found_items:
                            found_items.append(i)
    if "logged_in" in session:
        user = user_table.find_one({"username": session["username"]})
        return render_template("search_products.html", **locals())
    else:
        return render_template("search_products.html", **locals())

@app.route("/edit/<string:n>", methods=['GET', 'POST'])
def edit(n):
    n = ObjectId(n)
    i = admin_table.find_one({"_id": n})
    print(i)
    ispost = False
    if request.method == "POST":
        ispost = True
        form_data = request.form
        product_info = {}
        product_info["productname"] = form_data["productname"]
        product_info["category"] = form_data["category"]
        product_info["brand"] = form_data["brand"]
        product_info["price"] = form_data["price"]
        product_info["description"] = form_data["description"]
        if form_data["img"] != "":
            product_info["img"] = form_data["img"]
        print(product_info)
        admin_table.update_one({"_id": n}, {"$set": product_info})
        #admin_table.insert_one(product_info)
    return render_template("edit.html", **locals())

@app.route("/delete/<string:n>", methods=['GET', 'POST'])
def delete(n):
    n = ObjectId(n)
    admin_table.delete_one({"_id" : n})
    return render_template("deleted.html", **locals())



@app.route('/', methods=['GET', "POST"])
def index():
    loggedin = "logged_in" in session
    if "logged_in" in session:
        user = user_table.find_one({"username": session["username"]})
        return render_template("index.html", **locals())
    else:
        return render_template("index.html", **locals())


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5002)
