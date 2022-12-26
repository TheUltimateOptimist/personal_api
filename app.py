from flask import jsonify
from flask import Flask
from flask import request
import time

app = Flask(__name__)

import mysql.connector

def get_conn(db="TheUltimateOptim$tracker"):
    return mysql.connector.connect(
        host="TheUltimateOptimist.mysql.pythonanywhere-services.com",
        user="TheUltimateOptim",
        password="!566071!A1a1B2b2",
        db=db
)

@app.route("/")
def index():
    return "This is the API for the Training Tracker!"

@app.route("/sets/<int:performance_id>",  methods=["POST"])
def add_set(performance_id):
    if request.method == "POST":
        index = int(request.form["index"])
        tension = float(request.form["tension"])
        note = request.form["note"]
        reps = float(request.form["reps"])
        import time
        start = round(time.time())
        rest = int(request.form["rest"])
        db = get_conn()
        cursor = db.cursor()
        cursor.execute(f"INSERT INTO sets(indx, tension, start, rest, performance_id, note, reps)VALUES({index}, {tension}, {start}, {rest}, {performance_id}, '{note}', {reps})")
        db.commit()
        cursor.close()
        return "success"

@app.route("/sessions/<string:user_name>", methods=["POST"])
def start_training(user_name):
    if request.method == "POST":
        bodyweight = float(request.form["bodyweight"])
        import time
        start = round(time.time())
        db = get_conn()
        cursor = db.cursor()
        cursor.execute(f"INSERT INTO sessions(start, bodyweight, user_name)VALUES({start}, {bodyweight}, '{user_name}')")
        cursor.execute(f"SELECT MAX(id) from sessions")
        result =  str(cursor.fetchall()[0][0])
        db.commit()
        cursor.close()
        return result

@app.route("/exercises/<string:user_name>", methods=["GET"])
def get_exercises(user_name):
    if request.method == "GET":
        db = get_conn()
        cursor = db.cursor()
        cursor.execute(f"SELECT id, name from exercises where user_name = '{user_name}'")
        exercises = cursor.fetchall()
        cursor.close()
        return jsonify(exercises)

@app.route("/performances/<int:session_id>/<int:exercise_id>/<string:tension_type>", methods=["POST"])
def start_performance(session_id, exercise_id, tension_type):
    if request.method == "POST":
        db = get_conn()
        cursor = db.cursor()
        cursor.execute(f"INSERT INTO performances(exercise_id, tension_type, session_id)VALUES({exercise_id}, '{tension_type}', {session_id})")
        cursor.execute(f"SELECT MAX(id) from performances")
        result = str(cursor.fetchall()[0][0])
        db.commit()
        cursor.close()
        return result

@app.route("/tension_types/<int:exercise_id>")
def get_tension_types(exercise_id):
    db = get_conn()
    cursor = db.cursor()
    cursor.execute(f"SELECT tension_type from tension_type_mappings where exercise_id = {exercise_id}")
    result = cursor.fetchall()
    final_list = []
    for row in result:
        final_list.append(row[0])
    cursor.close()
    return jsonify(final_list)

@app.route("/last_stats/<int:exercise_id>/<string:tension_type>/<int:session_id>")  
def get_last_stats(exercise_id, tension_type, session_id):
    db = get_conn()
    cursor = db.cursor()
    cursor.execute(f"Select indx, tension, reps, note from sets where performance_id = (SELECT MAX(id) from performances where exercise_id = {exercise_id} and tension_type = '{tension_type}' and session_id != {session_id});")
    result = cursor.fetchall()
    cursor.close()
    return jsonify(result)

@app.route("/performances/remove/<int:performance_id>", methods = ["POST"])
def remove_performance(performance_id):
    db = get_conn()
    cursor = db.cursor()
    cursor.execute(f"delete from performances where id = {performance_id}")
    db.commit()
    cursor.close()
    return "success"

