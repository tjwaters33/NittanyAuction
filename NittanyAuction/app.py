from flask import Flask, jsonify, render_template, request, redirect, url_for
import sqlite3 as sql
import init_database
import uuid

app = Flask(__name__)

host = 'http://127.0.0.1:5000/'

# maps token to (email,type)
sessions = dict()

def getUserEmail(token):
	return sessions[token][0]

def getUserType(token):
	return sessions[token][1]

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/logout', methods=['GET'])
def logout():
	token = request.args.get('token')
	if token in sessions:
		sessions.pop(token)
	return redirect('/')

@app.route('/login', methods=['POST', 'GET'])
def login_endpoint():
	error = None
	if request.method == 'POST':
		result = valid_name(request.form['type'], request.form['email'], request.form['password'])
		if result:
			token = uuid.uuid1().hex
			sessions[token] = (request.form['email'], request.form['type'])
			print(f"NEW SESSION {request.form['email']} {token}")
			return redirect(url_for('home', token=token, type=request.form['type'], email=request.form['email']))
		else:
			error = 'invalid input name'
	return render_template('login.html', error=error)

@app.route('/home', methods=['GET'])
def home():
	token = request.args.get('token')
	if not token in sessions:
		return redirect('/')
	type = getUserType(token)
	email = getUserEmail(token)
	return render_template('home.html', token = token, type=type, email=email)

@app.route('/search_listings', methods=['GET','POST'])
def search_listings():
	if request.method == 'POST':
		searchString = request.form.get('searchString',None)
		print(searchString)
		if searchString==None:
			return jsonify([])
		
		connection = init_database.get_connection()
		# This makes columns named
		connection.row_factory = sql.Row

		cursor = connection.execute(
			"SELECT listing.Seller_Email, listing.Listing_ID, listing.Category, listing.Auction_Title, listing.Product_Name, listing.Product_Description, listing.Quantity, listing.Status, COALESCE(MAX(bid.Bid_Price), 0) as price FROM Auction_Listings listing LEFT JOIN Bids bid ON listing.Listing_ID = bid.Listing_ID WHERE listing.Auction_Title LIKE ? GROUP BY listing.Listing_ID",
			(f"%{searchString}%",)
		)

		results = cursor.fetchall()
		return jsonify([dict(row) for row in results])
	else:
		token = request.args.get('token')
		if not token in sessions:
			return redirect('/')
		return render_template('search_listings.html', token = token, type = getUserType(token), email = getUserEmail(token))

@app.route('/register_bidder', methods=['GET', 'POST'])
def register_bidder_endpoint():
	error = None

	if request.method == 'POST':
		email = request.form['email']
		password = request.form['password']
		first_name = request.form['first_name']
		last_name = request.form['last_name']
		age = request.form['age']
		zipcode = request.form['zipcode']
		city = request.form['city']
		state = request.form['state']
		street_num = request.form['street_num']
		street_name = request.form['street_name']
		major = request.form['major']
		result = valid_register('Bidders', email)
		if result:
			print("Success bidder")
			existing_city, existing_state = get_or_create_zipcode_info(zipcode, city, state)
			if existing_city != city or existing_state != state:
				error = 'Invalid zipcode, city, or state'
				return render_template('register_bidder.html', error=error)
			home_address_id = get_or_create_address(zipcode, street_num, street_name)
			register_bidder(email, password, first_name, last_name, age, home_address_id, major)
			return render_template('login.html', error=error)
		else:
			error = 'Email already registered'
			return render_template('register_bidder.html', error=error)


	return render_template('register_bidder.html', error=error)

@app.route('/register_seller', methods=['GET', 'POST'])
def register_seller_endpoint():
	error = None

	if request.method == 'POST':
		email = request.form['email']
		password = request.form['password']
		bank_routing_number = request.form['bank_routing_number']
		bank_account_number = request.form['bank_account_number']
		balance = request.form['balance']
		result = valid_register('Sellers', email)
		if result:
			print("Success seller")
			register_seller(email, password, bank_routing_number,bank_account_number,balance)
			return render_template('login.html', error=error)
		else:
			error = 'Email already registered'
			return render_template('register_seller.html', error=error)


	return render_template('register_seller.html', error=error)


