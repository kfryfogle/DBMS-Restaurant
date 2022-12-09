from flask import Flask, g, redirect, render_template, request, session, url_for
from helper_functions import get_ingredients, get_bycategories, get_connection
import pymysql
import re

'''
CS 5200 Fall 2022
DBMS Project - Flask Restaurant

Kyle Fryfogle
Anthony Lee
'''

site = Flask(__name__)
site.secret_key = 'fryfoglekey'

@site.before_request
def before_request():
    # ignore db login route
    if request.endpoint == "frontpage":
        return
    g.user = None
    if 'user_id' in session:
        connection = get_connection(session['dbuser'], session['dbpw'])
        userquery = "SELECT * FROM employee"
        c = connection.cursor()
        c.execute(userquery)
        for user in c.fetchall():
            if (user['employee_id'] == session['user_id']):
                g.user = user 
        
@site.route("/", methods=["GET", "POST"])
def frontpage():
    if request.method == "POST":
        try:
            connection = get_connection(request.form['username'], request.form['password'])
            session['dbuser'] = request.form['username']
            session['dbpw'] = request.form['password'] 
            lastgidq = "SELECT MAX(order_id) AS lastorder FROM order_details LIMIT 1"
            c = connection.cursor()
            c.execute(lastgidq)
            lastgid = int((c.fetchone()['lastorder']))
            session['guestid'] = lastgid + 1
            return redirect(url_for('home'))
        except:
            return render_template("frontpage.html")
    return render_template("frontpage.html")

@site.route("/Home")
def home():
    if "guest_id" not in session:
        connection = get_connection(session['dbuser'], session['dbpw'])
        c2 = connection.cursor()
        c3 = connection.cursor()
        # add a count if null first
        newvisq = "INSERT INTO visitors VALUES ();"
        c2.execute(newvisq)
        guestidq = "SELECT * FROM visitors ORDER BY vis_num DESC LIMIT 1"
        c3.execute(guestidq)
        # retrieve new id
        id = c3.fetchone()
        # get/increment the last order number from orders
        session["guest_id"] = id['vis_num']
    session.pop('user_id', None)
    return render_template('homepage.html')

@site.route("/Employee", methods=['GET','POST'])
def emplogin():
    connection = get_connection(session['dbuser'], session['dbpw'])
    userquery = "SELECT * FROM employee"
    session.pop('user_id', None)
    error = None
    if request.method == "POST":
        c1 = connection.cursor()
        c1.execute(userquery)
        # check for valid credentials
        for user in c1.fetchall():
            if (user['username'] == request.form['username'] and user['password'] == request.form['password']):
                session['user_id'] = user['employee_id']
                return redirect(url_for('empmenu'))              
        # invalid credentials
        error = "Invalid Credentials. Please Try Again."
    return render_template('emplogin.html', error=error)

