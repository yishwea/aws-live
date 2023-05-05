from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from config import *

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'


@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('AddEmp.html')


@app.route("/about")
def about():
    return render_template('AboutUs.html')


@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    emp_image_file = request.files['emp_image_file']

    select_sql = "SELECT COUNT(*) FROM employee WHERE emp_id = %s"
    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:
        # Check if emp_id already exists in the database
        cursor.execute(select_sql, (emp_id,))
        result = cursor.fetchone()

        if result is not None:
            return "Employee ID already exists, Please enter a different ID"

        cursor.execute(insert_sql, (emp_id, first_name, last_name, pri_skill, location))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name

        # Upload image file to S3
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("All modifications done...")
    return render_template('AddEmpOutput.html', name=emp_name)


@app.route("/UpEmp", methods=['POST'])
def UpEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    emp_image_file = request.files['emp_image_file']

    select_sql = "SELECT COUNT(*) FROM employee WHERE emp_id = %s"
    edit_sql = "UPDATE employee SET first_name=%s, last_name=%s, pri_skill=%s, location=%s WHERE emp_id=%s"
    cursor = db_conn.cursor()

    try:
        cursor.execute(select_sql, (emp_id))
        result = cursor.fetchone()

        if result is None:
            return "Employee ID not exists, Please enter a different ID"

        cursor.execute(edit_sql, (first_name, last_name, pri_skill, location, emp_id))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name

        if emp_image_file.filename != "":
            key = "emp-id-" + str(emp_id) + "_image_file.png"
            emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file.png"
            s3 = boto3.resource('s3')

            try:
                print("Data inserted in MySQL RDS... uploading image to S3...")
                s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
                bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
                s3_location = (bucket_location['LocationConstraint'])

                if s3_location is None:
                    s3_location = ''
                else:
                    s3_location = '-' + s3_location

                object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                    s3_location,
                    custombucket,
                    emp_image_file_name_in_s3)

            except Exception as e:
                return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('UpdateEmpOutput.html', name=emp_name, id=emp_id)

@app.route("/fetchdata", methods=['GET', 'POST'])
def FetchData():
    emp_id = request.form['emp_id']
    select_sql = "SELECT COUNT(*) FROM employee WHERE emp_id = %s"
    sqlCmd = "SELECT * FROM employee WHERE emp_id=%s"
    cursor = db_conn.cursor()

    if emp_id == "":
        return "Please enter an employee ID"

    cursor.execute(select_sql, (emp_id))
    result = cursor.fetchone()

    if result is None:
        return "Employee ID not exists, Please enter a different ID"

    try:
        #Getting Employee Data
        cursor.execute(sqlCmd, (emp_id))
        row = cursor.fetchone()
        dEmpID = row[0]
        dFirstName = row[1]
        dLastName = row[2]
        dPriSkill = row[3]
        dLocation = row[4]

        key = "emp-id-" + str(emp_id) + "_image_file.png"

        # Get Image URL
        # bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
        # s3_location = (bucket_location['LocationConstraint'])

        s3_client = boto3.client('s3')
        for item in s3_client.list_objects(Bucket=custombucket)['Contents']:
            if(item['Key'] == key):
                url = s3_client.generate_presigned_url('get_object', Params = {'Bucket': bucket, 'Key': item['Key']})

        #url = "https://%s.s3.amazonaws.com/%s" % (custombucket, key)

    except Exception as e:
        return str(e)
        
    finally:
        cursor.close()

    return render_template("GetEmpOutput.html", id=dEmpID, fname=dFirstName, 
    lname=dLastName, interest=dPriSkill, location=dLocation, image_url=url)

@app.route("/getemp")
def getemp():
    return render_template('GetEmp.html')

@app.route("/upemp")
def upemp():
    return render_template('UpdateEmp.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
