import csv
import hashlib
import sqlite3

# create database
DB_NAME = "database.db"


# connect to database using sqlite3
def get_connection():
    connect = sqlite3.connect(DB_NAME)
    #foreign key rule enforcement
    connect.execute("PRAGMA foreign_keys = ON;")
    return connect


# hashlib to hash and store hashed password
def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# create relational schema tables in databse using cursor *sqlite3*
def create_tables():
    connect = get_connection()
    cur = connect.cursor()

    # Delete any already existing tables with schema names
    cur.executescript("""
    DROP TABLE IF EXISTS Ratings;
    DROP TABLE IF EXISTS Transactions;
    DROP TABLE IF EXISTS Bids;
    DROP TABLE IF EXISTS Auction_Listings;
    DROP TABLE IF EXISTS Local_Vendors;
    DROP TABLE IF EXISTS Sellers;
    DROP TABLE IF EXISTS Credit_Cards;
    DROP TABLE IF EXISTS Bidders;
    DROP TABLE IF EXISTS Requests;
    DROP TABLE IF EXISTS Helpdesk;
    DROP TABLE IF EXISTS Address;
    DROP TABLE IF EXISTS Zipcode_Info;
    DROP TABLE IF EXISTS Categories;
    DROP TABLE IF EXISTS Users;
    """)

    # Execute SQL relationship scripts from phase 1 report
    # ensure table hierarchy, child after parent, for foreign key relations
    cur.executescript("""
    CREATE TABLE Users (
        email TEXT PRIMARY KEY,
        password TEXT NOT NULL
    );

    CREATE TABLE Helpdesk (
        email TEXT PRIMARY KEY,
        position TEXT,
        FOREIGN KEY (email) REFERENCES Users(email)
    );

    CREATE TABLE Zipcode_Info (
        zipcode INTEGER PRIMARY KEY,
        city TEXT NOT NULL,
        state TEXT NOT NULL
    );

    CREATE TABLE Address (
        address_id TEXT PRIMARY KEY,
        zipcode INTEGER NOT NULL,
        street_num INTEGER NOT NULL,
        street_name TEXT NOT NULL,
        FOREIGN KEY (zipcode) REFERENCES Zipcode_Info(zipcode)
    );

    CREATE TABLE Bidders (
        email TEXT PRIMARY KEY,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        age INTEGER,
        home_address_id TEXT,
        major TEXT,
        FOREIGN KEY (email) REFERENCES Users(email),
        FOREIGN KEY (home_address_id) REFERENCES Address(address_id)
    );

    CREATE TABLE Sellers (
        email TEXT PRIMARY KEY,
        bank_routing_number TEXT NOT NULL,
        bank_account_number INTEGER NOT NULL,
        balance REAL DEFAULT 0,
        FOREIGN KEY (email) REFERENCES Users(email)
    );

    CREATE TABLE Local_Vendors (
        email TEXT PRIMARY KEY,
        business_name TEXT NOT NULL,
        business_address_id TEXT NOT NULL,
        customer_service_phone_number TEXT NOT NULL,
        FOREIGN KEY (email) REFERENCES Sellers(email),
        FOREIGN KEY (business_address_id) REFERENCES Address(address_id)
    );

    CREATE TABLE Credit_Cards (
        credit_card_num TEXT PRIMARY KEY,
        card_type TEXT NOT NULL,
        expire_month INTEGER NOT NULL,
        expire_year INTEGER NOT NULL,
        security_code INTEGER NOT NULL,
        owner_email TEXT NOT NULL,
        FOREIGN KEY (owner_email) REFERENCES Bidders(email)
    );

    CREATE TABLE Categories (
        category_name TEXT PRIMARY KEY,
        parent_category TEXT,
        FOREIGN KEY (parent_category) REFERENCES Categories(category_name)
    );

    CREATE TABLE Requests (
        request_id INTEGER PRIMARY KEY,
        sender_email TEXT NOT NULL,
        helpdesk_staff_email TEXT NOT NULL,
        request_type TEXT NOT NULL,
        request_desc TEXT NOT NULL,
        request_status INTEGER NOT NULL CHECK (request_status IN (0,1)),
        FOREIGN KEY (sender_email) REFERENCES Users(email),
        FOREIGN KEY (helpdesk_staff_email) REFERENCES Helpdesk(email)
    );

    CREATE TABLE Auction_Listings (
        seller_email TEXT NOT NULL,
        listing_id INTEGER NOT NULL,
        category TEXT NOT NULL,
        auction_title TEXT NOT NULL,
        product_name TEXT NOT NULL,
        product_description TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        reserve_price REAL NOT NULL,
        max_bids INTEGER NOT NULL,
        status INTEGER NOT NULL CHECK (status IN (0,1,2)),
        PRIMARY KEY (seller_email, listing_id),
        FOREIGN KEY (seller_email) REFERENCES Sellers(email),
        FOREIGN KEY (category) REFERENCES Categories(category_name)
    );

    CREATE TABLE Bids (
        bid_id INTEGER PRIMARY KEY,
        seller_email TEXT NOT NULL,
        listing_id INTEGER NOT NULL,
        bidder_email TEXT NOT NULL,
        bid_price REAL NOT NULL,
        FOREIGN KEY (seller_email, listing_id)
            REFERENCES Auction_Listings(seller_email, listing_id),
        FOREIGN KEY (bidder_email) REFERENCES Bidders(email)
    );

    CREATE TABLE Transactions (
        transaction_id INTEGER PRIMARY KEY,
        seller_email TEXT NOT NULL,
        listing_id INTEGER NOT NULL,
        bidder_email TEXT NOT NULL,
        date TEXT NOT NULL,
        payment REAL NOT NULL,
        FOREIGN KEY (seller_email, listing_id)
            REFERENCES Auction_Listings(seller_email, listing_id),
        FOREIGN KEY (bidder_email) REFERENCES Bidders(email)
    );

    CREATE TABLE Ratings (
        bidder_email TEXT NOT NULL,
        seller_email TEXT NOT NULL,
        date TEXT NOT NULL,
        rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
        rating_desc TEXT,
        PRIMARY KEY (bidder_email, seller_email, date),
        FOREIGN KEY (bidder_email) REFERENCES Bidders(email),
        FOREIGN KEY (seller_email) REFERENCES Sellers(email)
    );
    """)

    # Commit and close
    connect.commit()
    connect.close()