@app.route('/register_local_vendor', methods=['GET', 'POST'])
def register_local_vendor_endpoint():
	error = None

	if request.method == 'POST':
		email = request.form['email']
		password = request.form['password']
		bank_routing_number = request.form['bank_routing_number']
		bank_account_number = request.form['bank_account_number']
		balance = request.form['balance']
		business_name = request.form['business_name']
		zipcode = request.form['zipcode']
		city = request.form['city']
		state = request.form['state']
		street_num = request.form['street_num']
		street_name = request.form['street_name']
		phone_num = request.form['customer_service_phone_number']
		result = valid_register('Sellers', email)
		if result:
			print("Success seller")
			existing_city, existing_state = get_or_create_zipcode_info(zipcode, city, state)
			if existing_city != city or existing_state != state:
				error = 'Invalid zipcode, city, or state'
				return render_template('register_bidder.html', error=error)
			address_id = get_or_create_address(zipcode, street_num, street_name)
			register_seller(email, password, bank_routing_number,bank_account_number,balance)
			register_local_vendor(email, business_name, address_id, phone_num)
			return render_template('login.html', error=error)
		else:
			error = 'Email already registered'
			return render_template('register_local_vendor.html', error=error)


	return render_template('register_local_vendor.html', error=error)

def valid_register(type, email):
	connection = init_database.get_connection()
	cursor = connection.execute(f'SELECT COUNT(*) FROM users JOIN {type} ON users.email = {type}.email WHERE users.email = ?', (email,))
	count = cursor.fetchall()[0][0]
	print(count)
	if count > 0:
		return False
	return count == 0

def register_bidder(email, password, first_name, last_name, age, home_address_id, major):
	connection = init_database.get_connection()
	connection.execute(
		'INSERT INTO users (email, password) VALUES (?, ?)',
		(email, init_database.hash_password(password))
	)

	connection.execute(
		f'INSERT INTO bidders (email,first_name,last_name,age,home_address_id,major) VALUES (?,?,?,?,?,?)',
		(email, first_name, last_name, age, home_address_id, major)
	)
	connection.commit()

def get_or_create_address(zipcode, street_num, street_name):
	connection = init_database.get_connection()

	cursor = connection.execute(
		'''
		SELECT address_id
		FROM Address
		WHERE zipcode = ? AND street_num = ? AND street_name = ?
		''',
		(zipcode, street_num, street_name)
	)

	row = cursor.fetchone()

	if row:
		address_id = row[0]
		connection.close()
		return address_id

	address_id = uuid.uuid4().hex

	connection.execute(
		'''
		INSERT INTO Address (address_id, zipcode, street_num, street_name)
		VALUES (?, ?, ?, ?)
		''',
		(address_id, zipcode, street_num, street_name)
	)

	connection.commit()
	connection.close()
	return address_id

def get_or_create_zipcode_info(zipcode, city, state):
	connection = init_database.get_connection()
	cursor = connection.execute(
		'''
		SELECT city, state
		FROM zipcode_info
		WHERE zipcode = ?
		''',
		(zipcode,)
	)

	row = cursor.fetchone()

	# zipcode exists already
	if row:
		existing_city, existing_state = row
		return existing_city, existing_state

	connection.execute(
		'''
		INSERT INTO zipcode_info (zipcode, city, state)
		VALUES (?, ?, ?)
		''',
		(zipcode, city, state)
	)
	connection.commit()
	return city, state

def register_seller(email, password, bank_routing_number, bank_account_number, balance):
	connection = init_database.get_connection()
	connection.execute(
		'INSERT INTO users (email, password) VALUES (?, ?)',
		(email, init_database.hash_password(password))
	)


	connection.execute(
		f'INSERT INTO sellers (email, bank_routing_number, bank_account_number, balance) VALUES (?,?,?,?)',
		(email, bank_routing_number, bank_account_number, balance)
	)
	connection.commit()

def register_local_vendor(email, business_name, address_id, phone_num):
	connection = init_database.get_connection()
	connection.execute(
		f'INSERT INTO local_vendors (email, business_name, business_address_id, customer_service_phone_number) VALUES (?,?,?,?)',
		(email, business_name, address_id, phone_num)
	)
	connection.commit()

def valid_name(type, email, password):
	connection = init_database.get_connection()
	cursor = connection.execute(f'SELECT COUNT(*) FROM users JOIN {type} ON users.email = {type}.email WHERE users.email = ? and password = ?', (email, init_database.hash_password(password)))
	count = cursor.fetchall()[0][0] 
	print(count)
	if count > 1:
		raise 'duplicate entry in user database'
	return count == 1


