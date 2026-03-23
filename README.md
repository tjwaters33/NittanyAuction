Nittany Auction Phase 2

This is the github repository for the implementation of the Nittany Auction Database Project.
Current Functions: Database Population, User Login

init_database.py: 
This file is responsible for initializing the database using the data given in the .csv files found in the repository. 
This is where the tables in which the data will be stored in the database are created and populated.
The relationships between data are also introduced, which are outlined in our Phase 1 Report.
NOTE: User passwords must be stored as hashes and authenticated with hashes. Uses hashlib.sha256 to accomplish.

app.py:
This file handles the backend logic for the database application.
Handles login functionality and logic in valid_name(), ensuring that entered password is hashed before checked with the database.
Handles HTML forms and user inputs, navigating the users to the correct pages.
Establishes connection between Flask and SQLite3 database.

HTML Files:
Found in the Templates folder:
- index.html is the login page, users can input credentials and type of login
- input.html allows user input; email, password, login type, and enter
- reset_password.html currently not implemented

Found in auction_house folder:
- AH_Bidders.html is the main page for bidders, unfinished;
- AH_Sellers.html is the main page for sellers, unfinished;
- AH_Helpdesk.html is the main page for helpdesk, unfinished.

CSV Files:
These are the given datasets used to populate the database.

How To Run:
1) run init_database.py
2) run app.py
3) Copy web address into browser 'http://127.0.0.1:5000/'
Command Prompt:
1) Navigate to directory
2) python init_database.py
3) python app.py
4) Move to browser and paste address 'http://127.0.0.1:5000/'