@site.route("/EmpMenu", methods=['GET','POST'])
def empmenu():
    connection = get_connection(session['dbuser'], session['dbpw'])
    if g.user == None:
        return redirect(url_for('home'))
    itemlist = []
    # ingredientdict = {}
    ingredientquerybase = "SELECT r.*, i.ingredient_name FROM recipe r INNER JOIN ingredient i ON i.ingredient_id = r.ingredient_id WHERE ({});"
    categoryquerybase = "SELECT * FROM food_item WHERE ({});"
    pricequerybase = "SELECT * FROM food_item WHERE price <= '{}' ORDER BY price DESC"

    if request.method == "POST" and "options" in request.form:
        # filter by ingredients
        if request.form['options'] == "ingredients":
            whereclause = ""
            # parse input filter terms
            parsedinput = re.split(", |,", request.form['filterquery'])
            # add filter parses to query string using OR
            for i in range(0, len(parsedinput)):
                # last item
                if (i == len(parsedinput) - 1):
                    whereclause = whereclause + f"i.ingredient_name = '{parsedinput[i]}'"
                else:
                    whereclause = whereclause + f"i.ingredient_name = '{parsedinput[i]}' OR "
            ingredientq1 = "SELECT bq.item_name FROM (" + ingredientquerybase.format(whereclause).replace(";", "") + ") bq"
            # itemquery use depends on navigation
            itemquery = f'SELECT * FROM food_item WHERE item_name IN ({ingredientq1});'
            # if filtering by menu type might need to reassign itemquery and add a menutype = ...
            c2 = connection.cursor()
            c2.execute(itemquery)
            # move matching menu items to an array
            for row in c2.fetchall():
                ingredientq2 = ingredientquerybase.format("item_name = '" + row['item_name'] + "'")
                # second query for each items ingredients
                row['ingredients'] = get_ingredients(connection, ingredientq2)
                itemlist.append(row)
            itemlist = get_bycategories(itemlist)
            render_template('empmenu.html', filteritems=itemlist, title='Menu')
            # input matching menu items to page
            return render_template('empmenu.html', filteritems=itemlist, title='Menu')

        # filter by price
        if request.form['options'] == "price":
            # parse input filter terms
            parsedinput = re.split(", |,", request.form['filterquery'])
            # take in the first price parameter, no multi inputs for this filter
            priceq = pricequerybase.format(parsedinput[0])
            c2 = connection.cursor()
            c2.execute(priceq)
            # move matching menu items to an array
            for row in c2.fetchall():
                priceq2 = ingredientquerybase.format("item_name = '" + row['item_name'] + "'")
                # second query for each items ingredients
                row['ingredients'] = get_ingredients(connection, priceq2)
                itemlist.append(row)
            itemlist = get_bycategories(itemlist)
            return render_template('empmenu.html', filteritems=itemlist, title="Menu")

        # filter by category
        if request.form['options'] == "category":
            whereclause = ""
            # parse input filter terms
            parsedinput = re.split(", |,", request.form['filterquery'])
            # add filter parses to query string using OR
            for i in range(0, len(parsedinput)):
                # last item
                if (i == len(parsedinput) - 1):
                    whereclause = whereclause + f"category = '{parsedinput[i]}'"
                else:
                    whereclause = whereclause + f"category = '{parsedinput[i]}' OR "
            # take in the first price parameter, no multi inputs for this filter
            categoryq = categoryquerybase.format(whereclause)
            c2 = connection.cursor()
            c2.execute(categoryq)
            # move matching menu items to an array
            for row in c2.fetchall():
                categoryq2 = ingredientquerybase.format("item_name = '" + row['item_name'] + "'")
                # second query for each items ingredients
                row['ingredients'] = get_ingredients(connection, categoryq2)
                itemlist.append(row)
            itemlist = get_bycategories(itemlist)
            return render_template('empmenu.html', filteritems=itemlist, title="Menu")

    if request.method == "POST" and 'edit_button' in request.form:
        fooditemq = "SELECT * FROM food_item WHERE item_name = {}"
        edithistq = "INSERT INTO edithistory(item_name, editor_id) VALUES ('{}', {});"
        c2 = connection.cursor()
        # add to edit history log
        c2.execute(edithistq.format(request.form['edit_button'], g.user['employee_id']))
        # need to input ingredients list as variable
        return redirect(url_for('editor'))

    if request.method == "POST" and 'delete_button' in request.form:
        fooditemdel = "DELETE FROM food_item WHERE item_name = '{}'"
        recipedel = "DELETE FROM recipe where item_name = '{}'"
        c2 = connection.cursor()
        c3 = connection.cursor()
        c2.execute(recipedel.format(request.form['delete_button']))
        c3.execute(fooditemdel.format(request.form['delete_button']))
        itemquery = 'SELECT * FROM food_item;'
        # get ingredients list for all items
        c4 = connection.cursor()
        c4.execute(itemquery)
        # move matching menu items to an array
        for row in c4.fetchall():
            # second query for each items ingredients
            ingredientq = ingredientquerybase.format("item_name = '" + row['item_name'] + "'")
            row['ingredients'] = get_ingredients(connection, ingredientq)
            itemlist.append(row)
        itemlist = get_bycategories(itemlist)
        return render_template('empmenu.html', filteritems=itemlist, title="Employee Menu")

    if request.method == "POST" and "add_button" in request.form:
        return redirect(url_for('add'))

    # get ingredients list for all items
    itemquery = 'SELECT * FROM food_item;'
    c2 = connection.cursor()
    c2.execute(itemquery)
    # move matching menu items to an array
    for row in c2.fetchall():
        # second query for each items ingredients
        ingredientq = ingredientquerybase.format("item_name = '" + row['item_name'] + "'")
        row['ingredients'] = get_ingredients(connection, ingredientq)
        itemlist.append(row)
    itemlist = get_bycategories(itemlist)
    return render_template('empmenu.html', filteritems=itemlist, title='Employee Menu')

