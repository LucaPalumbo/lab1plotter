from flask import Flask, redirect, render_template, request, url_for, send_file
from flask.helpers import flash
import json
import numpy as np
from matplotlib import pyplot as plt
from scipy.optimize import curve_fit
import random

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


def parabola(x,a, b, c):
    return a*x**2 + b*x +c

def sinusoide(x,a,b,c):
    return a*np.sin(x*b+c)

def retta(x,a,b):
    return a*x+b

def esponenziale(x,a,b,c):
    return a* (np.e**(b*x) ) 

class Plotter(object):
    def __init__(self, form):
        super(Plotter, self).__init__()
        self.form = form
        self.modelli = {
            'parabola': parabola,
            'sinusoide': sinusoide,
            'retta': retta,
            'esponenziale': esponenziale
        }

    def parse_data(self,data):
        # prende una stringa e prova a valutarla come una lista python
        # se riesce la converte in array e la ritorna
        # altrimenti ritorna False
        try:
            array =  np.array( json.loads(data) )
            return array
        except:
            return False

    def scatter(self, x=None, y=None, sigma_y = None, sigma_x = None, label=None):
        # questa funzione disegna i dati inseriti dallo user
        # se le incertezze sono inserite usa errorbar, altrimenti scatter
        if 'legend_checkbox' in self.form and label == None:
            label = self.form['legend']
        if type(x) != np.ndarray:
            x = self.x_data
        if type(y) != np.ndarray:
            y = self.y_data
        if type(sigma_y) != np.ndarray:
            sigma_y = self.sigma_y
        if type(sigma_x) != np.ndarray:
            sigma_x = self.sigma_x
        if type(sigma_x) != np.ndarray and type(sigma_y) != np.ndarray:
            plt.scatter(x, y, label=label)
        else:
            plt.errorbar(x, y, sigma_y, sigma_x, fmt='.', label=label)

    def setAxisLabel(self, x_axis = None, y_axis = None):
        # assegna i nomi agli assi se inseriti
        if x_axis == None:
            x_axis = self.form['x_label']
        if y_axis == None:
            y_axis = self.form['y_label']
        if (x_axis != '' ):
            plt.xlabel(x_axis)
        if (y_axis != '' ):
            plt.ylabel(y_axis)
            
    def doFit(self):
        # Questa funzione si occupa di effettuare il fit
        # in questa funzione non faccio controlli su self.sigma_y perche curve_fit
        # accetta anche None come valore
        # returna parametri ottimali e incertezze ricavate dalla radice quadrata della diagonale
        # della matrice di covarianza
        modello = self.modelli[self.form['modello']]
        popt, pcov = curve_fit(modello, self.x_data, self.y_data, sigma = self.sigma_y )
        return popt, np.sqrt( pcov.diagonal())

    def drawBestFit(self, popt, label=None, smooth=500):
        # si occupa di disegnare il grafico di miglior fit
        label = "Best fit"
        modello = self.modelli[self.form['modello']]
        min = self.x_data.min()
        max = self.x_data.max()
        x_ = np.linspace(min,max,smooth)
        plt.plot(x_,modello(x_, *popt),label=label)

    def getOutString(self, popt, sigmas,x2):
        # genera una stringa da mostrare all'utente che contiene informazioni sul fit
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

    def compute_residuals(self,popt):
        modello = self.modelli[self.form['modello']]
        res = modello(self.x_data,*popt)- self.y_data
        return res

    def grid(self):
        # se specificato aggiunge la griglia di sfondo
        if 'grid_checkbox' in self.form:
            plt.grid(axis='both', ls='dashed', color='gray')
    
    def legend(self):
        if 'legend_checkbox' in self.form:
            plt.legend()

    def get_image_name(self):
        return self.image_name

    def handle_graph(self):
        # gestisce la creazione del grafico
            
        self.fig = plt.figure()
        if 'residuals_checkbox' in self.form:
            self.fig.add_axes((0.1, 0.3, 0.8, 0.6))
        
        print("-------\n", self.form, "--------\n" )

        status = self.parse_all_data()
        if status != "ok":
            return status

        self.setAxisLabel()

        self.scatter()
        self.grid()
        
        popt, sigmas = self.doFit()
        self.drawBestFit( popt)

        self.legend()

        if 'residuals_checkbox' in self.form:
            self.fig.add_axes((0.1, 0.1, 0.8, 0.2))
            res = self.compute_residuals(popt)
            self.setAxisLabel(y_axis='Residui')
            self.scatter(y = res)
            self.grid()


        x2 = self.compute_chi_squared( popt )
        output = self.getOutString(popt, sigmas, x2)

        self.image_name = f"plot{str(random.randint(0,100))}.png"
        plt.savefig("./static/" + self.image_name) #/home/lucapalumbo/lab1plotter/static/plot.png

        return output


