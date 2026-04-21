from flask import Flask, jsonify, render_template, request, redirect, url_for
import sqlite3 as sql
import init_database

app = Flask(__name__)

host = 'http://127.0.0.1:5000/'

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/login', methods=['POST', 'GET'])
def login_endpoint():

	error = None
	if request.method == 'POST':
		result = valid_name(request.form['type'], request.form['email'], request.form['password'])
		if result:
			return redirect(url_for('home', type=request.form['type']))
		else:
			error = 'invalid input name'
	return render_template('login.html', error=error)

@app.route('/home', methods=['GET'])
def home():
	return render_template('home.html', type = request.args.get('type'))

@app.route('/search_listings', methods=['GET','POST'])
def search_listings():
	if request.method == 'POST':
		searchString = request.form.get('searchString',None)

		if searchString==None:
			return jsonify([])
		
		connection = init_database.get_connection()
		# This makes columns named
		connection.row_factory = sql.Row

		cursor = connection.execute(
			"SELECT * FROM Auction_Listings WHERE Auction_Title LIKE ?",
			(f"%{searchString}%",)
		)

		results = cursor.fetchall()
		return jsonify([dict(row) for row in results])
	else:
		return render_template('search_listings.html', type = request.args.get('type'))

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
			return render_template('input.html', error=error)
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
			return render_template('input.html', error=error)
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
			return render_template('input.html', error=error)
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
		"""SELECT listing.*, 
    		vendor.Business_Name AS vendor_name
			FROM Auction_Listings listing
			LEFT JOIN Local_Vendors vendor ON listing.Seller_Email = vendor.Email
			WHERE listing.Category = ?
		""",
		(cat,)
	)

	results = cursor.fetchall()
	return jsonify([dict(row) for row in results])

if __name__ == "__main__":
	app.run()