@site.route("/add", methods=['GET','POST'])
def add():
    if g.user == None:
        return redirect(url_for('emplogin'))
    connection = get_connection(session['dbuser'], session['dbpw'])
    foodquerybase = "SELECT item_name FROM food_item;"
    if request.method == "POST":
        if "add" in request.form:
            name = request.form['item_name'] 
            # check if there is an item with the same name
            c2 = connection.cursor()
            c2.execute(foodquerybase)
            item_exists = False
            for row in c2.fetchall():
                if request.form['item_name'] == row['item_name']:
                    item_exists = True
            # item already exists, add nameerror message and try again
            if item_exists == True:
                nameerror = "Item with this name already exists!"
                return render_template("add.html", title="Add Menu Item", nameerror=nameerror)
            # item_name, description, category, price, employee_id
            addfoodq = "INSERT INTO food_item VALUES ('{}', '{}', '{}', '{}', '{}')".format(name, request.form['description'], request.form['categories'], request.form['price'], g.user['employee_id'])
            c3 = connection.cursor()
            c3.execute(addfoodq)
            # check if all ingredients currently exist in the ingredients list before adding to recipe
            newings = request.form['ingredients']
            splitings = newings.split(", ")
            for each in splitings:
                allingredientsq = "SELECT * FROM ingredient"
                c4 = connection.cursor()
                c4.execute(allingredientsq)
                ingexists = False
                # check if ingredient exists in ingredients table
                for ingredient in c4.fetchall():
                    if ingredient['ingredient_name'] == each:
                        ingexists = True
                # ingredient doesnt exist
                if ingexists == False:
                    insertingq = "INSERT INTO ingredient VALUES (NULL, '{}')".format(each)
                    # INSERT NEW INGREDIENT TO TABLE
                    c5 = connection.cursor()
                    c5.execute(insertingq)
                # retrieve ingredient_id of ingredient
                idqbase = "SELECT * FROM ingredient WHERE ingredient_name = '{}'".format(each)
                c6 = connection.cursor()
                c6.execute(idqbase)
                ingredientitem = c6.fetchone()
                # once created, add ingredient to current recipe
                insertqbase = "INSERT INTO recipe VALUES ({});"
                itembase = "'{0}','{1}'".format(name, ingredientitem['ingredient_id']) 
                insertq = insertqbase.format(itembase)
                c7 = connection.cursor()
                c7.execute(insertq) 
            return redirect(url_for("empmenu"))
        if "back" in request.form:
            return redirect(url_for("empmenu"))
    return render_template("add.html", title="Add Menu Item")

