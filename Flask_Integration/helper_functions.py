import pymysql

'''
Kyle Fryfogle
Anthony Lee
CS 5200
Project Helper Functions
'''

'''
Helper function used to find the ingredients within an input items recipe
'''
def get_ingredients(connect, query2):
    c = connect.cursor()
    c.execute(query2)
    ing = []
    # add all ingredients for current menu item
    for row in c.fetchall():
        ing.append(row["ingredient_name"])
    ing = ", ".join(ing)
    return ing


'''
Getter function that sorts each item by their categorical attribute
'''
def get_bycategories(itemlist):
    drinks = []
    side = []
    entree = []
    for i in itemlist:
        if i['category'] == 'drink':
            drinks.append(i)
            continue
        elif i['category'] == 'side':
            side.append(i)
            continue
        entree.append(i)
    counter = 1
    for item in drinks:
        item['order'] = counter
        counter += 1
    for item in entree:
        item['order'] = counter
        counter += 1
    for item in side:
        item['order'] = counter
        counter += 1
    sort = [drinks, entree, side]
    return sort

'''
Getter function to retrieve a mysql server connection, given login parameters
'''
def get_connection(u, pw):
    connection = pymysql.connect(host='localhost',
                                 user=u,
                                 password=pw,
                                 database='restaurantdb',
                                 cursorclass=pymysql.cursors.DictCursor,
                                 autocommit=True)
    return connection