@app.route('/get_subcategories', methods=['POST'])
def get_subcategories():

	key = 'Root'

	if request.method == 'POST':
		key = request.form.get('super_category', 'Root')

	connection = init_database.get_connection()

	cursor = connection.execute(
		'SELECT category_name FROM Categories WHERE parent_category = ?',
		(key,)
	)

	results = cursor.fetchall()

	return jsonify([row[0] for row in results])

@app.route('/get_listings', methods=['POST'])
def get_listings():

	cat = request.form.get('category',None)

	if cat==None:
		return jsonify([])
	
	connection = init_database.get_connection()
	# This makes columns named
	connection.row_factory = sql.Row

	cursor = connection.execute(
		""" SELECT listing.Seller_Email, listing.Listing_ID, listing.Category, listing.Auction_Title, listing.Product_Name, listing.Product_Description, listing.Quantity, listing.Status, COALESCE(MAX(bid.Bid_Price), 0) as price FROM (SELECT listing.*, 
    		vendor.Business_Name AS vendor_name
			FROM Auction_Listings listing
			LEFT JOIN Local_Vendors vendor ON listing.Seller_Email = vendor.Email
			WHERE listing.Category = ?) as listing LEFT JOIN Bids bid ON listing.Listing_ID = bid.Listing_ID GROUP BY listing.Listing_ID
		""",
		(cat,)
	)

	results = cursor.fetchall()
	return jsonify([dict(row) for row in results])

@app.route('/sellitem', methods=['GET', 'POST'])
def sellitem():
	error = None
	success = None

	token = request.args.get('token')
	if not token in sessions:
		return redirect('/')
	connection = init_database.get_connection()

	# get categories (same pattern as other queries)
	cursor = connection.execute(
		'SELECT category_name FROM Categories ORDER BY category_name'
	)
	categories = [row[0] for row in cursor.fetchall()]

	if request.method == 'POST':
		print("MAKING LISTING")
		seller_email = request.form.get('seller_email', None)
		category = request.form.get('category', None)
		auction_title = request.form.get('auction_title', None)
		product_name = request.form.get('product_name', None)
		product_description = request.form.get('product_description', None)
		quantity = request.form.get('quantity', None)
		reserve_price = request.form.get('reserve_price', None)
		max_bids = request.form.get('max_bids', None)

		# basic validation (same style as other endpoints)
		if None in [seller_email, category, auction_title, product_name, product_description, quantity, reserve_price, max_bids]:
			error = "Missing required fields"
		else:
			# check seller exists
			cursor = connection.execute(
				'SELECT COUNT(*) FROM Sellers WHERE email = ?',
				(seller_email,)
			)
			if cursor.fetchone()[0] != 1:
				error = "Seller email not found"
			else:
				# get next listing_id
				cursor = connection.execute(
					'''
					SELECT COALESCE(MAX(listing_id), 0) + 1
					FROM Auction_Listings
					WHERE seller_email = ?
					''',
					(seller_email,)
				)
				next_listing_id = cursor.fetchone()[0]

				# insert listing
				connection.execute(
					'''
					INSERT INTO Auction_Listings
					(seller_email, listing_id, category, auction_title, product_name,
						product_description, quantity, reserve_price, max_bids, status)
					VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
					''',
					(
						seller_email,
						next_listing_id,
						category,
						auction_title,
						product_name,
						product_description,
						int(quantity),
						float(reserve_price),
						int(max_bids),
						1
					)
				)

				connection.commit()
				success = "Listing created successfully"

	connection.close()
	return render_template('sellitem.html', token = token, type = getUserType(token), email = getUserEmail(token), categories=categories, error=error, success=success)

@app.route('/cancel_listing', methods=['POST'])
def cancel_listing():
	listing_id = request.args.get('listing_id', None)
	token = request.args.get('token')
	if not token in sessions:
		return redirect('/')
	seller_email = getUserEmail(token)
	error = None
	success = None
	if seller_email is not None and listing_id is not None:
		listing_info = getListingInfo(listing_id)
		if listing_info[0]!=seller_email:
			error = "Unauthorized"
		elif listing_info[9]==2:
			error = "Can't cancel sold auctions"
		else:
			connection = init_database.get_connection()

			connection.execute(
				'''
				UPDATE Auction_Listings
				SET status = 0
				WHERE seller_email = ? AND listing_id = ?
				''',
				(seller_email, int(listing_id))
			)

			connection.commit()
			connection.close()
			success = "Canceled Listing Succesfully"
	else:
		error = "Invalid Parameters"
	return redirect(url_for('my_listings', token = token, error=error, success=success))

