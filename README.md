# DareToWinWebapp

To install this webapp:

1. In your terminal, navigate to the root directory and enter<br>
    $ python3 -m venv venv<br>
   which creates the virtual environment folder named venv.<br>
<br>
2. Enter the virtual environment by entering<br>
    $ source venv/bin/activate<br>
    
3. To install the requirements in the current environment, enter
    $ pip install -r requirements.txt
    
4. Enter the following commands to initialise the db database file
    $ flask db init
    $ flask db migrate -m "initial_migration"
    $ flask db upgrade
   You should see a new file named app.db in the root directory

5. To start the webapp, enter
    $ flask run
    
6. Navigate to http://localhost:5000/index in your web browser of choice