@app.route("/sets/history/<int:exercise_id>/<string:tension_type>", methods = ["GET"])
def get_history(exercise_id, tension_type):
    db = get_conn()
    cursor = db.cursor()
    cursor.execute(f"SELECT indx, tension, reps, note FROM sets LEFT JOIN performances ON performance_id = performances.id WHERE exercise_id = {exercise_id} AND tension_type = '{tension_type}';")
    result = cursor.fetchall()
    cursor.close()
    return jsonify(result)

@app.route("/worktracker/session/add", methods=["POST"])
def add_session():
    db = get_conn(db="TheUltimateOptim$worktracker")
    cursor = db.cursor()
    start = request.form["start"]
    end = request.form["end"]
    topic_id = request.form["topic_id"]
    cursor.execute(f"INSERT INTO sessions(start, end, topic_id)VALUES({start}, {end}, '{topic_id}')")
    db.commit()
    cursor.close()
    return "success"

@app.route("/worktracker/topic/name/<int:topic_id>", methods=["GET"])
def get_topic_name(topic_id):
    db = get_conn(db="TheUltimateOptim$worktracker")
    cursor = db.cursor()
    cursor.execute(f"SELECT name from topics where id = {topic_id}")
    result = cursor.fetchall()
    if len(result) == 0:
        return "None"
    return result[0][0]

@app.route("/worktracker/topic/add", methods=["POST"])
def add_topic():
    db = get_conn(db="TheUltimateOptim$worktracker")
    cursor = db.cursor()
    topic_name = request.form["topic"]
    parent_id = request.form["parent_id"]
    cursor.execute(f"INSERT INTO topics(name) VALUES('{topic_name}')")
    cursor.execute("select last_insert_id()")
    topic_id = cursor.fetchall()[0][0]
    cursor.execute(f"INSERT INTO hierarchy (parent, child, depth) SELECT parent, {topic_id}, depth + 1 from hierarchy where child = {parent_id}")
    cursor.execute(f"INSERT INTO hierarchy (parent, child, depth) VALUES({parent_id}, {topic_id}, 1)")
    db.commit()
    cursor.close()
    return str(topic_id)

@app.route("/worktracker/hierarchy/<int:parent_id>", methods=['GET'])
def get_hierarchy(parent_id: int):
    db = get_conn(db="TheUltimateOptim$worktracker")
    cursor = db.cursor()
    cursor.execute(f"select name, parent, child from hierarchy left join topics on child = id where depth = 1 and child in (SELECT DISTINCT child from hierarchy where parent = {parent_id})")
    result = jsonify(cursor.fetchall())
    cursor.close()
    return result

@app.route("/worktracker/topic/last/<int:steps_back>")
def get_past_topic_id(steps_back: int):
    db = get_conn(db="TheUltimateOptim$worktracker")
    cursor = db.cursor()
    cursor.execute(f"SELECT topic_id from sessions order by id DESC limit {steps_back}")
    result = cursor.fetchall()[steps_back - 1][0]
    cursor.close()
    return str(result)

@app.route("/worktracker/sessions/last/<int:steps_back>")
def get_past_sessions(steps_back: int):
    db = get_conn(db="TheUltimateOptim$worktracker")
    cursor = db.cursor()
    cursor.execute(f"select topic_id, name, start, end from sessions left join topics on topics.id = topic_id order by sessions.id desc limit {steps_back}")
    result = cursor.fetchall()
    cursor.close()
    return jsonify(result)

@app.route("/worktracker/sessions/today")
def get_todays_sessions():
    db = get_conn(db="TheUltimateOptim$worktracker")
    cursor = db.cursor()
    import datetime
    now = datetime.datetime.fromtimestamp(time.time())
    start = datetime.datetime(now.year, now.month, now.day).timestamp()
    cursor.execute(f"select topic_id, name, start, end from sessions left join topics on topics.id = topic_id where start >= {start} order by sessions.id desc")
    result = cursor.fetchall()
    cursor.close()
    return jsonify(result)

if __name__ == "__main__":
    app.run()