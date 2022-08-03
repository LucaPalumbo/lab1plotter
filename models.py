import numpy as np
def parabola(x,a, b, c):
    return a*x**2 + b*x +c

def sinusoide(x,a,b,c):
    return a*np.sin(x*b+c)

def retta(x,a,b):
    return a*x+b

def esponenziale(x,a,b,c):
    return a* (np.e**(b*x) ) 