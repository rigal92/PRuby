import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os 

#local imports 
import pruby.core.pspectrum as pspec
from pruby.mathfunc.conversions import cm_inverse_to_wl,compute_P
from pruby.mathfunc.math_def import *



class PRuby(list):

	def __init__(self):
		self.RubyIds = set()
		super().__init__(self)



	def __getitem__(self, index):
		if(type(index) == int):
			return super().__getitem__(index)
		else:
			return PRuby(super().__getitem__(index))

	def copy(self):
		return PRuby(super().copy())

	def add_spectra(self, files = [], folder = ""):
		if(folder): 
			files += os.listdir(folder)
			if(not folder.endswith("/")): 
				folder += "/"
			files = [folder + x for x in files]
		
		for f in files:
			df = pd.read_table(f, comment="#", header = None,encoding_errors="replace")
			#assign x and y names to the first two columns, then zi
			df.columns = ["x","y"] + [f"z{x}" for x in range(len(df.columns) -2 )]

			#assigne the name of the file as a name for the event cropping folder and filetype 
			name = f.split("/")[-1].split(".")[0] 
			if (not name): name = f

			#acreates PData elements 
			data = pspec.PData(df,name = name)
			data.guess()

			self.append(data)
			try:
				self.RubyIds.add(data["tokens"]["Rubyid"])
			except:
				pass

	# def get_P(self, shift0 = 4390, laser_wl =  531.87e-9):
	# 	#calculate P
	# 	for data in self:
	# 		wl = cm_inverse_to_wl(data["fit_par"][7],laser_wl)
	# 		wl0 = cm_inverse_to_wl(shift0,laser_wl)
	# 		P = compute_P(wl,wl0)
	# 		data["P"] = P


	def plot_stack(self,factor = 1, normalize = "y", **kwargs):
		"""
		Plot all the spectra stacked, separated by factor. 
		"""
		ax = plt.axes()
		df_copy = self.copy()
		for i in range(len(self)):
			shift = i*factor
			if(normalize): df_copy[i]["data"] =  normalize_spectrum(df_copy[i]["data"], normalize, ignore = ["x"])
			df_copy[i]["data"].loc[:,"y":] += shift 
			df_copy[i].plot(ax =ax)

		return ax 


	def tidy(self):
		"""
		Returns a pd.DataFrame with all the P values and their attributes.  
		"""
		names = [x["name"] for x in self]
		Ps = [x["P"] for x in self]
		tokens = self.getTokens()
		return pd.concat([pd.DataFrame({"name" : names,"P" : Ps}),tokens],axis = 1 ) 
	
	def getTokens(self):
		"""
		Creates a pandas.DataFrame of tokens extracted by the strings in names.
		If Pid is present as a token it is placed as the first column.
		"""
		df = pd.DataFrame([i["tokens"] for i in self])
		try:
			df = pd.concat([df.pop("Pid"),df],axis = 1)
		except:
			pass
		return df 

		

def main():
	pass


#-----------------testing-------------------------

if __name__ == '__main__':
	r = PRuby()
	r.add_spectra(["Tests/R3_P00_loaded.txt"])
	# r.add_spectra(folder = "Tests/Experiment/",laser_wl =  532e-9)
	# r.add_spectra(folder = "Tests")
	for i in r:
		i.fit()
	# r.plot(1)
	# plt.show()
	# r.plot_stack()
	# plt.show()

	# df = r[0]["data"]