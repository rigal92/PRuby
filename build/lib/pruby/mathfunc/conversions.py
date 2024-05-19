import pandas as pd 


def cm_inverse_to_wl(value,laser_wl):
    """converts the raman energy in cm inverse to wavelength in meters
    laser_wl in meter"""
    return 1./(1./laser_wl - value*100)


def readPeaks(filename,folder = ""):
    """Read a .peak Fityk file and parse the useful information"""
    if(not folder.endswith("/")): folder = folder + "/" 
    df = pd.read_csv(folder + filename,sep = '\t')

    filename = filename.replace(".peaks","")
    name = filename.split("_")

    out = df.loc[:,["Center","FWHM"]]
    out[["Label","P_label","Time"]] = name
    out = pd.concat([out.iloc[:,2:5],out.iloc[:,0:2]],axis = 1)
    return out

def compute_P(wl,wl0):
    """Computes P(wl)"""
    A = 1.87e3
    B = 5.63
    ratio = (wl -wl0)/wl0
    return A * ratio * (1 + B * ratio)