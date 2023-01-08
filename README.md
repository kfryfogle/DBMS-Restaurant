# DBMS-Restaurant
Final Project for CS 5200: Database Management Systems at Northeastern University

Project Demonstration:
https://drive.google.com/file/d/188Kmt945hH_n-YgbjN-f7tsm-8aY300O/view?usp=sharing

Required Python Modules:
  pymysql: (https://pypi.org/project/PyMySQL/), 
  re,
  flask: (https://pypi.org/project/Flask/)
  
README Instructions:
  1.) Make sure to install and import the required python modules.
  
  2.) Import/load the restaurantdb database into the MySQL Workbench from the dbdumps
  folder, the dump file is named restaurantdbdumpFINAL.sql.
  
  3.) Open the restaurantdb.py file from the Flask_Integration folder in the Python IDE.
  
  4.) run the restaurantdb.py file in the IDE.
  
  5.) The program will open the website in your default browser.
  
  6.) If otherwise, the terminal response will provide a direct link to the site's landing page.
  
  7.) Use link provided to visit the site (usually port 5000 unless otherwise specified).
  
Project Overview:

This is an application that both guests and employees can interact with during working hours of operation. The program consists of 2 different types
of user views, one for employees and one for customers. The employee view will be able to alter the restaurant's menu by having the voice of adding, altering or deleting menu items. These menu items can be chosen from the list of menu items or can be filtered by price, category and ingredients. The employee will also be able to view orders placed by customers.
Restaurant customers can view the menu and filter items by price, category and ingredients before placing an order. When a customer is done viewing the menu, they
have the option to add items to their cart and place an order. Menu item data will be supplied from our own ideas based on the restaurant type of our choosing.

Each user view utilizes the pymysql library in order to enact changes to the restaurantdb database through varying CRUD operations. This application uses the Python Flask framework in order to dynamically display data throughout the site. the regular expressions module, re, is utilized in this project to parse user input data.
