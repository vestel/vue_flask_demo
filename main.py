"""Cloud Foundry test"""
from flask import Flask, json, jsonify, render_template, request, session
import os
import psycopg2

app = Flask(__name__)

port = os.getenv("PORT")
cursor = False
if port:
    port = int(port)
    vcap = json.loads(os.getenv("VCAP_SERVICES"))

    pg = vcap['postgresql'][0]['credentials']
    pg_conn_str = "host='%(hostname)s' port='%(port)s' dbname='%(dbname)s' user='%(username)s' password='%(password)s'" % pg
    pg = psycopg2.connect(pg_conn_str)
    cursor = pg.cursor()
    print "Connected to DB"

@app.route('/')
def hello_world():
    return 'Hello World! I am running on port ' + str(port)

@app.route('/redis')
def redis_data():
    return 'Hello World! I am running on port ' + str(vcap['redis'])

@app.route('/todo')
def todo():
    return render_template('index.html')

@app.route('/migrate')
def migrate():
    sql = """CREATE TABLE tasks
    (
      id serial NOT NULL,
      text character varying(128),
      done boolean DEFAULT FALSE,
      CONSTRAINT tasks_pkey PRIMARY KEY (id)
    )"""
    if cursor:
        cursor.execute('DROP TABLE IF EXISTS tasks')
        cursor.execute(sql)
        cursor.execute("INSERT INTO tasks (text) VALUES ('Fresh dump been loaded')")
    return "Database migrated"

@app.route('/api/list')
def list():
    data = []
    default = [
        {'index': 1, 'text': 'This is from Python', 'done': False},
        {'index': 2, 'text': 'Ajax works', 'done': True}
    ]
    if cursor:
        sql = "SELECT * FROM tasks";
        cursor.execute(sql);
        for line in cursor.fetchall():
            data.append({'index': line[0], 'text': line[1], 'done': line[2]})
        print "Retrieved", data
    if not data:
        data = default
    return jsonify(data)

@app.route('/api/append', methods=['POST'])
def append():
    if request.is_json:
        text = request.json.get('value')
    id = 34
    if cursor:
        sql = "INSERT INTO tasks (text, done) VALUES (%s, %s) RETURNING id"
        cursor.execute(sql, (text, False))
        id = cursor.fetchone()[0]
    return jsonify({'index': id})

@app.route('/api/update', methods=['POST'])
def update():
    if request.is_json:
        data = request.json.get('value')
    toggle_id = int(data)
    if cursor:
        sql = "UPDATE tasks SET done = NOT done WHERE id=%s"
        cursor.execute(sql, (toggle_id,))
        print 'DB updated'
    return jsonify({})

if __name__ == '__main__':
    print migrate()
    app.run(host='0.0.0.0', port=port)
