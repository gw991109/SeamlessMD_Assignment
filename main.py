from flask import Flask, render_template, request, redirect, url_for, flash
import requests
from dateutil.relativedelta import relativedelta
from datetime import datetime
import json

app = Flask(__name__)


@app.route("/", methods=["POST", "GET"])
def home():
    """
    Home page where users can input the number of patients to fetch.
    :return: redirect to table page or render html template.
    """
    if request.method == "POST":
        num = request.form["number"]
        if not str.isdigit(num) or int(num) <= 0:
            flash("Please input a positive integer.")
            return redirect(request.url)
        return redirect(url_for("table", num=num))
    else:
        return render_template("fetch.html")


@app.route("/<num>")
def table(num):
    """
    Page displaying the information on patients fetched in the form of a table.
    :param num: the number of patients to be fetched.
    :return: html page to be rendered where the table is displayed.
    """
    # Fetch the requested amount of patients using the HAPI FHIR API call and
    # process in json format.
    url = f"http://hapi.fhir.org/baseR4/Patient/$everything?_count={num}"
    jsn = requests.get(url=url).json()
    # with open('./sample.json') as file:
    #     jsn = json.load(file)
    global resources
    print(jsn)
    resources = jsn['entry']
    headings = ["Patient ID", "Family Name", "Given Name", "Date of Birth",
                "Gender"]
    data = []
    for resource in resources:
        patient = resource["resource"]
        # Assume patient has no information at all.
        entry = [patient["id"], "N/A", "N/A", "N/A", "N/A"]
        if "name" in patient:
            family_name = patient["name"][0]['family']
            given_name = patient["name"][0]['given'][0]
            entry[1], entry[2] = family_name, given_name
        if "birthDate" in patient:
            entry[3] = patient["birthDate"]
        if "gender" in patient:
            entry[4] = patient["gender"]
        data.append(entry)

    return render_template("table.html", headings=headings, data=data)


@app.route("/summary", methods=["POST", "GET"])
def summary():
    """
    Page displaying the information on patients fetched in the form of a table.
    :param num: the number of patients to be fetched.
    :return: html page to be rendered where the table is displayed.
    """

    average_age, counted = _find_average_age()
    male, female = _find_male_female_percentage()
    headings = ["Total Number of Patients", "Average Age",
                "Patients Involved In Average Age", "Percentage of Male",
                "Percentage of Female"]
    data = [len(resources), average_age, counted, male, female]
    return render_template("summary.html", headings=headings, data=data)


def _find_average_age():
    """
    private function to find the average age of all patients fetched. Note that
    some patients do not have a date of birth so count indicates how many
    patients are involved in the average.
    :param resources: the resources field extracted from the json, used to
    further extract patient information.
    :return: a count of how many patients were involved in the average, and the
    resulting average age. Returns 0, 0 in the event of all patients not having an
    age.
    """
    count, total = 0, 0
    for resource in resources:
        patient = resource["resource"]
        if "birthDate" in patient:
            count += 1
            dob = patient["birthDate"].split("-")
            dob = datetime(int(dob[0]), int(dob[1]), int(dob[2]), 0, 0, 0, 0)
            if "deceasedDateTime" in patient:
                death_time = patient["deceasedDateTime"].split("T")[0].split(
                    "-")
                death_time = datetime(int(death_time[0]), int(death_time[1]),
                                      int(death_time[2]), 0, 0, 0, 0)
            else:
                death_time = datetime.now()
            age = relativedelta(death_time, dob).years
            total += age
    if count == 0:
        return count, count
    return total / count, count


def _find_male_female_percentage():
    """
    determine the male and female percentage among the patients fetched.
    :return: return 0, 0 in the event that no gender information is available
    for all patients.
    """
    count, male = 0, 0
    for resource in resources:
        patient = resource["resource"]
        if "gender" in patient:
            count += 1
            if patient["gender"] == "male":
                male += 1
    if count == 0:
        return 0, 0
    return male / count, 1 - (male / count)


if __name__ == "__main__":
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(debug=True)
