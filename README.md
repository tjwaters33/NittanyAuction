Nittany Auction Phase 2

This is the github repository for the implementation of the Nittany Auction Database Project.
Current Functions: Database Population, User Login, User Profile Update, User Registration, Category Hierarchy, Product Search, Auction Listing Management, Auction Bidding, Rating


Files:
    1.  init_database.py: 
        This file is responsible for initializing the database using the data given in the .csv files found in the repository. 
        This is where the tables in which the data will be stored in the database are created and populated.
        The relationships between data are also introduced, which are outlined in our Phase 1 Report.
        NOTE: User passwords must be stored as hashes and authenticated with hashes. Uses hashlib.sha256 to accomplish.

    2.  app.py:
        This file handles the backend logic for the database application.
        Implements all auction functionalties via Flask routes
        Handles HTML forms and user inputs, navigating the users to the correct pages.
        Establishes connection between Flask and SQLite3 database.

    3.  init_data
        Contains all of the CSV data files used by init_database to populate database data and create tables.

    4.  Static
        Contains CSS and JavaScript files, used throughout the Nittany Auction application.
        -   global.css: general application style
        -   homeStyles.css: homepage layout and listing grid
        -   loginStyles.css: login and register sytle
        -   productCard.js: dynamically creates listing cards

    5.  Templates
        Contains HTML files used to create the user interface
        -   base.html: login and register page layouts
        -   page.html: homepage layout and navbar
        -   imports.html: loads external libraries and global styles
        -   index.html: application landing page layout
        -   login.html: login form layout
        -   home.html: homepage layout with category browser
        -   register_bidder.html: register bidder account form layout
        -   register_seller.html: register seller account form layout
        -   register_local_vendor.html: register local vendor account form layout
        -   sellitem.html: create new listing form layout
        -   edit_listing.html: edit listing page layout
        -   view_listing.html: view listing details page layout
        -   my_listings.html: view seller listings page layout
        -   my_bids.html: view bidder bids page layout
        -   search_listings.html: search listings page layout 
        -   account.html: view and edit account page layout
        -   vendor_view.html: vendor info and rating layout
        -   requests.html: helpdest and request layout
        -   cart.html:
        -   tickets.html:
    
Functionalities
    1.  Database Population
        Initialize the database and populate the data from the CSV files.
        Store passwords as hash
        Files: init_database.py, all .csv files in init_data folder

    2.  User Login
        Logs user in using email, password and account type
        Passwords are converted to hash to be compared to the hash stored in the database
        Successful login creates session token where the account is stored, and directs user to the correct home page
        Files: app.py, login.html, index.html, page.html, base.html

    3.  User Registration
        Allows Bidder, Seller, and Local Business Vendor account creation
        Adds new account information to the database
        Files: app.py, register_bidder.html, register_seller.html, register_local_vendor.html, login.html, base.html

    4.  Auction Listing Management
        Allows sellers to create listings, edit listings and cancel listing
        Sellers have a My Listings page to view their listings.
        Sellers can request a new subcategory while creating listings
        Files: app.py, sellitem.html, edit_listing.html, my_listings.html, view_listing.html

    5.  Auction Bidding
        Allows bidders to place bids on active listings.
        Bidders must bid higher than the current bid
        Auction stops when max bids is reached
        Auction status is automatically updated
        Bidders have a My Bids page to view their active bids
        Files: view_listing.html, my_bids.html, productCard.js, app.py

    6.  Rating
        Allows bidders to give sellers a rating based on the trasaction
        Only allow the winning bidder to rate the seller after transaction goes through
        Files: vendor_view.html, app.py


    7.  Product Search
        Allows users to search for listings by title
        Separate search page 
        Files: search_listings.html, productCard.js, app.py


    8.  User Profile Update
        Allows users to view and update account info
        Users have an account page to view and update information
        Allows specific user types to edit type specific information
        Files: account.html, app.py


    9.  Category Hierarchy
        Categories are stored with parent and child information
        Allows user to click on subcategories to see current listings
        Category hierarchy is viewable from the homepage
        Files: app.py, home.html, page.html, productCard.js


How To Run:
1) run init_database.py
2) run app.py
3) Copy web address into browser 'http://127.0.0.1:5000/'
Command Prompt:
1) Navigate to directory
2) python init_database.py
3) python app.py
4) Move to browser and paste address 'http://127.0.0.1:5000/'

