from flask import Flask, redirect, render_template, request, send_file
from flask.helpers import flash
import json
import numpy as np
from matplotlib import pyplot as plt
from scipy.optimize import curve_fit

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
        return render_template("index.html", out=output )

        #return send_file('plot.png', mimetype='image/png')



def parabola(x,a, b, c):
    return a*x**2 + b*x +c

def sinusoide(x,a,b,c):
    return a*np.sin(x*b+c)

class Plotter(object):

    def __init__(self, form):
        super(Plotter, self).__init__()
        self.form = form
        self.modelli = {
            'parabola': parabola,
            'sinusoide': sinusoide
        }

    def parse_data(self,data):
        try:
            array =  np.array( json.loads(data) )
            return array
        except:
            return False

    def scatter(self, fig ,x_data, y_data, sigma_x, sigma_y):
        plt.errorbar(x_data, y_data, sigma_y, sigma_x, fmt='.')

    def setAxisLabel(self, fig, label, axis):
        if axis == 'x':
            plt.xlabel(label)
        if axis == 'y':
            plt.ylabel(label)


    def doFit(self, modello, x_data, y_data, sigma_y ):
        popt, pcov = curve_fit(modello, x_data, y_data, sigma = sigma_y )
        return popt, np.sqrt( pcov.diagonal())


    def drawBestFit(self, modello, popt, x_data, smooth=100):
        min = x_data.min()
        max = x_data.max()
        x_ = np.linspace(min,max,smooth)
        plt.plot(x_,modello(x_, *popt))


    def getOutString(self, popt, sigmas,x2):
        parameters = ['a','b','c']
        output = []
        for p, hat, s in zip(parameters, popt, sigmas):
            output.append( f'{p}= {hat}+/-{s}')
        output.append( f'chi quadro = {x2}')
        return output


    def compute_chi_squared(self,modello, popt, x_data, y_data, sigma_y):
        expected = modello(x_data,*popt)
        return (((expected-y_data)/sigma_y)**2).sum()

    def handle_graph(self):
        self.fig = plt.figure()

        print( self.form )

        self.x_data = self.parse_data( self.form['x_data'] )
        if type(self.x_data) != np.ndarray:
            return "error: C'è un errore nei valori dell'asse x"
        self.y_data = self.parse_data( self.form['y_data'] )
        if type(self.y_data) != np.ndarray:
            return "error: C'è un errore nei valori dell'asse y"
        self.sigma_x = self.parse_data( self.form['sigma_x'] )
        if type(self.sigma_x) != np.ndarray:
            return "error: C'è un errore negli errori dell'asse x"
        self.sigma_y = self.parse_data( self.form['sigma_y'] )
        if type(self.sigma_y) != np.ndarray:
            return "error: C'è un errore negli errori dell'asse y"


        result = all(el == len(self.x_data) for el in [len(self.x_data),len(self.y_data),len(self.sigma_x),len(self.sigma_y)] )
        if result == False:
            return "error: le liste devono essere tutte della stassa lunghezza"

        if (self.form['x_label'] != '' ):
            self.setAxisLabel(self.fig,self.form['x_label'],'x')
        if (self.form['y_label'] != '' ):
            self.setAxisLabel(self.fig,self.form['y_label'],'y')

        self.scatter(self.fig,self.x_data, self.y_data, self.sigma_x, self.sigma_y)

        popt, sigmas = self.doFit(self.modelli[self.form['modello']] , self.x_data, self.y_data, self.sigma_y)
        self.drawBestFit(self.modelli[self.form['modello']],popt,  self.x_data)

        x2 = self.compute_chi_squared(self.modelli[self.form['modello']], popt, self.x_data, self.y_data, self.sigma_y)
        output = self.getOutString(popt, sigmas, x2)

        plt.savefig("/home/lucapalumbo/lab1plotter/static/plot.png")#/home/lucapalumbo/lab1plotter/static/plot.png

        return output


        return output
