# imports from flask
from datetime import datetime
from urllib.parse import urljoin, urlparse
from flask import abort, redirect, render_template, request, send_from_directory, url_for, jsonify, current_app, g # import render_template from "public" flask libraries
from flask_login import current_user, login_user, logout_user
from flask.cli import AppGroup
from flask_login import current_user, login_required
from flask import current_app
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
from api.jwt_authorize import token_required


# import "objects" from "this" project
from __init__ import app, db, login_manager  # Key Flask objects 
# API endpoints
from api.user import user_api 
from api.python_exec_api import python_exec_api
from api.javascript_exec_api import javascript_exec_api
from api.section import section_api
from api.pfp import pfp_api
from api.stock import stock_api
from api.analytics import analytics_api
from api.student import student_api
from api.groq_api import groq_api
from api.gemini_api import gemini_api
from api.microblog_api import microblog_api
from api.classroom_api import classroom_api
from hacks.joke import joke_api  # Import the joke API blueprint
from hacks.DBS2endpoint import DBS2_api  # Import the Discord Basement Simulator 2 API blueprint
from api.post import post_api  # Import the social media post API
from api.dbs2_api import dbs2_api
from model.dbs2_player import DBS2Player, initDBS2Players
#from api.announcement import announcement_api ##temporary revert

# database Initialization functions
from model.user import User, initUsers
from model.user import Section;
from model.github import GitHubUser
from model.feedback import Feedback
from api.analytics import get_date_range
# from api.grade_api import grade_api
from api.study import study_api
from api.feedback_api import feedback_api
from model.study import Study, initStudies
from model.classroom import Classroom
from model.post import Post, init_posts
from model.microblog import MicroBlog, Topic, init_microblogs
from hacks.jokes import initJokes
from hacks.DBS2data import initDBS2
# from model.announcement import Announcement ##temporary revert

# server only Views

import os
import requests

# Load environment variables
load_dotenv()

app.config['KASM_SERVER'] = os.getenv('KASM_SERVER')
app.config['KASM_API_KEY'] = os.getenv('KASM_API_KEY')
app.config['KASM_API_KEY_SECRET'] = os.getenv('KASM_API_KEY_SECRET')



# register URIs for api endpoints
app.register_blueprint(python_exec_api)
app.register_blueprint(javascript_exec_api)Prerequisites
Before we deploy…

Complete review of frontend to backend server
Have a personalized deployment blog, including Terms and Visuals the deploymnet purpose and process
Have a deployment issues with Deploymnet Admin roles
Prepare configuration files below in your repo
Test Server
Ensure you have a working frontend-to-backend test server. If it does not work locally, there is no need to try it on deployment.

CRUD Demonstration

Subdomain
Setup DNS endpoint through AWS Route 53.

    Server: https://flask.opencodingsociety.com/
    Domain: opencodingsociety.com
    Subdomain: flask
Port (Backend)
Select a unique port for your application. Update all locations

main.py - Prepare the localhost test server port to run on the same port for consistency.

  # this runs the flask application on the development server
  if __name__ == "__main__":
      # change name for testing
      app.run(debug=True, host="0.0.0.0", port="8403")
Dockerfile - Prepare this file to run a server as a virtual machine on the deployment host.

  FROM docker.io/python:3.11

  WORKDIR /

  # --- [Install python and pip] ---
  RUN apt-get update && apt-get upgrade -y && \
      apt-get install -y python3 python3-pip git
  COPY . /

  RUN pip install --no-cache-dir -r requirements.txt
  RUN pip install gunicorn

  ENV GUNICORN_CMD_ARGS="--workers=1 --bind=0.0.0.0:8403"

  EXPOSE 8087

  # Define environment variable
  ENV FLASK_ENV=production

  CMD [ "gunicorn", "main:app" ]
docker-compose.yml - Prepare this file to serve as the “make” for Docker.

      version: '3'
      services:
              web:
                      image: flask
                      build: .
                      env_file:
                              - .env
                      ports:
                              - "8403:8403"
                      volumes:
                              - ./instance:/instance
                      restart: unless-stopped