@app.route('/edit_listing', methods=['GET', 'POST'])
def edit_listing():
	error = None
	success = None

	token = request.args.get('token')

	if not token in sessions:
		return redirect('/')
	
	seller_email = getUserEmail(token)
	listing_id = request.args.get('listing_id', None)

	connection = init_database.get_connection()

	cursor = connection.execute(
		'SELECT category_name FROM Categories ORDER BY category_name'
	)
	categories = [row[0] for row in cursor.fetchall()]

	if request.method == 'POST':
		listing_id = request.form.get('listing_id', None)
		category = request.form.get('category', None)
		auction_title = request.form.get('auction_title', None)
		product_name = request.form.get('product_name', None)
		product_description = request.form.get('product_description', None)
		quantity = request.form.get('quantity', None)
		reserve_price = request.form.get('reserve_price', None)
		max_bids = request.form.get('max_bids', None)

		if None in [seller_email, listing_id, category, auction_title, product_name, product_description, quantity, reserve_price, max_bids]:
			error = "Missing required fields"
		else:
			listing_info = getListingInfo(listing_id)
			if listing_info[9]==2:
				error = "Can't edit sold items"
			elif int(max_bids)<listing_info[8]:
				error = "Can't reduce max number of bids"
			else:
				connection.execute(
					'''
					UPDATE Auction_Listings
					SET category = ?, auction_title = ?, product_name = ?, product_description = ?,
						quantity = ?, reserve_price = ?, max_bids = ?
					WHERE seller_email = ? AND listing_id = ?
					''',
					(
						category,
						auction_title,
						product_name,
						product_description,
						int(quantity),
						float(reserve_price),
						int(max_bids),
						seller_email,
						int(listing_id)
					)
				)

				connection.commit()
				success = "Listing updated successfully"

	cursor = connection.execute(
		'''
		SELECT seller_email, listing_id, category, auction_title, product_name,
				product_description, quantity, reserve_price, max_bids, status
		FROM Auction_Listings
		WHERE seller_email = ? AND listing_id = ?
		''',
		(seller_email, int(listing_id))
	)

	listing = cursor.fetchone()
	connection.close()

	return render_template('edit_listing.html', token = token, type = getUserType(token), email = getUserEmail(token), categories=categories, listing=listing, error=error, success=success)

@app.route('/my_listings', methods=['GET'])
def my_listings():
	token = request.args.get('token')
	if not token in sessions:
		return redirect('/')
	connection = init_database.get_connection()
	# This makes columns named
	connection.row_factory = sql.Row

	cursor = connection.execute(
		"SELECT listing.Seller_Email, listing.Listing_ID, listing.Category, listing.Auction_Title, listing.Product_Name, listing.Product_Description, listing.Quantity, listing.Status, COALESCE(MAX(bid.Bid_Price), 0) as price FROM Auction_Listings listing LEFT JOIN Bids bid ON listing.Listing_ID = bid.Listing_ID WHERE listing.Seller_Email = ? GROUP BY listing.Listing_ID",
		(getUserEmail(token),)
	)

	results = cursor.fetchall()
	
	connection.close()
	return render_template('my_listings.html', token = token, type = getUserType(token), email = getUserEmail(token), listings = [dict(row) for row in results], error = request.args.get('error',None), success = request.args.get('success',None))

def getListingBidInfo(listing_id):
	connection = init_database.get_connection()
	cursor = connection.execute(
		"""
		SELECT * FROM Bids WHERE Listing_ID = ?
		""",
		(listing_id, )
	)

	return cursor.fetchall()

def getListingInfo(listing_id):
	connection = init_database.get_connection()
	cursor = connection.execute(
		'''
		SELECT *
		FROM Auction_Listings
		WHERE listing_id = ?
		''',
		(int(listing_id), )
	)

	return cursor.fetchone()