# !!! Dataset Import Functions!!!
# sqlite3 to insert dataset into database
# All functions have similar format
# Connect, open data, insert, close

# Import user dataset
# Ensure hashed password storage!
def import_users():
    # connect database
    connect = get_connection()
    cur = connect.cursor()

    # open dataset, read, get data
    f = open("Users.csv", "r", newline="", encoding="utf-8-sig")
    #Skip heading
    next(f)
    for row in f:
        #clean each row
        row = row.strip()
        content = row.split(",")

        email = content[0].strip()
        password = hash_password(content[1].strip())

        # sqlite3 instert data into database
        cur.execute("INSERT INTO Users (email, password) VALUES (?, ?)", (email, password))

    # ensure commit and close
    f.close()
    connect.commit()
    connect.close()


# Import helpdesk dataset
# User must exist before becoming helpdesk
def import_helpdesk():
    connect = get_connection()
    cur = connect.cursor()

    # open dataset, read, get data
    f = open("Helpdesk.csv", "r", encoding="utf-8-sig")
    # skip header
    next(f)  
    for row in f:
        #clean each row
        row = row.strip()
        content = row.split(",")

        email = content[0].strip()
        position = content[1].strip()

        # sqlite3 insert helpdesk user into user data
        # Helpdesk users need a password!
        cur.execute("INSERT OR IGNORE INTO Users (email, password) VALUES (?, ?)", (email, hash_password("temporary")))

        # sqlite3 insert helpdesk role into database
        cur.execute("INSERT INTO Helpdesk (email, position) VALUES (?, ?)", (email, position))

    # ensure commit and close
    f.close()
    connect.commit()
    connect.close()


