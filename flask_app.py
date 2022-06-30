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

    def scatter(self):
        if type(self.sigma_x) != np.ndarray and type(self.sigma_y) != np.ndarray:
            plt.scatter(self.x_data, self.y_data)
        else:
            plt.errorbar(self.x_data, self.y_data, self.sigma_y, self.sigma_x, fmt='.')



    def setAxisLabel(self):
        if (self.form['x_label'] != '' ):
            plt.xlabel(self.form['x_label'])
        if (self.form['y_label'] != '' ):
            plt.ylabel(self.form['y_label'])
            

    def doFit(self):
        modello = self.modelli[self.form['modello']]
        popt, pcov = curve_fit(modello, self.x_data, self.y_data, sigma = self.sigma_y )
        return popt, np.sqrt( pcov.diagonal())


    def drawBestFit(self, popt, smooth=100):
        modello = self.modelli[self.form['modello']]
        min = self.x_data.min()
        max = self.x_data.max()
        x_ = np.linspace(min,max,smooth)
        plt.plot(x_,modello(x_, *popt))


    def getOutString(self, popt, sigmas,x2):
        parameters = ['a','b','c']
        output = []
        for p, hat, s in zip(parameters, popt, sigmas):
            output.append( f'{p}= {hat}+/-{s}')
        output.append( f'chi quadro = {x2}')
        return output


    def compute_chi_squared(self, popt):
        # questa funzione calcola il chi-quadro del fit
        # x^2 = \sum{ (modello(x)-y / sigma_y)**2  }
        # se non si sono usate le incertezze, di default utilizza 1
        #ritorna il chi-quadro
        if type(self.sigma_y) != np.ndarray:
            sigma_y = np.full(self.y_data.shape, 1)
        else:
            sigma_y = self.sigma_y

        modello = self.modelli[self.form['modello']]
        expected = modello(self.x_data,*popt)
        return (((expected-self.y_data)/sigma_y)**2).sum()

    def parse_all_data(self):
        # questa funzione prende i parametri del form e li parsa per creare degli np array
        # se fallisce qualcosa ritorna una stringa di errore
        # se la checkbox non è checkata non parsa le incertezze e al posto degli array mette None
        # inoltre controlla cha la lunghezza degli array sia consistente
        # se termina senza errori ritorna 'ok'
        self.x_data = self.parse_data( self.form['x_data'] )
        if type(self.x_data) != np.ndarray:
            return "error: C'è un errore nei valori dell'asse x"
        self.y_data = self.parse_data( self.form['y_data'] )
        if type(self.y_data) != np.ndarray:
            return "error: C'è un errore nei valori dell'asse y"
        if 'uncert_checkbox' in self.form:
            self.sigma_x = self.parse_data( self.form['sigma_x'] )
            if type(self.sigma_x) != np.ndarray:
                return "error: C'è un errore negli errori dell'asse x"
            self.sigma_y = self.parse_data( self.form['sigma_y'] )
            if type(self.sigma_y) != np.ndarray:
                return "error: C'è un errore negli errori dell'asse y"
        else: 
            self.sigma_x = self.sigma_y = None
        if type(self.sigma_x) != np.ndarray and type(self.sigma_y) != np.ndarray:
            if len(self.x_data) != len(self.y_data):
                return "error: le liste devono essere tutte della stassa lunghezza"
        else:        
            result = all(el == len(self.x_data) for el in [len(self.x_data),len(self.y_data),len(self.sigma_x),len(self.sigma_y)] )
            if result == False:
                return "error: le liste devono essere tutte della stassa lunghezza"
        return "ok"

    def handle_graph(self):
        self.fig = plt.figure()

        print("-------\n", self.form, "--------\n" )

        status = self.parse_all_data()
        if status != "ok":
            return status

        self.setAxisLabel()
        
        self.scatter()

        popt, sigmas = self.doFit()
        self.drawBestFit( popt )
 
        x2 = self.compute_chi_squared( popt )
        output = self.getOutString(popt, sigmas, x2)

        plt.savefig("./static/plot.png") #/home/lucapalumbo/lab1plotter/static/plot.png

        return output


