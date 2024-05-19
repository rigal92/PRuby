import pandas as pd 


def normalize(data, factor = None):
    if(factor == None):
        return data/data.max()
    else:
        return data/factor


def normalize_spectrum(df, column, ignore = ["x"]):
    """
    Normalize a data frame by one column. Columns in ignore (type = list) will be skipped.
    """
    M = max(df[column])
    if(ignore):
        df_out = df.iloc[:,df.columns.isin(ignore)]
        df = df.iloc[:,df.columns.isin(ignore)^True]
        
    else:
        df_out = pd.DataFrame()
        
            
    return pd.concat([df_out,pd.eval("df/M")],axis = 1)

def lorentzian(x, A=1, x0=0, FWHM=1):
    """Lorentzian function for fitting"""
    return A/(1 + ((x-x0)/(FWHM/2))**2)

def twoLorentzian(x, *pars):
    return lorentzian(x,pars[0],pars[1],pars[2]) + lorentzian(x,pars[3],pars[4],pars[5])

def bg_quadratic(x, a0,a1,a2):
    return a0 + a1 * x + a2 * x**2

def fitFunction(x, *pars):
    return bg_quadratic(x, pars[0], pars[1], pars[2])  + twoLorentzian(x,pars[3],pars[4],pars[5],pars[6],pars[7],pars[8]) 