@site.route("/editor", methods=['GET','POST'])
def editor():
    if g.user == None:
       return redirect(url_for('emplogin'))
    toeditq = "SELECT edit_num, item_name FROM edithistory ORDER BY edit_num DESC LIMIT 1;"
    foodquerybase = "SELECT * FROM food_item WHERE ({});"
    ingredientquerybase = "SELECT r.*, i.ingredient_name FROM recipe r INNER JOIN ingredient i ON i.ingredient_id = r.ingredient_id WHERE ({});"
    # retrieve the last inserted edit details
    connection = get_connection(session['dbuser'], session['dbpw'])
    c2 = connection.cursor()
    c2.execute(toeditq)
    editinfo = c2.fetchone()
    c3 = connection.cursor()
    c3.execute(foodquerybase.format("item_name = '{}'".format(editinfo['item_name'])))
    edititem = c3.fetchone()
    if request.method == "POST":
        if "save_exit" in request.form:
            # write all changes to tables
            newdesc = request.form['description']
            newprice = request.form['price']
            # UPDATE DESCRIPTION AND PRICE
            updatequery = "UPDATE food_item SET description = '{0}', price = {1} WHERE item_name = '{2}'".format(newdesc, newprice, edititem['item_name'])
            updatec = connection.cursor()
            updatec.execute(updatequery)
            newings = request.form['ingredients']
            splitings = newings.split(", ")
            recipedelbase = "DELETE FROM recipe WHERE item_name = '{}';"
            recipedelq = recipedelbase.format(edititem['item_name'])
            # delete the current recipe
            c = connection.cursor()
            c.execute(recipedelq)
            # check if all input ingredients exist first
            for each in splitings:
                allingredientsq = "SELECT * FROM ingredient"
                c4 = connection.cursor()
                c4.execute(allingredientsq)
                ingexists = False
                # check if ingredient exists in ingredients table
                for ingredient in c4.fetchall():
                    if ingredient['ingredient_name'] == each:
                        ingexists = True
                # ingredient doesnt exist
                if ingexists == False:
                    insertingq = "INSERT INTO ingredient VALUES (NULL, '{}')".format(each)
                    # INSERT NEW INGREDIENT TO TABLE
                    c5 = connection.cursor()
                    c5.execute(insertingq)
                # retrieve ingredient_id of ingredient
                idqbase = "SELECT * FROM ingredient WHERE ingredient_name = '{}'".format(each)
                c6 = connection.cursor()
                c6.execute(idqbase)
                ingredientitem = c6.fetchone()
                # once created, add ingredient to current recipe
                insertqbase = "INSERT INTO recipe VALUES ({});"
                itembase = "'{0}','{1}'".format(edititem['item_name'], ingredientitem['ingredient_id']) 
                insertq = insertqbase.format(itembase)
                c7 = connection.cursor()
                c7.execute(insertq)
                whereclause = "item_name = '{}'".format(edititem['item_name'])
                ingredientq = ingredientquerybase.format(whereclause)
                ingredients = get_ingredients(connection, ingredientq)
                edititem['ingredients'] = ingredients
            return render_template("editor.html", chosenitem=edititem)
        if "delete_item" in request.form:
            fooditemdel = "DELETE FROM food_item WHERE item_name = '{}'"
            recipedel = "DELETE FROM recipe where item_name = '{}'"
            c4 = connection.cursor()
            c5 = connection.cursor()
            c4.execute(recipedel.format(request.form['delete_button']))
            c5.execute(fooditemdel.format(request.form['delete_button']))
            return render_template('empmenu.html', title="Employee Menu")
        if "back" in request.form:
            return redirect(url_for("empmenu"))
    whereclause = "item_name = '{}'".format(edititem['item_name'])
    ingredientq = ingredientquerybase.format(whereclause)
    ingredients = get_ingredients(connection, ingredientq)
    edititem['ingredients'] = ingredients
    return render_template("editor.html", chosenitem=edititem)
        
@site.route("/Orders")
def orders():
    if g.user == None:
        return redirect(url_for('emplogin'))
    connection = get_connection(session['dbuser'], session['dbpw'])
    # get all item names and quantities from order
    maxordersq = "SELECT MAX(order_id) as order_id FROM order_details ORDER BY order_id;"
    c2 = connection.cursor()
    c2.execute(maxordersq)
    maxorder = c2.fetchone()
    orderitemsqbase = "SELECT * FROM order_details WHERE order_id = {}"
    fooditemqbase = "SELECT * FROM food_item WHERE item_name = '{}';"
    allorders = []
    for i in range(1, maxorder['order_id'] + 1):
        # for every order
        order = {}
        itemquery = orderitemsqbase.format(i)
        # retrieve every row for the current order
        c3 = connection.cursor()
        c3.execute(itemquery)
        totalprice = 0
        foodlist = []
        # for every item in the order
        for row in c3.fetchall():
            itemprice = 0
            c4 = connection.cursor()
            # get the current item dictionary from food_item
            c4.execute(fooditemqbase.format(row['item_name']))
            food_item = c4.fetchone()
            # set unit price
            itemprice = food_item['price'] * row['quantity']
            totalprice += itemprice
            # add item to food list
            foodlist.append(row)
        order['price'] = totalprice
        order['items'] = foodlist
        order['ordercount'] = i
        order['maxcount'] = maxorder['order_id']
        allorders.append(order)
    return render_template("orders.html", orders=allorders)

