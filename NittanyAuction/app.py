from flask import Flask, render_template, request
import sqlite3 as sql
import init_database

app = Flask(__name__)

host = 'http://127.0.0.1:5000/'


@app.route('/')
def index():
	return render_template('index.html')


@app.route('/login', methods=['POST', 'GET'])
def login_endpoint():

	print('testing')
	error = None
	if request.method == 'POST':
		print(request.form)
		result = valid_name(request.form['type'], request.form['email'], request.form['password'])
		if result:
			return render_template(f'auction_house/AH_{request.form['type']}.html', error=error, result=result)
		else:
			error = 'invalid input name'

			
	return render_template('input.html', error=error)


def valid_name(type, email, password):
	connection = init_database.get_connection()
	cursor = connection.execute(f'SELECT COUNT(*) FROM users JOIN {type} ON users.email = {type}.email WHERE users.email = ? and password = ?', (email, init_database.hash_password(password)))
	count = cursor.fetchall()[0][0] 
	print(count)
	if count > 1:
		raise 'duplicate entry in user database'
	return count == 1



if __name__ == "__main__":
	app.run()


