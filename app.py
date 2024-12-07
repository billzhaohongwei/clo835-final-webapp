import os
from flask import Flask, render_template, request
from pymysql import connections
import random
import argparse
import boto3
from botocore.exceptions import NoCredentialsError

DBHOST = os.environ.get("DBHOST") or "localhost"
DBUSER = os.environ.get("DBUSER") or "root"
DBPWD = os.environ.get("DBPWD") or "password"
DATABASE = os.environ.get("DATABASE") or "employees"
COLOR_FROM_ENV = os.environ.get('APP_COLOR') or "lime"
DBPORT = int(os.environ.get("DBPORT"))
# Specify the background image:
BACKGROUND_IMAGE_URL = os.getenv("BACKGROUND_IMAGE_URL") or "Background image location not passed"

def download_image():
    # Get the S3 URL from the environment variable or a default value
    global BACKGROUND_IMAGE_URL
    
    # Ensure BACKGROUND_IMAGE_URL is a valid URL
    if BACKGROUND_IMAGE_URL == "Background image location not passed":
        print("No background image URL provided.")
        return
    
    # Parse the S3 URL to extract bucket name and object key
    try:
        # Parse the BACKGROUND_IMAGE_URL to extract bucket name and object key
        s3_path = BACKGROUND_IMAGE_URL.replace("https://", "").split("/", 1)
        s3_bucket = s3_path[0].split(".")[0]  # Extract bucket name
        s3_object_key = s3_path[1]           # Extract object key
        file_name = os.path.basename(s3_object_key)
        local_file_path = f"/app/static/{file_name}"  # Save the file with same name locally

        print(f"Bucket: {s3_bucket}, Key: {s3_object_key}, Local Path: {local_file_path}")

        # Initialize S3 client
        s3 = boto3.client("s3")

        # Download the file
        s3.download_file(s3_bucket, s3_object_key, local_file_path)
        print("Image downloaded successfully!")

        # Update the global variable to point to the local path
        BACKGROUND_IMAGE_URL = f"/static/{file_name}"
    except IndexError as e:
        print(f"Error parsing BACKGROUND_IMAGE_URL: {BACKGROUND_IMAGE_URL}")
        print(e)
    except NoCredentialsError:
        print("Credentials not available")
    except Exception as e:
        print(f"Error downloading image: {e}")

# Call the function when the app starts
download_image()

app = Flask(__name__)

# Create a connection to the MySQL database
db_conn = connections.Connection(
    host=DBHOST,
    port=DBPORT,
    user=DBUSER,
    password=DBPWD,
    db=DATABASE
)
output = {}
table = 'employee';

# Define the supported color codes
color_codes = {
    "red": "#e74c3c",
    "green": "#16a085",
    "blue": "#89CFF0",
    "blue2": "#30336b",
    "pink": "#f4c2c2",
    "darkblue": "#130f40",
    "lime": "#C1FF9C",
}

# Create a string of supported colors
SUPPORTED_COLORS = ",".join(color_codes.keys())

# Generate a random color
COLOR = random.choice(["red", "green", "blue", "blue2", "darkblue", "pink", "lime"])

@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('addemp.html', background_image_url=BACKGROUND_IMAGE_URL)

@app.route("/about", methods=['GET', 'POST'])
def about():
    # Use the global BACKGROUND_IMAGE_URL for the background image
    return render_template('about.html', background_image_url=BACKGROUND_IMAGE_URL)

@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    primary_skill = request.form['primary_skill']
    location = request.form['location']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    try:
        cursor.execute(insert_sql, (emp_id, first_name, last_name, primary_skill, location))
        db_conn.commit()
        emp_name = first_name + " " + last_name

    finally:
        cursor.close()

    print("All modifications done...")
    
    # Use the global BACKGROUND_IMAGE_URL for the background image
    return render_template('addempoutput.html', background_image_url=BACKGROUND_IMAGE_URL, name=emp_name, color="lime")


@app.route("/getemp", methods=['GET', 'POST'])
def GetEmp():
    # Use the global BACKGROUND_IMAGE_URL for the background image
    return render_template('getemp.html', background_image_url=BACKGROUND_IMAGE_URL, color="lime")


@app.route("/fetchdata", methods=['GET', 'POST'])
def FetchData():
    emp_id = request.form['emp_id']

    output = {}
    select_sql = "SELECT emp_id, first_name, last_name, primary_skill, location from employee where emp_id=%s"
    cursor = db_conn.cursor()

    try:
        cursor.execute(select_sql, (emp_id,))
        result = cursor.fetchone()

        # Populate the output dictionary with the retrieved data
        output["emp_id"] = result[0]
        output["first_name"] = result[1]
        output["last_name"] = result[2]
        output["primary_skills"] = result[3]
        output["location"] = result[4]

    except Exception as e:
        print(e)

    finally:
        cursor.close()
    
    # Use the global BACKGROUND_IMAGE_URL for the background image
    return render_template("getempoutput.html", background_image_url=BACKGROUND_IMAGE_URL, id=output["emp_id"], fname=output["first_name"],
                           lname=output["last_name"], interest=output["primary_skills"], location=output["location"],
                           color=color_codes[COLOR])


if __name__ == '__main__':

    # Check for Command Line Parameters for color
    parser = argparse.ArgumentParser()
    parser.add_argument('--color', required=False)
    args = parser.parse_args()

    if args.color:
        print("Color from command line argument =" + args.color)
        COLOR = args.color
        if COLOR_FROM_ENV:
            print("A color was set through environment variable -" + COLOR_FROM_ENV + ". However, color from command line argument takes precedence.")
    elif COLOR_FROM_ENV:
        print("No Command line argument. Color from environment variable =" + COLOR_FROM_ENV)
        COLOR = COLOR_FROM_ENV
    else:
        print("No command line argument or environment variable. Picking a Random Color =" + COLOR)

    # Check if input color is a supported one
    if COLOR not in color_codes:
        print("Color not supported. Received '" + COLOR + "' expected one of " + SUPPORTED_COLORS)
        exit(1)

    app.run(host='0.0.0.0', port=81, debug=True)