# Import zipcode info dataset
def import_zipcode_info():
    connect = get_connection()
    cur = connect.cursor()

    # open dataset, read, get data
    f = open("Zipcode_Info.csv", "r", newline="", encoding="utf-8-sig")
    # skip header
    next(f)
    for row in f:
        #clean each row
        row = row.strip()
        content = row.split(",")

        zipcode = int(content[0].strip())
        city = content[1].strip()
        state = content[2].strip()
        # sqlite3 insert zipcode info database
        cur.execute("INSERT INTO Zipcode_Info (zipcode, city, state) VALUES (?, ?, ?)", (zipcode, city, state))

    # ensure commit and close
    f.close()
    connect.commit()
    connect.close()


# Import address dataset
def import_address():
    connect = get_connection()
    cur = connect.cursor()

    f = open("Address.csv", "r", newline="", encoding="utf-8-sig")
    # skip header
    next(f)
    for row in f:
        #clean each row
        row = row.strip()
        content = row.split(",")

        address_id = content[0].strip()
        zipcode = int(content[1].strip())
        street_num = int(content[2].strip())
        street_name = content[3].strip()

        # sqlite3 insert address into database
        cur.execute("INSERT INTO Address (address_id, zipcode, street_num, street_name) VALUES (?, ?, ?, ?)", (address_id, zipcode, street_num, street_name))

    # ensure commit and close
    f.close()
    connect.commit()
    connect.close()


# Import bidders dataset
def import_bidders():
    connect = get_connection()
    cur = connect.cursor()

    # open dataset, read, get data
    f = open("Bidders.csv", "r", encoding="utf-8-sig")
    # skip header
    next(f)  
    for row in f:
        #clean each row
        row = row.strip()
        content = row.split(",")

        email = content[0].strip()
        first_name = content[1].strip()
        last_name = content[2].strip()
        # blank entry error checking, unrequired fields
        age = None
        if content[3].strip() != "":
            age = int(content[3].strip())
        home_address_id = None
        if content[4].strip() != "":
            home_address_id = content[4].strip()
        major = None
        if content[5].strip() != "":
            major = content[5].strip()

        # sqlite3 insert bidders into database
        cur.execute("INSERT INTO Bidders (email, first_name, last_name, age, home_address_id, major) VALUES (?, ?, ?, ?, ?, ?)", (email, first_name, last_name, age, home_address_id, major))

    # ensure commit and close
    f.close()
    connect.commit()
    connect.close()


# Import sellers dataset
def import_sellers():
    connect = get_connection()
    cur = connect.cursor()

    # open dataset, read, get data
    f = open("Sellers.csv", "r", encoding="utf-8-sig")
    # skip header
    next(f)  
    for row in f:
        #clean each row
        row = row.strip()
        content = row.split(",")

        email = content[0].strip()
        bank_routing_number = content[1].strip()
        bank_account_number = int(content[2].strip())
        balance = float(content[3].strip())

        # sqlite3 insert sellers into database
        cur.execute("INSERT INTO Sellers (email, bank_routing_number, bank_account_number, balance) VALUES (?, ?, ?, ?)", (email, bank_routing_number, bank_account_number, balance))

    # ensure commit and close
    f.close()
    connect.commit()
    connect.close()


# Import local vendors dataset
def import_local_vendors():
    connect = get_connection()
    cur = connect.cursor()

    # open dataset, read, get data
    f = open("Local_Vendors.csv", "r", encoding="utf-8-sig")
    # business names can have commas :( alternate logic to handle
    i = csv.reader(f)
    # skip header
    next(i)  
    for row in i:
        #clean each row
        email = row[0].strip()
        business_name = row[1].strip()
        business_address_id = row[2].strip()
        customer_service_phone_number = row[3].strip()

        # sqlite3 insert local vendors into database
        cur.execute("INSERT INTO Local_Vendors (email, business_name, business_address_id, customer_service_phone_number) VALUES (?, ?, ?, ?)", (email, business_name, business_address_id, customer_service_phone_number))

    # ensure commit and close
    f.close()
    connect.commit()
    connect.close()


