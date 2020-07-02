# DareToWinWebapp

To install this webapp:

1. In your terminal, navigate to the root directory and enter:<br>
    For versions of Python 3.4 and newer:<br>
        $ python3 -m venv venv<br>
    For versions of Python older than 3.4 that do not support virtual environments natively:<br>
        $ sudo pip install virtualenv<br>
    $ virtualenv venv<br>
   This creates the virtual environment folder named venv.<br>

2. Enter the virtual environment by entering<br>
    $ source venv/bin/activate<br>
    
3. To install the requirements in the current environment, enter<br>
    $ pip install -r requirements.txt<br>
    
4. Enter the following commands to initialise the db database file<br>
    $ flask db init<br>
    $ flask db migrate -m "initial_migration"<br>
    $ flask db upgrade<br>
   You should see a new file named app.db in the root directory<br>
   
5. Before starting the webapp, open config.py and <br>
   edit the UPLOAD_FOLDER variable with the path to your directory of choice<br>
   This directory will be used to store uploaded video files.<br>

5. To start the webapp, enter<br>
    $ flask run<br>
    
6. Navigate to http://localhost:5000/index in your web browser of choice

NOTE: In the current build, the first user to register will have access to admin privileges