nginx_file - Prepare this file for reverse proxy from the internet to the application and back to the requester.

  server {
      listen 80;
      listen [::]:80;
      server_name flask.opencodingsociety.com;

      location / {
          proxy_pass http://localhost:8087;

          # Preflighted requests
          if ($request_method = OPTIONS) {
              add_header "Access-Control-Allow-Credentials" "true" always;
              add_header "Access-Control-Allow-Origin"  "https://open-coding-society.github.io" always;
              add_header "Access-Control-Allow-Methods" "GET, POST, PUT, DELETE, OPTIONS, HEAD" always;
              add_header "Access-Control-Allow-MaxAge" 600 always;
              add_header "Access-Control-Allow-Headers" "Authorization, Origin, X-Origin, X-Requested-With, Content-Type, Accept" always;
              return 204;
          }
      }
  }
Port (Frontend)
assets/api/config.js - Prepare the frontend to access your domain and ports to match your localhost, port, and domain settings.

  export var pythonURI;
  if (location.hostname === "localhost" || location.hostname === "127.0.0.1") {
      pythonURI = "http://localhost:8403";  // Same URI for localhost or 127.0.0.1
  } else {
      pythonURI = "https://flask.opencodingsociety.com";
  }
Accessing AWS EC2
Development Operations (DevOps) requires server access.

Amazon Web Services (AWS) Management Console
Login to AWS Console using your account. Navigate to “EC2” and the “Instances” page.
EC2 Screenshot

From here, a variety of instances will show up. For this project, depending on which class you have, select either “CSP” or “CSA”
Unrestricted Gateway to AWS EC2 Terminal
At school access cockpit.stu.opencodingsociety.com or csa.opencodingsociety.com to log in to the deployment server. Observe Cockpit features in section below, but primarily you will be using Terminal in this setup. - Username is ubuntu. Password hint is 3 Musketeers

Application Setup
Finding a Port
In AWS EC2 terminal;

Run docker ps review list and find a port number starting in 8— that is not in use. Valid ports are between 1024-49150, but we are asking that you stick to 8—.
On localhost setup Docker files using VSCode
Open VSCode and navigate to your repository (backend)

Make sure your Dockerfile and docker-compose.yml match the port you discovered with docker ps on AWS EC2. Refer to anatomy guide for you language and framework for a guide to you Docker files.

Test docker-compose up or sudo docker-compose up in your VSCode terminal (don’t forget to ‘cd’ into the right repo.) Errors will be shown in Terminal, be sure NOT to type -d.

After it’s done building, type in http://localhost:8--- in your browser (replace ‘8—’ with your port number you’ve chosen)

If all runs smoothly, push your changes to Github and continue to AWS setup

Server Setup
In the AWS EC2 terminal;

cd ~

Clone your backend repo: git clone github.com/server/project.git my_group_name

Navigate to your repo: cd my_group_name

Build your site: docker-compose up -d --build

Test your site: curl localhost:8--- (replace ‘8—’ with your port number)

This should show you all the html content of your home page. If this provides 500 error you need to check your site on localhost. If it produces broken pipe error you need to check your ports between docker-compose.yml and Docker files. If the page does not have your content, you need to check docker ps as someone is using your port number.

If all runs smooth, continue to DNS & NGINX Setup

Route 53 DNS
Goto AWS Route 53 and setup DNS subdomain for your backend server.

Route 53 Hosted Zone Configuration File:

Route 53

Route 53 DNS Setup:

Record name	Type	Value/Route traffic to
projectUniqueName	CNAME	csp.opencodingsociety.com
projectUniqueName	CNAME	csa.opencodingsociety.com
Nginx setup
Begin process of establishing reverse proxy (map) of your application to your Domain.

Navigate to in terminal to nginx: cd /etc/nginx/sites-available

Create an nginx config file (change projectUniqueName to make you unique config file, suggest using your registered domain): sudo nano projectUniqueName

Use the format below to write into your config file, make updates according to comments

