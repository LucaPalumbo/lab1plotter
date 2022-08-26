from flask import Flask, redirect, render_template, request, url_for, send_file, jsonify
from flask.helpers import flash
import json
import random


from plotter import Plotter
from models import * 

app = Flask(__name__)
app.secret_key = 'qwerty'


@app.route('/',  methods=['POST', 'GET'] )
def index():
    if request.method == 'GET':
        return render_template("index.html")

    if request.method == 'POST':
        p = Plotter(request.form)
        output = p.handle_graph()
        if "error" in output:
            flash(output)
            return redirect(url_for("index"))
        img = p.get_image_name()
        return render_template("index.html", out=output, image = img )


@app.route('/api/', methods=['GET','POST'])
def api():
    if request.method == 'POST':
        data = request.get_data().decode()
        p = Plotter( data )
        output = p.handle_graph()
        img  = p.get_image_name()
        print(output, img)
        return jsonify({'img': img, 'output': output})
    if request.method == 'GET':
        return jsonify({'test': 'test2'})