# Import credit cards dataset
def import_credit_cards():
    connect = get_connection()
    cur = connect.cursor()

    # open dataset, read, get data
    f = open("Credit_Cards.csv", "r", encoding="utf-8-sig")
    # skip header
    next(f)  
    for row in f:
        #clean each row
        row = row.strip()
        content = row.split(",")

        credit_card_num = content[0].strip()
        card_type = content[1].strip()
        expire_month = int(content[2].strip())
        expire_year = int(content[3].strip())
        security_code = int(content[4].strip())
        owner_email = content[5].strip()

        # sqlite3 insert credit cards into database
        cur.execute("INSERT INTO Credit_Cards (credit_card_num, card_type, expire_month, expire_year, security_code, owner_email) VALUES (?, ?, ?, ?, ?, ?)", (credit_card_num, card_type, expire_month, expire_year, security_code, owner_email))

    # ensure commit and close
    f.close()
    connect.commit()
    connect.close()


# Import categories dataset
# Handle parent, child category hierarchy
def import_categories():
    connect = get_connection()
    cur = connect.cursor()

    #collect parent child relationships
    rows = []

    # open dataset, read, get data
    f = open("Categories.csv", "r", encoding="utf-8-sig")
    # skip header
    next(f)  
    for row in f:
        #clean each row
        row = row.strip()
        content = row.split(",")

        # Not all categories have parent, blank entry handling
        parent = None
        if content[0].strip() != "":
            parent = content[0].strip()
        child = content[1].strip()

        rows.append((parent, child))

    # get parent child realtionships
    all_categories = set()
    for parent, child in rows:
        all_categories.add(child)
        if parent:
            all_categories.add(parent)

    for category_name in sorted(all_categories):
        # sqlite3 insert categories into database
        cur.execute("INSERT OR IGNORE INTO Categories (category_name, parent_category) VALUES (?, NULL)", (category_name,))

    for parent, child in rows:
        # sqlite3 update category parent relationships
        cur.execute("UPDATE Categories SET parent_category = ? WHERE category_name = ?", (parent, child))

    # ensure commit and close
    f.close()
    connect.commit()
    connect.close()


