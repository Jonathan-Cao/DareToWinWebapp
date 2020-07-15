# DareToWin Webapp

Connecting daredoers everywhere

## Introduction

The <a href='http://daretowinweb.herokuapp.com/'>DareToWin Webapp</a> acts as a companion social media app to the Telegram Bot game <a href=https://github.com/VisnuRavi/DareToWinSubmit>DareToWin</a> (@daretowinbot)<br>
With this webapp, registered users are able to:
* upload videos of their dares (supports mp4 and webm files)
* upvote other users' dares and gain upvotes for their own
* earn badges based on the total number of upvotes they have
* comment on other users' dares
* follow other users so that their dares show up on their main feed
* report inappropriate dares and comments,<br>
  after which an admin will review said content and decide whether to ban it,<br>
  doing so will cause the offending user to get a demerit

## Video Demo
<a href="http://www.youtube.com/watch?feature=player_embedded&v=FbWiYg62btQ
" target="_blank"><img src="http://img.youtube.com/vi/FbWiYg62btQ/0.jpg" 
alt="IMAGE ALT TEXT HERE" width="480" height="360" border="0" /></a>

## Access

To access this webapp, click <a href='https://daretowinweb.herokuapp.com/' target='_blank'>here</a>

## Setup

To test this webapp on your own machine:

1. In your terminal, navigate to the root directory of the webapp and enter:<br>
    For Python 3:<br>
    ```
    $ sudo apt-get install python3-venv
    $ python3 -m venv venv
    ```
    Alternatively, if the above does not work, enter:<br>
    ```
    $ sudo apt install virtualenv
    $ virtualenv venv
    ```
   This creates the virtual environment folder named venv.<br>

2. Enter the virtual environment by entering<br>
    `$ source venv/bin/activate`<br>
    
3. To install the requirements in the current environment, enter:<br>
    `$ pip3 install -r requirements.txt`<br>
    
    Alternatively, if the above does not work, enter:<br>
    `$ pip install -r requirements.txt`<br>
    
4. Enter the following commands to initialise the db database file<br>
    ```
    $ flask db init
    $ flask db migrate -m "initial_migration"
    $ flask db upgrade
    ```
   You should see a new file named app.db in the root directory<br>
   
5. Before starting the webapp, open config.py and<br>
   edit the UPLOAD_FOLDER variable with the path to your directory of choice<br>
   This directory will be used to store uploaded video files.<br>
   The following command can be used to find the full path to your current working directory.<br>
   `$ pwd`<br>

5. To start the webapp, enter:<br>
   `$ flask run`<br>
    
6. Navigate to http://localhost:5000 in your web browser of choice

NOTE: In the current build, the first user to register will have access to admin privileges

## Contributions
This DareToWin webapp was created by <a href='https://github.com/VisnuRavi'>Visnu</a> and <a href='https://github.com/joncao159'>Jonathan</a>.

## Acknowledgements
The code for this webapp is inspired by the <a href="https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world" target="_blank">Flask Tutorial by Miguel Grinberg</a>
