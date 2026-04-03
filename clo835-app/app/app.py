from flask import Flask, render_template, request
from pymysql import connections
import os
import random
import boto3
from botocore.exceptions import ClientError

app = Flask(__name__)

DBHOST = os.environ.get("DBHOST", "localhost")
DBUSER = os.environ.get("DBUSER", "root")
DBPWD = os.environ.get("DBPWD", "pw")
DATABASE = os.environ.get("DATABASE", "employees")
DBPORT = int(os.environ.get("DBPORT", 3306))

APP_COLOR = os.environ.get("APP_COLOR", "lime")
MY_NAME = os.environ.get("MY_NAME", "Group 9")
BG_IMAGE_URL = os.environ.get("BG_IMAGE_URL", "")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

LOCAL_IMAGE_DIR = "static/downloads"
LOCAL_IMAGE_NAME = "background.jpg"
LOCAL_IMAGE_PATH = os.path.join(LOCAL_IMAGE_DIR, LOCAL_IMAGE_NAME)
LOCAL_IMAGE_WEB_PATH = f"/{LOCAL_IMAGE_PATH}"

table = "employee"

color_codes = {
    "red": "#e74c3c",
    "green": "#16a085",
    "blue": "#89CFF0",
    "blue2": "#30336b",
    "pink": "#f4c2c2",
    "darkblue": "#130f40",
    "lime": "#C1FF9C",
}

COLOR = APP_COLOR if APP_COLOR in color_codes else "lime"


def get_db_connection():
    return connections.Connection(
        host=DBHOST,
        port=DBPORT,
        user=DBUSER,
        password=DBPWD,
        db=DATABASE
    )


def download_s3_image():
    if not BG_IMAGE_URL:
        return None

    if not BG_IMAGE_URL.startswith("s3://"):
        print(f"BG_IMAGE_URL is invalid: {BG_IMAGE_URL}")
        return None

    try:
        s3_path = BG_IMAGE_URL.replace("s3://", "", 1)
        bucket, key = s3_path.split("/", 1)

        os.makedirs(LOCAL_IMAGE_DIR, exist_ok=True)

        s3 = boto3.client("s3", region_name=AWS_REGION)
        s3.download_file(bucket, key, LOCAL_IMAGE_PATH)

        print(f"Background image URL: {BG_IMAGE_URL}")
        print(f"Downloaded image to: {LOCAL_IMAGE_PATH}")
        return f"/{LOCAL_IMAGE_PATH}"
    except (ValueError, ClientError, Exception) as e:
        print(f"Failed to download image from S3: {e}")
        return None


def resolve_background_image():
    if BG_IMAGE_URL:
        s3_image = download_s3_image()
        if s3_image:
            return s3_image

    # Local fallback for Docker/local testing if a bundled image exists.
    if os.path.exists(LOCAL_IMAGE_PATH):
        print(f"Using bundled local background image: {LOCAL_IMAGE_WEB_PATH}")
        return LOCAL_IMAGE_WEB_PATH

    print("No background image configured.")
    return None


BACKGROUND_IMAGE = resolve_background_image()


@app.route("/", methods=["GET", "POST"])
def home():
    return render_template(
        "addemp.html",
        color=color_codes[COLOR],
        my_name=MY_NAME,
        background_image=BACKGROUND_IMAGE
    )


@app.route("/about", methods=["GET", "POST"])
def about():
    return render_template(
        "about.html",
        color=color_codes[COLOR],
        my_name=MY_NAME,
        background_image=BACKGROUND_IMAGE
    )


@app.route("/addemp", methods=["POST"])
def AddEmp():
    emp_id = request.form["emp_id"]
    first_name = request.form["first_name"]
    last_name = request.form["last_name"]
    primary_skill = request.form["primary_skill"]
    location = request.form["location"]

    # Input validation: do not insert if any field is empty
    if not all([emp_id, first_name, last_name, primary_skill, location]):
        return render_template(
            "addempoutput.html",
            name="Input Error: All fields are required!",
            color=color_codes[COLOR],
            my_name=MY_NAME,
            background_image=BACKGROUND_IMAGE
        )

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(insert_sql, (emp_id, first_name, last_name, primary_skill, location))
        conn.commit()
        emp_name = first_name + " " + last_name
    finally:
        cursor.close()
        conn.close()

    return render_template(
        "addempoutput.html",
        name=emp_name,
        color=color_codes[COLOR],
        my_name=MY_NAME,
        background_image=BACKGROUND_IMAGE
    )


@app.route("/getemp", methods=["GET", "POST"])
def GetEmp():
    return render_template(
        "getemp.html",
        color=color_codes[COLOR],
        my_name=MY_NAME,
        background_image=BACKGROUND_IMAGE
    )


@app.route("/fetchdata", methods=["GET", "POST"])
def FetchData():
    emp_id = request.form["emp_id"]

    select_sql = """
        SELECT emp_id, first_name, last_name, primary_skill, location
        FROM employee
        WHERE emp_id=%s
    """

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(select_sql, (emp_id,))
        result = cursor.fetchone()

        if not result:
            return render_template(
                "getempoutput.html",
                id="Not found",
                fname="N/A",
                lname="N/A",
                interest="N/A",
                location="N/A",
                color=color_codes[COLOR],
                my_name=MY_NAME,
                background_image=BACKGROUND_IMAGE
            )

        return render_template(
            "getempoutput.html",
            id=result[0],
            fname=result[1],
            lname=result[2],
            interest=result[3],
            location=result[4],
            color=color_codes[COLOR],
            my_name=MY_NAME,
            background_image=BACKGROUND_IMAGE
        )
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=81, debug=True)