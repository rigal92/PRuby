import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import signal as sg
from scipy.optimize import curve_fit


#local import
from pruby.mathfunc.conversions import cm_inverse_to_wl,compute_P
from pruby.mathfunc.math_def import *



def tokenize(string, char = "_"):
    """
    Split the file name in individual tokens that can have important information 
    e.g. A_P03_initial has the inforation of the pressure point (Pid = P03) and if the pressure was measured
    before or after the datapoints (time = i)


    """
    #some definition to indicate the time of the pressure acquisition during the experiment
    time_def = {"f","i","initial","final"}

    s = string.split(char)

    tokens = {}
    count = 0
    for i in s:
        if(i.startswith("P") and not ("Pid" in tokens)):
            tokens["Pid"] = i
        elif(i in time_def):
            tokens["Time"] = i
        elif(i.startswith("R") and not ("Rubyid" in tokens)):
            tokens["Rubyid"] = i 
        else:
            tokens[f"extra{count + 1}"] = i
            count +=1
    return tokens 


 
class PData(dict):
    """
    Create a pressure data object. 

    Input
    -----------------------------------------------------------------
    data: str or pd.DataFrame
        Filename or DataFrame to assign to data. If a *str* is given 
        it is assumed to be a filename. pd.read_table is then called
        using *read_data_args* in order to create a DataFrame
    name: str, default = ""
        PData name
    read_data_args: dict, default = {"comment"="#", "header" = None}
        arguments to be passed to pd.read_table for the data

    """

    def __init__(self, data, name = "",read_data_args = {"comment":"#", "header":None,"encoding_errors":"replace"}):
        if(isinstance(data,str)):
            #case where filename is passed as an argument 
            self["data"] = pd.read_table(data,**read_data_args)
            self["data"].rename(columns={0:"x",1:"y"},inplace = True)
        else:
            self["data"] = data
        self["name"] = name
        self["tokens"] = tokenize(name)
        self["P"] = None

     
    def guess_old(self, min_height = None, min_width = 5):
        """
        -----------------------------------------------------------------
        DEPRECATED
        -----------------------------------------------------------------
        Guess of initial parameters for fitting using scipy.signal.find_peak. 
        min_height sets the limit for acceptable peak heights for find peak. If none max(data)/5 is used.
        min_width set the minimum acceptable FWHM for find peak
        Background is quadratic 
        """
        name = self["name"] 
        print(f"Guessing initial parameters for {name}...")


        data = self["data"] 
        x,y = data.x,data.y

        #estimate R1 and R2 position, height and FWHM
        if(min_height == None): min_height = y.max()/5
        peaks, propr = sg.find_peaks(y, height = min_height, width = min_width)

        if(len(peaks) !=2):
            print(f'{len(peaks)} peaks have been found for {name}. Try adjusting height and width levels for peak find.')
            data["ftot"] = 0
            data["bg"]= 0
            data["R2"]= 0
            data["R1"]= 0
            self["fit_par"] = [0]*9
        else:
            print(f"Found {len(peaks)}. All good mate.")
            peak_x0 = x[peaks]
            peak_heights = propr['peak_heights']
            # widths are calculated on the indices from find_peaks 
            # peak_widths = propr['widths']
            # to find widths we need to find the x values corresponiding to the widths
            h = propr['width_heights'] # estimated height to calculate the width
            left_i = propr["left_ips"].astype(int) # index of the width on the left of the peak
            xmin = interpolate(h, y[left_i].values, y[left_i + 1].values, x[left_i].values, x[left_i + 1].values)
            right_i = propr["right_ips"].astype(int) # index of the width on the right of the peak
            xmax = interpolate(h, y[right_i].values, y[right_i + 1].values, x[right_i].values, x[right_i + 1].values)
            peak_widths = xmax - xmin 

            guess = [x for sl in zip(peak_heights, peak_x0, peak_widths) for x in sl]

            guess_bg = [y[0], 0, 0]

            self["fit_par"] = guess_bg + guess 
            self.update_function()

     
    def guess(self,min_width = 5):
        """
        Guess of initial parameters for fitting. Higher peak is assigned
        to R1. Then higher peak on the residual is assigned to R2.   
        Background is quadratic.

        Input
        -----------------------------------------------------------------
        min_width: float, default = 5
            minimum width (in points) accepted for guessing 
        """
        def get_peak():
            """
            Extract maximum peak values after find_peaks

            """

            i = res[peaks].argmax() # index of higher peak
            x0 = x[peaks[i]]
            height = res[peaks[i]]
            # widths are calculated on the indices from find_peaks 
            # peak_widths = propr['widths']
            # to find widths we need to find the x values corresponiding to the widths
            w_h = propr['width_heights'][i] # estimated height of the the width
            left_i = int(propr["left_ips"][i]) # index of the width on the left of the peak
            xmin = interpolate(w_h, res[left_i], res[left_i + 1], x[left_i], x[left_i + 1])
            right_i = int(propr["right_ips"][i]) # index of the width on the right of the peak
            xmax = interpolate(w_h, res[right_i], res[right_i + 1], x[right_i], x[right_i + 1])
            width = xmax - xmin 
            return height, x0, width 

        name = self["name"]
        print(f"Guessing initial parameters for {name}...")

        data = self["data"] 
        x,y = data.x,data.y


        # -----------------------------------------------------------------
        # R1 guessing
        # -----------------------------------------------------------------
        res = y 
        peaks, propr = sg.find_peaks(res, width = min_width)
        
        if(len(peaks) == 0):
            print("No peaks found.")
            self["fit_par"] = [0]*9
            self.update_function()
            return 

        R1 = get_peak()
        res = y - lorentzian(x,*R1) # calculate residual

        # -----------------------------------------------------------------
        # R2 guessing
        # -----------------------------------------------------------------
        peaks, propr = sg.find_peaks(res, width = min_width)
        
        if(len(peaks) == 0):
            print("R2 not found.")
            self["fit_par"] = list(R1) + [0]*6
            self.update_function()
            return 

        R2 = get_peak()
        res = res - lorentzian(x,*R2) # calculate residual

        # -----------------------------------------------------------------
        # backgroung guessing
        # -----------------------------------------------------------------
        bg = np.polyfit(x,res,2).tolist()[-1::-1]
        # bg = [0,0,0]


        self["fit_par"] = bg + list(R1 + R2)
        self.update_function()


    def fit(self):
        """
        Fit ruby spectrum. If fit fails, the original parameters are kept.
        """
        name = self["name"]
        data = self["data"]
        x,y = data.x, data.y
        print(f"Fitting {name}...")

        #fitting. If fit fails, the original parameters are kept.
        try:
            fit,_ = curve_fit(fitFunction, x, y, self["fit_par"])
            self["fit_par"] = fit
            self.update_function()
        except RuntimeError as er:
            print("Fit Failed!!!!!", er)

    def update_function(self):
        data = self["data"]
        par = self["fit_par"]
        x = data.x
        data["ftot"] = fitFunction(x,*par)
        data["bg"]= bg_quadratic(x,*par[:3])
        data["R2"]= lorentzian(x,*par[6:])
        data["R1"]= lorentzian(x,*par[3:6])

    #----plotting----
    def plot(self,normalize = None,**kwargs):
        """
        Plot the spectrum. *kwargs* are the same as matplotlib.pyplot.axis.plot()

        Parameters
        ----------
        key : int
            index of the spectrum to be plotted
        normalize : str, default None
            name of the column to be used for normalisation. If None the spectrum will not be normalized.
        **kwargs
            keyboard arguments for pandas.DataFrame.plot
        Returns
        -------
        plt.axes
            The plot axes
        """

        df = self["data"]
        if(normalize):
            df = normalize_spectrum(df, normalize, ignore= ["x"])
        if("ax" in kwargs):
            ax = kwargs.pop("ax")
        else:
            ax = plt.axes()
        ax.scatter(x = df["x"], y = df["y"], c = "r", **kwargs)
        ax.plot(df["x"], df["ftot"], c = "orange", **kwargs)
        ax.plot(df["x"], df["R1"],":", c = "orange", alpha = .3, **kwargs)
        ax.plot(df["x"], df["R2"],":", c = "orange", alpha = .3, **kwargs)
        ax.plot(df["x"], df["bg"],":", c = "gray", alpha = .3, **kwargs)
        ax.set(xlabel = "Raman Shift ($cm^{-1}$)",
            ylabel = "P (GPa)")


    def calc_P(self, shift0, laser_wl =  531.87e-9):

        if(isinstance(shift0,dict)):
            s0 = shift0.get(self["tockens"].get("Rubyid"))
            if(s0 == None):
                print("Rubyid not found in the shift0 dictionary")
            return s0
        else:
            s0 = shift0

        try:
            pos = self["fit_par"][4]
            if (abs(pos) <.1): return None
            wl = cm_inverse_to_wl(self["fit_par"][4],laser_wl)
        except KeyError:
            print("fit_par not found, consider guessing or fitting.")
        wl0 = cm_inverse_to_wl(s0,laser_wl)
        P = compute_P(wl,wl0)
        self["P"] = P
        return P