@app.route('/view_listing', methods=['GET'])
def view_listing():
	token = request.args.get('token')
	if not token in sessions:
		return redirect('/')
	listing_id = request.args.get('listing_id', None)

	listing = getListingInfo(listing_id)
	bids = getListingBidInfo(listing_id)
	listing_list = list(listing)
	listing_list[7] = max([bid[4] for bid in bids], default=0)
	listing = tuple(listing_list)
	isowner = getUserEmail(token) == listing[0]
	return render_template('view_listing.html', token = token, type = getUserType(token), email = getUserEmail(token), listing=listing, isowner = isowner, bids = bids, error = request.args.get('error',None), success = request.args.get('success',None))

@app.route('/submit_bid', methods=['POST'])
def submit_bid():
	token = request.args.get('token')
	if not token in sessions:
		return redirect('/')
	listing_id = request.args.get('listing_id', None)
	price = request.form.get('price',None)
	if not price.isdecimal():
		return redirect(url_for('view_listing', listing_id=listing_id, token=token, error='Missing Fields'))
	price=int(price)
	
	listing = getListingInfo(listing_id)

	if listing[9]==0:
		return redirect(url_for('view_listing', listing_id=listing_id, token=token, error='Listing Inactive'))
	if listing[9]==2:
		return redirect(url_for('view_listing', listing_id=listing_id, token=token, error='Listing Closed'))

	bid_info = getListingBidInfo(listing_id)

	if len(bid_info)>=listing[8]:
		return redirect(url_for('view_listing', listing_id=listing_id, token=token, error='Too many bids'))
	
	price_to_beat = max([bid[4] for bid in bid_info], default=0)
	if getUserEmail(token) in [bid[3] for bid in bid_info]:
		return redirect(url_for('view_listing', listing_id=listing_id, token=token, error='You already placed a bid'))
	if price<=price_to_beat:
		return redirect(url_for('view_listing', listing_id=listing_id, token=token, error='Bid must be higher than current top bid'))

	connection = init_database.get_connection()
	cursor = connection.execute('SELECT COALESCE(MAX(Bid_ID), 0) + 1 FROM Bids')
	next_bid_id = cursor.fetchone()[0]
	connection.execute(
		'''
		INSERT INTO Bids
		(Bid_ID, Seller_Email, Listing_ID, Bidder_Email, Bid_Price)
		VALUES (?, ?, ?, ?, ?)
		''',
		(
			next_bid_id,
			listing[0],
			listing[1],
			getUserEmail(token),
			price
		)
	)

	if len(bid_info)+1==listing[8]:
		if price>listing[7]:
			connection.execute(
				'''
				UPDATE Auction_Listings
				SET status = 2
				WHERE Listing_ID = ?
				''',
				(listing_id, )
			)
		else:
			connection.execute(
				'''
				UPDATE Auction_Listings
				SET status = 0
				WHERE Listing_ID = ?
				''',
				(listing_id, )
			)

	connection.commit()
	connection.close()

	return redirect(url_for('view_listing', listing_id=listing_id, token=token, success='Placed Bid Successfully'))

@app.route('/my_bids', methods=['GET'])
def my_bids():
	token = request.args.get('token')
	if not token in sessions:
		return redirect('/')
	connection = init_database.get_connection()
	cursor = connection.execute(
		"""
		SELECT bid.Seller_Email,bid.Bid_Price,listing.listing_id,listing.Auction_Title FROM Bids bid, Auction_Listings listing WHERE bid.bidder_email = ? AND bid.listing_id = listing.listing_id
		""",
		(getUserEmail(token), )
	)
	bids = cursor.fetchall()
	return render_template('my_bids.html', token = token, type = getUserType(token), email = getUserEmail(token), bids = bids)

