# DareToWin Webapp

## Introduction

This webapp acts as a companion social media app to the Telegram Bot game DareToWin (@daretowinbot)<br>
With this webapp, registered users are able to:
* upload videos of their dares (supports mp4 and webm files)
* upvote other users' dares and gain upvotes for their own
* earn badges based on the total number of upvotes they have
* comment on other users' dares
* follow other users so that their dares show up on your main feed
* report inappropriate dares and comments,<br>
  after which an admin will review said content and decide whether to ban it,<br>
  doing so will award the offending user with a demerit

## Setup

To test this webapp on your own machine:

1. In your terminal, navigate to the root directory of the webapp and enter:<br>
    For versions of Python 3.4 and newer:<br>
    `$ python3 -m venv venv`<br>
    Alternatively, for versions of Python older than 3.4 that do not support virtual environments natively:<br>
    ```
    $ sudo pip install virtualenv
    $ virtualenv venv
    ```
   This creates the virtual environment folder named venv.<br>

2. Enter the virtual environment by entering<br>
    `$ source venv/bin/activate`<br>
    
3. To install the requirements in the current environment, enter<br>
    `$ pip install -r requirements.txt`<br>
    
4. Enter the following commands to initialise the db database file<br>
    ```
    $ flask db init
    $ flask db migrate -m "initial_migration"
    $ flask db upgrade
    ```
   You should see a new file named app.db in the root directory<br>
   
5. Before starting the webapp, open config.py and <br>
   edit the UPLOAD_FOLDER variable with the path to your directory of choice<br>
   This directory will be used to store uploaded video files.<br>

5. To start the webapp, enter<br>
   `$ flask run`<br>
    
6. Navigate to http://localhost:5000/index in your web browser of choice

NOTE: In the current build, the first user to register will have access to admin privileges

## Acknowledgements
The code for this webapp is based on the <a href="https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world" target="_blank">Flask Tutorial by Miguel Grinberg</a>