@site.route("/Menu", methods=['GET','POST'])
def menu():
    itemlist = []
    connection = get_connection(session['dbuser'], session['dbpw'])
    
    ingredientquerybase = "SELECT r.*, i.ingredient_name FROM recipe r INNER JOIN ingredient i ON i.ingredient_id = r.ingredient_id WHERE ({});"
    categoryquerybase = "SELECT * FROM food_item WHERE ({});"
    pricequerybase = "SELECT * FROM food_item WHERE price <= '{}' ORDER BY price DESC"

    if request.method == "POST" and "options" in request.form:
        # filter by ingredients
        if request.form['options'] == "ingredients":
            whereclause = ""
            # parse input filter terms
            parsedinput = re.split(", |,", request.form['filterquery'])
            # add filter parses to query string using OR
            for i in range(0, len(parsedinput)):
                # last item
                if (i == len(parsedinput) - 1):
                    whereclause = whereclause + f"i.ingredient_name = '{parsedinput[i]}'"
                else:
                    whereclause = whereclause + f"i.ingredient_name = '{parsedinput[i]}' OR "
            ingredientq1 = "SELECT bq.item_name FROM (" + ingredientquerybase.format(whereclause).replace(";", "") + ") bq"
            # itemquery use depends on navigation
            itemquery = f'SELECT * FROM food_item WHERE item_name IN ({ingredientq1});'
            print(itemquery)
            # if filtering by menu type might need to reassign itemquery and add a menutype = ...
            c2 = connection.cursor()
            c2.execute(itemquery)
            # move matching menu items to an array
            for row in c2.fetchall():
                ingredientq2 = ingredientquerybase.format("item_name = '" + row['item_name'] + "'")
                # second query for each items ingredients
                row['ingredients'] = get_ingredients(connection, ingredientq2)
                itemlist.append(row)
            itemlist = get_bycategories(itemlist)
            render_template('menu.html', filteritems=itemlist, title='Menu')
            
            # input matching menu items to page
            return render_template('menu.html', filteritems=itemlist, title='Menu')

        # filter by price
        if request.form['options'] == "price":
            # parse input filter terms
            parsedinput = re.split(", |,", request.form['filterquery'])
            # take in the first price parameter, no multi inputs for this filter
            priceq = pricequerybase.format(parsedinput[0])
            c2 = connection.cursor()
            c2.execute(priceq)
            # move matching menu items to an array
            for row in c2.fetchall():
                priceq2 = ingredientquerybase.format("item_name = '" + row['item_name'] + "'")
                # second query for each items ingredients
                row['ingredients'] = get_ingredients(connection, priceq2)
                itemlist.append(row)
            itemlist = get_bycategories(itemlist)
            return render_template('menu.html', filteritems=itemlist, title="Menu")

        # filter by category
        if request.form['options'] == "category":
            whereclause = ""
            # parse input filter terms
            parsedinput = re.split(", |,", request.form['filterquery'])
            # add filter parses to query string using OR
            for i in range(0, len(parsedinput)):
                # last item
                if (i == len(parsedinput) - 1):
                    whereclause = whereclause + f"category = '{parsedinput[i]}'"
                else:
                    whereclause = whereclause + f"category = '{parsedinput[i]}' OR "
            # take in the first price parameter, no multi inputs for this filter
            categoryq = categoryquerybase.format(whereclause)
            c2 = connection.cursor()
            c2.execute(categoryq)
            # move matching menu items to an array
            for row in c2.fetchall():
                categoryq2 = ingredientquerybase.format("item_name = '" + row['item_name'] + "'")
                # second query for each items ingredients
                row['ingredients'] = get_ingredients(connection, categoryq2)
                itemlist.append(row)
            itemlist = get_bycategories(itemlist)
            return render_template('menu.html', filteritems=itemlist, title="Menu")
            
    if request.method == "POST" and "add" in request.form:
        insertcartq = "INSERT INTO cart VALUES ({}, '{}', {});".format(session['guest_id'], request.form['add'], request.form['qty'])
        itemquery = 'SELECT * FROM food_item;'
        c2 = connection.cursor()
        c3 = connection.cursor()
        c4 = connection.cursor() 
        if request.form['qty'] == 0:
            # dont add to cart and refresh page
            c2.execute(itemquery)
            for row in c2.fetchall():
                # second query for each items ingredients
                ingredientq = ingredientquerybase.format("item_name = '" + row['item_name'] + "'")
                row['ingredients'] = get_ingredients(connection, ingredientq)
                itemlist.append(row)
            itemlist = get_bycategories(itemlist)
            return render_template('menu.html', filteritems=itemlist, title='Menu')
        # add an item to order_details with quantity
        print(insertcartq)
        c3.execute(insertcartq)
        c4.execute(itemquery)
        # move matching menu items to an array
        for row in c4.fetchall():
            # second query for each items ingredients
            ingredientq = ingredientquerybase.format("item_name = '" + row['item_name'] + "'")
            row['ingredients'] = get_ingredients(connection, ingredientq)
            itemlist.append(row)
        itemlist = get_bycategories(itemlist)
        return render_template('menu.html', filteritems=itemlist, title='Menu')

    # itemquery use depends on navigation
    itemquery = 'SELECT * FROM food_item;'
    c2 = connection.cursor()
    c2.execute(itemquery)
    # move matching menu items to an array
    for row in c2.fetchall():
        # second query for each items ingredients
        ingredientq = ingredientquerybase.format("item_name = '" + row['item_name'] + "'")
        row['ingredients'] = get_ingredients(connection, ingredientq)
        itemlist.append(row)
    itemlist = get_bycategories(itemlist)
    return render_template('menu.html', filteritems=itemlist, title='Menu')