@app.route('/account', methods=['GET'])
def account():
	token = request.args.get('token')
	if not token in sessions:
		return redirect('/')
	connection = init_database.get_connection()

	account_info = []
	is_vendor = False
	vendor_info = []
	address_info = []
	zipcode_info = []
	type = getUserType(token)
	email = getUserEmail(token)
	if type == "Bidders":
		cursor = connection.execute(
			'''
			SELECT *
			FROM Bidders
			WHERE email = ?
			''',
			(email, )
		)
		account_info = cursor.fetchone()
		cursor = connection.execute(
			'''
            SELECT *
            FROM Address
            WHERE address_id = ?
            ''',
			(account_info[4], )
		)
		address_info = cursor.fetchone()
		print(" Address info:")
		print(address_info)

		cursor = connection.execute(
			'''
            SELECT *
            FROM Zipcode_info
            WHERE zipcode = ?
            ''',
			(address_info[1],)
		)
		zipcode_info = cursor.fetchone()
		print(" Zipcode info:")
		print (zipcode_info)

	elif type == "Sellers":
		cursor = connection.execute(
			'''
			SELECT *
			FROM Sellers
			WHERE email = ?
			''',
			(email, )
		)
		account_info = cursor.fetchone()

		cursor = connection.execute(
			'''
			SELECT *
			FROM Local_Vendors
			WHERE email = ?
			''',
			(email, )
		)
		vendor_info = cursor.fetchone()
		if vendor_info:
			is_vendor = True
			cursor = connection.execute(
				'''
                SELECT *
                FROM Address
                WHERE address_id = ?
                ''',
				(vendor_info[2],)
			)
			address_info = cursor.fetchone()
			print(" Address info:")
			print(address_info)

			cursor = connection.execute(
				'''
                SELECT *
                FROM Zipcode_info
                WHERE zipcode = ?
                ''',
				(address_info[1],)
			)
			zipcode_info = cursor.fetchone()
			print(" Zipcode info:")
			print(zipcode_info)
	elif type == "Helpdesk":
		cursor = connection.execute(
			'''
			SELECT *
			FROM Helpdesk
			WHERE email = ?
			''',
			(email, )
		)
		account_info = cursor.fetchone()
	connection.close()
	return render_template('account.html', token = token, type = type, email = email, account_info = account_info, is_vendor = is_vendor, vendor_info = vendor_info, address_info = address_info, zipcode_info = zipcode_info)