# Import auction listings dataset
def import_auction_listings():
    connect = get_connection()
    cur = connect.cursor()

    # open dataset, read, get data
    f = open("Auction_Listings.csv", "r", encoding="utf-8-sig")
    # numbers have comma :( alernate logic
    i = csv.reader(f)
    # skip header
    next(i)  
    for row in i:
        #clean each row
        seller_email = row[0].strip()
        listing_id = int(row[1].strip())
        category = row[2].strip()
        auction_title = row[3].strip()
        product_name = row[4].strip()
        product_description = row[5].strip()
        quantity = int(row[6].strip())
        reserve_price_text = row[7].strip()
        reserve_price_text = reserve_price_text.replace("$", "")
        reserve_price_text = reserve_price_text.replace(",", "")
        reserve_price = float(reserve_price_text)
        max_bids = int(row[8].strip())
        status = int(row[9].strip())

        # sqlite3 insert auction listings into database
        cur.execute("INSERT INTO Auction_Listings (seller_email, listing_id, category, auction_title, product_name, product_description, quantity, reserve_price, max_bids, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (seller_email, listing_id, category, auction_title, product_name, product_description, quantity, reserve_price, max_bids, status))

    # ensure commit and close
    f.close()
    connect.commit()
    connect.close()


# Import bids dataset
def import_bids():
    connect = get_connection()
    cur = connect.cursor()

    # open dataset, read, get data
    f = open("Bids.csv", "r", encoding="utf-8-sig")
    # skip header
    next(f)  
    for row in f:
        #clean each row
        row = row.strip()
        content = row.split(",")

        bid_id = int(content[0].strip())
        seller_email = content[1].strip()
        listing_id = int(content[2].strip())
        bidder_email = content[3].strip()
        bid_price = float(content[4].strip())

        # sqlite3 insert bids into database
        cur.execute("INSERT INTO Bids (bid_id, seller_email, listing_id, bidder_email, bid_price) VALUES (?, ?, ?, ?, ?)", (bid_id, seller_email, listing_id, bidder_email, bid_price))

    # ensure commit and close
    f.close()
    connect.commit()
    connect.close()


# Import transactions dataset
def import_transactions():
    connect = get_connection()
    cur = connect.cursor()

    # open dataset, read, get data
    f = open("Transactions.csv", "r", encoding="utf-8-sig")
    # skip header
    next(f)  
    for row in f:
        #clean each row
        row = row.strip()
        content = row.split(",")

        transaction_id = int(content[0].strip())
        seller_email = content[1].strip()
        listing_id = int(content[2].strip())
        bidder_email = content[3].strip()
        date = content[4].strip()
        payment = float(content[5].strip())

        # sqlite3 insert transactions into database
        cur.execute("INSERT INTO Transactions (transaction_id, seller_email, listing_id, bidder_email, date, payment) VALUES (?, ?, ?, ?, ?, ?)", (transaction_id, seller_email, listing_id, bidder_email, date, payment))

    # ensure commit and close
    f.close()
    connect.commit()
    connect.close()


# Import ratings dataset
def import_ratings():
    connect = get_connection()
    cur = connect.cursor()

    # open dataset, read, get data
    f = open("Ratings.csv", "r", encoding="utf-8-sig")
    # skip header
    next(f)
    for row in f:
        # clean each row
        row = row.strip()
        content = row.split(",")

        bidder_email = content[0].strip()
        seller_email = content[1].strip()
        date = content[2].strip()
        rating = int(content[3].strip())
        rating_desc = content[4].strip()

        # sqlite3 insert ratings into database
        cur.execute("INSERT INTO Ratings (bidder_email, seller_email, date, rating, rating_desc) VALUES (?, ?, ?, ?, ?)", (bidder_email, seller_email, date, rating, rating_desc))

    # ensure commit and close
    f.close()
    connect.commit()
    connect.close()


# Import requests dataset
def import_requests():
    connect = get_connection()
    cur = connect.cursor()

    # open dataset, read, get data
    f = open("Requests.csv", "r", encoding="utf-8-sig")
    # skip header
    next(f)

    for row in f:
        # clean each row
        row = row.strip()
        content = row.split(",")

        request_id = int(content[0].strip())
        sender_email = content[1].strip()
        helpdesk_email = content[2].strip()
        request_type = content[3].strip()
        request_desc = content[4].strip()
        request_status = int(content[5].strip())

        # helpdeskteam@lsu.edu does not exist in users, add it to prevent crash
        cur.execute("INSERT OR IGNORE INTO Users (email, password) VALUES (?, ?)", (helpdesk_email, hash_password("temporary")))
        # sqlite3 insert requests into database
        cur.execute("INSERT INTO Requests (request_id, sender_email, helpdesk_staff_email, request_type, request_desc, request_status) VALUES (?, ?, ?, ?, ?, ?)", (request_id, sender_email, helpdesk_email, request_type, request_desc, request_status))

    # ensure commit and close
    f.close()
    connect.commit()
    connect.close()


# !!! End data import functions!!!

# Display table contents
def print_table_counts():
    connect = get_connection()
    cur = connect.cursor()

    tables = [
        "Users", "Helpdesk", "Zipcode_Info", "Address", "Bidders", "Sellers",
        "Local_Vendors", "Credit_Cards", "Categories", "Requests",
        "Auction_Listings", "Bids", "Transactions", "Ratings"
    ]

    # SQL query get counts
    print("\nRow counts:")
    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"{table}: {count}")

    connect.close()


# Password hashing check
def show_users(limit=5):
    connect = get_connection()
    cur = connect.cursor()

    # SQL query to get user data
    cur.execute("SELECT email, password FROM Users LIMIT ?", (limit,))
    rows = cur.fetchall()

    # print user rows to see hashed passwords
    for row in rows:
        print(row)

    connect.close()


def main():
    create_tables()

    import_users()
    import_helpdesk()
    import_zipcode_info()
    import_address()
    import_bidders()
    import_sellers()
    import_local_vendors()
    import_credit_cards()
    import_categories()
    import_requests()
    import_auction_listings()
    import_bids()
    import_transactions()
    import_ratings()

    print_table_counts()
    show_users()

if __name__ == "__main__":
    main()