@site.route("/Cart", methods=["GET", "POST"])
def cart():
    detailsqbase = "SELECT * FROM cart WHERE vis_num = {}"
    itemq = "SELECT * FROM food_item WHERE item_name = '{}'"
    connection = get_connection(session['dbuser'], session['dbpw'])
    if request.method == "POST":
        if "order" in request.form:
            # collect all items from cart in current session
            # INSERT INTO ORDER DETAILS
            orderqbase = "INSERT INTO order_details(order_id, item_name, quantity) VALUES {};"
            detailsq = detailsqbase.format(session['guest_id'])
            c2 = connection.cursor()
            c2.execute(detailsq)
            itemlist = c2.fetchall()
            strlist = ""
            for i in range(0, len(itemlist)):
                if i == len(itemlist) - 1:
                    string = "({0},'{1}',{2})".format(itemlist[i]['vis_num'], itemlist[i]['item_name'], itemlist[i]['quantity'])
                    strlist += string
                else: 
                    string = "({0},'{1}',{2}), ".format(itemlist[i]['vis_num'], itemlist[i]['item_name'], itemlist[i]['quantity'])
                    strlist += string
            orderq = orderqbase.format(strlist)
            c3 = connection.cursor()
            c3.execute(orderq)
            # THEN DELETE ALL FROM CART
            clearcartq = "DELETE FROM cart WHERE vis_num = {}".format(session['guest_id'])
            c4 = connection.cursor()
            c4.execute(clearcartq)

            return redirect(url_for('menu'))

        if "delete" in request.form:
            info = request.form['delete']
            # dictionary object returns in full string format from button
            splitinfo = re.split("{|}|', 'quantity': |, 'item_name': '|'vis_num': ", info)
            cleaninfo = []
            for i in range(0, len(splitinfo)):
                if len(splitinfo[i]) == 0:
                    continue
                cleaninfo.append(splitinfo[i])
            deleteqbase = "DELETE FROM cart WHERE vis_num = {0} AND item_name = '{1}' AND quantity = {2};"
            deleteq = deleteqbase.format(int(cleaninfo[0]), cleaninfo[1], int(cleaninfo[2]))
            c4 = connection.cursor()
            c4.execute(deleteq)
            # retrieve items for the current cart
            detailsq = detailsqbase.format(session['guest_id'])
            c2 = connection.cursor()
            c2.execute(detailsq)
            totalprice = 0
            foodlist = []
            for row in c2.fetchall():
                itemprice = 0
                c3 = connection.cursor()
                c3.execute(itemq.format(row['item_name']))
                food_item = c3.fetchone()
                itemprice = food_item['price'] * row['quantity']
                totalprice += itemprice
                foodlist.append(row)
            return render_template("cart.html", allitems=foodlist, pricetotal=totalprice)
    # retrieve items for the current cart
    detailsq = detailsqbase.format(session['guest_id'])
    c2 = connection.cursor()
    c2.execute(detailsq)
    totalprice = 0
    foodlist = []
    for row in c2.fetchall():
        itemprice = 0
        c3 = connection.cursor()
        c3.execute(itemq.format(row['item_name']))
        food_item = c3.fetchone()
        # price by quantity, add to total
        itemprice = food_item['price'] * row['quantity']
        totalprice += itemprice
        # add item to food list
        foodlist.append(row)
    return render_template("cart.html", allitems=foodlist, pricetotal=totalprice)

if __name__ == "__main__":
    site.run(debug=True)