@app.route('/account_update', methods=['POST'])
def update_account():
	token = request.args.get('token')
	if not token in sessions:
		return redirect('/')
	connection = init_database.get_connection()
	type = getUserType(token)
	email = getUserEmail(token)
	error = None

	cursor = connection.execute(
		'''
        SELECT *
        FROM Local_Vendors
        WHERE email = ?
        ''',
		(email,)
	)
	vendor_info = cursor.fetchone()

	if vendor_info:
		bank_routing_number = request.form['bank_routing_number']
		bank_account_number = request.form['bank_account_number']
		business_name = request.form['business_name']
		street_num = request.form['street_num']
		street_name = request.form['street_name']
		city = request.form['city']
		state = request.form['state']
		zipcode = request.form['zipcode']
		balance = request.form['balance']
		customer_service_phone_number = request.form['customer_service_phone_number']

		new_city, new_state = get_or_create_zipcode_info(zipcode, city, state)
		if new_city != city or new_state != state:
			error = 'Invalid zipcode, city, or state. City and state automatically corrected to zipcode.'
			city = new_city
			state = new_state

		address_id = get_or_create_address(zipcode, street_num, street_name)

		connection.execute(
			'''
            UPDATE sellers
            SET bank_routing_number = ?, bank_account_number = ?
            WHERE email = ?
            ''',
			(bank_routing_number, bank_account_number, email)
		)

		connection.execute(
			'''
            UPDATE local_vendors
            SET business_name = ?, business_address_id = ?, customer_service_phone_number = ?
            WHERE email = ?
            ''',
			(business_name, address_id, customer_service_phone_number, email)
		)

		account_info = [email, bank_routing_number, bank_account_number, balance]
		is_vendor = True
		vendor_info = [email, business_name, address_id, customer_service_phone_number]
		address_info = [address_id, zipcode, street_num, street_name]
		zipcode_info = [zipcode, city, state]
		password = request.form['password']
		if password.strip() != '':
			connection.execute(
				'''
                UPDATE users
                SET password = ?
                WHERE email = ?
                ''',
				(init_database.hash_password(password), email)
			)

		connection.commit()
		return render_template('account.html', token=token, type=type, email=email, account_info=account_info,
							   is_vendor=is_vendor, vendor_info=vendor_info, address_info=address_info,
							   zipcode_info=zipcode_info, success='Account updated', error=error)


	elif type == "Sellers":
		bank_routing_number = request.form['bank_routing_number']
		bank_account_number = request.form['bank_account_number']
		balance = request.form['balance']
		connection.execute(
			'''
            UPDATE sellers
            SET bank_routing_number = ?, bank_account_number = ?
            WHERE email = ?
            ''',
			(bank_routing_number, bank_account_number, email)
		)
		account_info = [email, bank_routing_number, bank_account_number, balance]
		is_vendor = False
		vendor_info = []
		address_info = []
		zipcode_info = []
		password = request.form['password']
		if password.strip() != '':
			connection.execute(
				'''
                UPDATE users
                SET password = ?
                WHERE email = ?
                ''',
				(init_database.hash_password(password), email)
			)

		connection.commit()
		return render_template('account.html', token=token, type=type, email=email, account_info=account_info,
							   is_vendor=is_vendor, vendor_info=vendor_info, address_info=address_info,
							   zipcode_info=zipcode_info, success='Account updated', error=error)

	elif type == "Bidders":
		first_name = request.form['first_name']
		last_name = request.form['last_name']
		age = request.form['age']
		street_num = request.form['street_num']
		street_name = request.form['street_name']
		city = request.form['city']
		state = request.form['state']
		zipcode = request.form['zipcode']
		major = request.form['major']

		new_city, new_state = get_or_create_zipcode_info(zipcode, city, state)
		if new_city!=city or new_state!=state:
			error = 'Invalid zipcode, city, or state. City and state automatically corrected to zipcode.'
			city = new_city
			state = new_state

		address_id = get_or_create_address(zipcode, street_num, street_name)


		connection.execute(
			'''
            UPDATE bidders
            SET first_name = ?, last_name = ?, age = ?, home_address_id = ?, major = ?
            WHERE email = ?
            ''',
			(first_name, last_name, age, address_id, major, email)
		)

		account_info = [email,first_name,last_name,age,address_id,major]
		is_vendor = False
		vendor_info = []
		address_info = [address_id, zipcode, street_num, street_name]
		zipcode_info = [zipcode, city, state]
		password = request.form['password']
		if password.strip() != '':
			connection.execute(
				'''
				UPDATE users
				SET password = ?
				WHERE email = ?
				''',
				(init_database.hash_password(password), email)
			)

		connection.commit()
		return render_template('account.html', token=token, type=type, email=email, account_info=account_info,
							   is_vendor=is_vendor, vendor_info=vendor_info, address_info=address_info,
							   zipcode_info=zipcode_info, success='Account updated', error = error)
	elif type == "Helpdesk":
		role = request.form['role']
		connection.execute(
			'''
            UPDATE helpdesk
            SET role = ?
            WHERE email = ?
            ''',
			(role, email)
		)

		account_info = [email, role]
		is_vendor = False
		vendor_info = []
		address_info = []
		zipcode_info = []
		password = request.form['password']
		if password.strip() != '':
			connection.execute(
				'''
                UPDATE users
                SET password = ?
                WHERE email = ?
                ''',
				(init_database.hash_password(password), email)
			)

		connection.commit()
		return render_template('account.html', token=token, type=type, email=email, account_info=account_info,
							   is_vendor=is_vendor, vendor_info=vendor_info, address_info=address_info,
							   zipcode_info=zipcode_info, success='Account updated', error=error)

@app.route('/request_subcategory', methods=['POST'])
def request_subcategory():
	parent_category = request.form.get('parent_category', None)
	requested_category = request.form.get('requested_category', None)

	token = request.args.get('token')
	if not token in sessions:
		return redirect('/')
	
	email = getUserEmail(token)
	
	if None not in [email, parent_category, requested_category]:
		connection = init_database.get_connection()

		cursor = connection.execute('SELECT COALESCE(MAX(request_id), 0) + 1 FROM Requests')
		next_request_id = cursor.fetchone()[0]

		request_desc = f"Seller {email} requested new subcategory '{requested_category}' under '{parent_category}'."

		connection.execute(
			'''
			INSERT INTO Requests
			(request_id, sender_email, helpdesk_staff_email, request_type, request_desc, request_status)
			VALUES (?, ?, ?, ?, ?, ?)
			''',
			(
				next_request_id,
				email,
				'helpdeskteam@lsu.edu',
				'AddCategory',
				request_desc,
				0
			)
		)

		connection.commit()
		connection.close()

	return redirect(url_for('sellitem', token = token, request_success=1))

if __name__ == "__main__":
	app.run()