servserver {
        listen 80;
        listen [::]:80;
        server_name flask.opencodingsociety.com;

        location / {
                proxy_pass http://localhost:8403;

                # Preflighted requests
                if ($request_method = OPTIONS) {
                add_header "Access-Control-Allow-Credentials" "true" always;
                add_header "Access-Control-Allow-Origin"  "https://open-coding-society.github.io" always;
                add_header "Access-Control-Allow-Methods" "GET, POST, PUT, DELETE, OPTIONS, HEAD" always;
                add_header "Access-Control-Allow-MaxAge" 600 always;
                add_header "Access-Control-Allow-Headers" "Authorization, Origin, X-Origin, X-Requested-With, Content-Type, Accept" always;
                return 204;
                }
        }
}
To save changes, ctl X or cmd X, then y, then enter

Activate configuration. Create a symbolic link (change projectUniqueName to your nginx config file name): cd /etc/nginx/sites-enabled, then sudo ln -s /etc/nginx/sites-available/projectUniqueName /etc/nginx/sites-enabled

Validate by running: sudo nginx -t

Restart nginx by running sudo systemctl restart nginx

Test your domain name on your desktop browser now (only http://, not https://)

If all runs smoothly, continue to Certbot config

Certbot Config
Certbot allows your site to get a certificate in order for the http request to be secure (https)

Run command below and follow prompts
sudo certbot --nginx
Ideal outcome is shown below

There are two outcomes during Certbot
Success, test your domain name on your desktop browser now using https://
Failure, follow guidance provided by CertBot
Saving debug log to /var/log/letsencrypt/letsencrypt.log
Plugins selected: Authenticator nginx, Installer nginx

Which names would you like to activate HTTPS for?
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
...
28: cars.opencodingsociety.com
29: dolphin.opencodingsociety.com
30: saakd.opencodingsociety.com
...
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
Select the appropriate numbers separated by commas and/or spaces, or leave input
blank to select all options shown (Enter 'c' to cancel): # ENTER YOUR CORRESPONDING NUMBER

Cert not yet due for renewal

You have an existing certificate that has exactly the same domains or certificate name you requested and isn't close to expiry.
(ref: /etc/letsencrypt/renewal/opencodingsociety.com-0001.conf)

What would you like to do?
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
1: Attempt to reinstall this existing certificate
2: Renew & replace the cert (limit ~5 per 7 days)
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
Select the appropriate number [1-2] then [enter] (press 'c' to cancel): 2
Renewing an existing certificate
Performing the following challenges:
http-01 challenge for opencodingsociety.com
http-01 challenge for csa.opencodingsociety.com
http-01 challenge for cso.opencodingsociety.com
http-01 challenge for flm.opencodingsociety.com
Waiting for verification...
Cleaning up challenges
Deploying Certificate to VirtualHost /etc/nginx/sites-enabled/nighthawk_society
Deploying Certificate to VirtualHost /etc/nginx/sites-enabled/nighthawk_csa
Deploying Certificate to VirtualHost /etc/nginx/sites-enabled/nighthawk_csp
Deploying Certificate to VirtualHost /etc/nginx/sites-enabled/nighthawk_flm

Please choose whether or not to redirect HTTP traffic to HTTPS, removing HTTP access.
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
1: No redirect - Make no further changes to the webserver configuration.
2: Redirect - Make all requests redirect to secure HTTPS access. Choose this for
new sites, or if you're confident your site works on HTTPS. You can undo this
change by editing your web server's configuration.
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
Select the appropriate number [1-2] then [enter] (press 'c' to cancel): 2
Traffic on port 80 already redirecting to ssl in /etc/nginx/sites-enabled/nighthawk_society
Traffic on port 80 already redirecting to ssl in /etc/nginx/sites-enabled/nighthawk_csa
Traffic on port 80 already redirecting to ssl in /etc/nginx/sites-enabled/nighthawk_csp
Traffic on port 80 already redirecting to ssl in /etc/nginx/sites-enabled/nighthawk_flm

- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
Your existing certificate has been successfully renewed, and the new certificate
has been installed.

The new certificate covers the following domains:
https://opencodingsociety.com, 
https://csa.opencodingsociety.com, 
https://csp.opencodingsociety.com, and
https://flm.opencodingsociety.com,

You should test your configuration at:
https://www.ssllabs.com/ssltest/analyze.html?d=opencodingsociety.com
https://www.ssllabs.com/ssltest/analyze.html?d=csa.opencodingsociety.com
https://www.ssllabs.com/ssltest/analyze.html?d=csp.opencodingsociety.com
https://www.ssllabs.com/ssltest/analyze.html?d=flm.opencodingsociety.com
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

IMPORTANT NOTES:
 - Congratulations! Your certificate and chain have been saved at:
   /etc/letsencrypt/live/opencodingsociety.com-0001/fullchain.pem
   Your key file has been saved at:
   /etc/letsencrypt/live/opencodingsociety.com-0001/privkey.pem
   Your cert will expire on 2022-03-06. To obtain a new or tweaked
   version of this certificate in the future, simply run certbot again
   with the "certonly" option. To non-interactively renew *all* of
   your certificates, run "certbot renew"
 - If you like Certbot, please consider supporting our work by:

   Donating to ISRG / Let's Encrypt:   https://letsencrypt.org/donate
   Donating to EFF:                    https://eff.org/donate-le
Changing Code will require Deployment Updates
Changing Code in VSCode
To keep deployment working, good practices in your coding process with verifications prior to pushing code to GitHub will save a lot of troubleshooting.

Make sure to git pull before making changes
This will make sure that you pull any changes made by your team, and prevents merge conflicts

Open terminal in VSCode and run python3 main.py (Make sure you cd into your repo)
This should give you a local address where your flask is running. Open this in your browser to see your changes live

Make changes that are needed
Refer to your running site often to see changes as you develop

Commit your changes locally
Do not Sync change from UI or git push from terminal yet, just Commit. It is great practice to Commit Often with sensible comments. Anytime after you commit you can pull team members changes for additional verifications.

Before updating deployment start Docker Desktop app and test your Web Application.
Test docker-compose up or sudo docker-compose up in your VSCode terminal (don’t forget to ‘cd’ into the right repo).

After Docker is done building, type in http://localhost:8--- in your browser.
Replace ‘8—’ with your port number. Review your personal changes and team members changes in running site. As long as Docker Desktop and Docker App is running, you can make little changes and save, they should refresh in site within a few seconds. Any errors, runtime errors, will appear in browser of VSCode terminal, read messages thoroughly and debug errors. Docker Desktop may consume a lot of CPU resources, if you are unplugged you may want to close it after you are done testing.

If all goes well, Sync change from UI or git push from terminal.
If you can’t push review git status from terminal. Resolve all open files git restore or git commit, then git pull and repeat steps 5 to 7.

Pulling Changes into AWS EC2 deployment
Updates should be quick and easy, as long as your teams verifies problems on localhost prior to these steps.

In your AWS EC2 terminal;

Navigate to your repo: cd ~/my_unique_name

docker-compose down
Test Server in browser using https://, it should be down (502 Bad Gateway in browser)

git pull

Rebuild your docker container: docker-compose up -d --build
Test Server in browser using https://, sll updates should be up and running on internet.

Optional, Troubleshooting checks on AWS EC2
These commands let you see status of your running web application on AWS EC2

Try to curl: curl localhost:8--- (replace ‘8—’ with your port number)
Verify home pages is yours

Run docker-compose ps
Perform check on your container, verify docker is up

Run docker ps
Perform checks on all containers and all images

Cockpit Navigation
This portion will cover Cockpit’s features. Login to Cockpit by accessing your subdomain.

The left navigation bar in Cockpit presents a few options that you can select:

Overview
The overview section provides a summary of health, usage, system, and configuration information. Click on “View details and history” to check CPU, memory, and network settings.

Logs
These provide information about the system, such as a failed login. Logs can be filtered based on criteria such as time or priority.

Storage
See disk read and write settings and storage logs.

Networking
This portion shows the network traffic of the server and interface information. VLANs and bridges can also be added here.

Accounts
This setting allows the administrator to create and manage accounts. You can click on a user to edit user settings, such as changing the password and adding SSH keys.

Services
Click on a service to view its settings. A service can be reloaded, restarted, or stopped by clicking on the three dots. The dropdown under “Show relationships” includes information such as a service’s dependencies and when it starts in relation with other services (what services start before and after this service)

Software Updates
If you are running Ubuntu 17.10 or later, a “Loading available updates failed” error message will appear. This is because Ubuntu changed the network management from network-manager to netplan.io, which has not been updated in Cockpit. A way to fix this is to change netplan’s configuration file to manage one interface with network-manager.

sudo nano /etc/netplan/50-cloud-init.yaml
Next, add the following line under network:

renderer: NetworkManager
Then, execute

sudo netplan try
Refresh Cockpit, and the “Software Updates” page should work. Updates can now be installed.

Terminal
A command line interface that is the same as the machine’s terminal on AWS EC2.

Update hostname and system time
Go to Overview -> Configuration -> Click on “edit” next to “Hostname” and configure a hostname for the server.

Click on the time next to “System time” to set the time zone.

User account settings
Go to Accounts -> Click on “Create new account” and fill out the boxes

After the user is created, click on the user. You can check “Server administrator” to give the user sudo privileges.

You can also configure account expiration and password expiration settings by clicking on “edit” next to the two settings.



To test the new user account created, logout, and then login with the new user credentials. If the user has administrative privileges, you can click on the button that says “Limited access” at the top right corner to gain those privileges.

Note: If the user was not configured as a “Server administrator” and tried to gain admin privileges by clicking the button, the attempt will fail and will be logged. You can view the log by clicking on “Logs” in the sidebar:



Congratulations!
Congratulations on deploying your site with AWS!
app.register_blueprint(user_api)
app.register_blueprint(section_api)
app.register_blueprint(pfp_api) 
app.register_blueprint(stock_api)
app.register_blueprint(groq_api)
app.register_blueprint(gemini_api)
app.register_blueprint(microblog_api)

app.register_blueprint(analytics_api)
app.register_blueprint(student_api)
# app.register_blueprint(grade_api)
app.register_blueprint(study_api)
app.register_blueprint(classroom_api)
app.register_blueprint(feedback_api)
app.register_blueprint(joke_api)  # Register the joke API blueprint
app.register_blueprint(DBS2_api)  # Register the Discord Basement Simulator 2 API blueprint
app.register_blueprint(dbs2_api) # dbs2 database API
app.register_blueprint(post_api)  # Register the social media post API
# app.register_blueprint(announcement_api) ##temporary revert

# Jokes file initialization
with app.app_context():
    initJokes()
    initDBS2()
    initDBS2Players()


# Tell Flask-Login the view function name of your login route
login_manager.login_view = "login"

@login_manager.unauthorized_handler
def unauthorized_callback():
    return redirect(url_for('login', next=request.path))

# register URIs for server pages
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.context_processor
def inject_user():
    return dict(current_user=current_user)

# Helper function to check if the URL is safe for redirects
def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    next_page = request.args.get('next', '') or request.form.get('next', '')
    if request.method == 'POST':
        user = User.query.filter_by(_uid=request.form['username']).first()
        if user and user.is_password(request.form['password']):
            login_user(user)
            if not is_safe_url(next_page):
                return abort(400)
            return redirect(next_page or url_for('index'))
        else:
            error = 'Invalid username or password.'
    return render_template("login.html", error=error, next=next_page)

@app.route('/studytracker')  # route for the study tracker page
def studytracker():
    return render_template("studytracker.html")
    
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.errorhandler(404)  # catch for URL not found
def page_not_found(e):
    # note that we set the 404 status explicitly
    return render_template('404.html'), 404

@app.route('/')  # connects default URL to index() function
def index():
    print("Home:", current_user)
    return render_template("index.html")



@app.route('/users/table2')
@login_required
def u2table():
    users = User.query.all()
    return render_template("u2table.html", user_data=users)

@app.route('/dbs2admin')
@login_required
def dbs2_admin():
    return render_template("dbs2admin.html")

@app.route('/sections/')
@login_required
def sections():
    sections = Section.query.all()
    return render_template("sections.html", sections=sections)

# Helper function to extract uploads for a user (ie PFP image)
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
 
@app.route('/users/delete/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        user.delete()
        return jsonify({'message': 'User deleted successfully'}), 200
    return jsonify({'error': 'User not found'}), 404

@app.route('/users/reset_password/<int:user_id>', methods=['POST'])
@login_required
def reset_password(user_id):
    if current_user.role != 'Admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    # Set the new password
    if user.update({"password": app.config['DEFAULT_PASSWORD']}):
        return jsonify({'message': 'Password reset successfully'}), 200
    return jsonify({'error': 'Password reset failed'}), 500

@app.route('/kasm_users')
def kasm_users():
    # Fetch configuration details from environment or app config
    SERVER = current_app.config.get('KASM_SERVER')
    API_KEY = current_app.config.get('KASM_API_KEY')
    API_KEY_SECRET = current_app.config.get('KASM_API_KEY_SECRET')

    # Validate required configurations
    if not SERVER or not API_KEY or not API_KEY_SECRET:
        return render_template('error.html', message='KASM keys are missing'), 400

    try:
        # Prepare API request details
        url = f"{SERVER}/api/public/get_users"
        data = {
            "api_key": API_KEY,
            "api_key_secret": API_KEY_SECRET
        }

        # Perform the POST request
        response = requests.post(url, json=data, timeout=10)  # Added timeout for reliability

        # Validate the API response
        if response.status_code != 200:
            return render_template(
                'error.html', 
                message='Failed to get users', 
                code=response.status_code
            ), response.status_code

        # Parse the users list from the response
        users = response.json().get('users', [])

        # Process `last_session` and handle potential parsing issues
        for user in users:
            last_session = user.get('last_session')
            try:
                user['last_session'] = datetime.fromisoformat(last_session) if last_session else None
            except ValueError:
                user['last_session'] = None  # Fallback for invalid date formats

        # Sort users by `last_session`, treating `None` as the oldest date
        sorted_users = sorted(
            users, 
            key=lambda x: x['last_session'] or datetime.min, 
            reverse=True
        )

        # Render the sorted users in the template
        return render_template('kasm_users.html', users=sorted_users)

    except requests.RequestException as e:
        # Handle connection errors or other request exceptions
        return render_template(
            'error.html', 
            message=f"Error connecting to KASM API: {str(e)}"
        ), 500
        
        
@app.route('/delete_user/<user_id>', methods=['DELETE'])
def delete_user_kasm(user_id):
    if current_user.role != 'Admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    SERVER = current_app.config.get('KASM_SERVER')
    API_KEY = current_app.config.get('KASM_API_KEY')
    API_KEY_SECRET = current_app.config.get('KASM_API_KEY_SECRET')

    if not SERVER or not API_KEY or not API_KEY_SECRET:
        return {'message': 'KASM keys are missing'}, 400

    try:
        # Kasm API to delete a user
        url = f"{SERVER}/api/public/delete_user"
        data = {
            "api_key": API_KEY,
            "api_key_secret": API_KEY_SECRET,
            "target_user": {"user_id": user_id},
            "force": False
        }
        response = requests.post(url, json=data)

        if response.status_code == 200:
            return {'message': 'User deleted successfully'}, 200
        else:
            return {'message': 'Failed to delete user'}, response.status_code

    except requests.RequestException as e:
        return {'message': 'Error connecting to KASM API', 'error': str(e)}, 500


@app.route('/update_user/<string:uid>', methods=['PUT'])
def update_user(uid):
    # Authorization check
    if current_user.role != 'Admin':
        return jsonify({'error': 'Unauthorized'}), 403

    # Get the JSON data from the request
    data = request.get_json()
    print(f"Request Data: {data}")  # Log the incoming data

    # Find the user in the database
    user = User.query.filter_by(_uid=uid).first()
    if user:
        print(f"Found user: {user.uid}")  # Log the found user's UID
        
        # Update the user using the provided data
        user.update(data)  # Assuming `user.update(data)` is a method on your User model
        
        # Save changes to the database
        return jsonify({"message": "User updated successfully."}), 200
    else:
        print("User not found.")  # Log when user is not found
        return jsonify({"message": "User not found."}), 404



    
# Create an AppGroup for custom commands
custom_cli = AppGroup('custom', help='Custom commands')

# Define a command to run the data generation functions
@custom_cli.command('generate_data')
def generate_data():
    initUsers()
    init_microblogs()

# Register the custom command group with the Flask application
app.cli.add_command(custom_cli)
        
# this runs the flask application on the development server
if __name__ == "__main__":
    host = "0.0.0.0"
    port = app.config['FLASK_PORT']
    print(f"** Server running: http://localhost:{port}")  # Pretty link
    app.run(debug=True, host=host, port=port, use_reloader=False)
