import wx
from wx import grid
import sys

import numpy as np
import matplotlib

import matplotlib.pyplot as plt

from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg as NavigationToolbar
from pubsub import pub


#local
from pruby.core.pruby import PRuby
from pruby.graphics.pressureFrame import PressureFrame




class MainFrame(wx.Frame):
    def __init__(self,parent, dpi = None):
        
        self.dirname=''
        self.pruby = PRuby()

        wx.Frame.__init__(self,parent)

        #----------visual elements----------------
        # Setting up the menu.
        filemenu= wx.Menu()
        menuOpen = filemenu.Append(wx.ID_OPEN, "&Open"," Open a file to edit")
        menuExport = filemenu.Append(wx.ID_ANY, "&Export Pressure","Export pressure table")
        menuExit = filemenu.Append(wx.ID_EXIT,"E&xit"," Terminate the program")

        # Creating the menubar.
        menuBar = wx.MenuBar()
        menuBar.Append(filemenu,"&File") # Adding the "filemenu" to the MenuBar
        self.SetMenuBar(menuBar)  # Adding the MenuBar to the Frame content.

        #mpl image container 
        self.fig = Figure((6.0, 5.0),dpi = dpi)
        self.canvas = FigureCanvas(self, -1, self.fig)
        self.axes = self.fig.add_subplot(111)
        #mpl navigation
        self.toolbar = NavigationToolbar(self.canvas)
        self.toolbar.Realize()

        #list
        self.browserList=wx.ListCtrl(self,-1,style = wx.LC_REPORT|wx.BORDER_SUNKEN,size = (300,-1))
        self.browserList.InsertColumn(0, 'File',width = 300)

        #Notebook 
        self.parEditor = parNotebook(self)
        
        #layout
        self.layout()
        self.Show(True)
        
        #--------Events--------------------
        self.Bind(wx.EVT_MENU, self.OnOpen, menuOpen)
        self.Bind(wx.EVT_MENU, self.OnExport, menuExport)
        self.Bind(wx.EVT_MENU, self.OnExit, menuExit)

        self.Bind(wx.EVT_LIST_ITEM_FOCUSED, self.onListBox, self.browserList)


        #----------------listener------------------
        pub.subscribe(self.mod_fitPar, "fitTable")
        pub.subscribe(self.calcP, "calcP")
        pub.subscribe(self.showPTable, "showPTable")




    def layout(self):
        # #-----------sizer-----------------
        # sizer = wx.BoxSizer(wx.HORIZONTAL)
        # sizer.Add(self.guessButton, 1, wx.EXPAND)
        # sizer.Add(self.fitButton, 1, wx.EXPAND)


        sizer2 = wx.BoxSizer(wx.VERTICAL)
        sizer2.Add(self.toolbar, 0, wx.LEFT | wx.EXPAND)
        sizer2.Add(self.canvas, 1, wx.EXPAND)
        sizer2.Add(self.parEditor,0,wx.EXPAND)


        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3.Add(sizer2,1,wx.EXPAND)
        sizer3.Add(self.browserList,0,wx.EXPAND)
        
        self.SetSizerAndFit(sizer3)

        







    #---------------event functions----------------
    def getSelected(self):
        return [self.browserList.IsSelected(i) for i in range(self.browserList.GetItemCount())]


    def fitEvent(self,event):
        l = self.getSelected()
        for i,t in enumerate(l):
            if(t):
                self.pruby[i].fit()
        self.Update()


    def guessEvent(self,event):
        l = self.getSelected()
        height = self.parEditor.guessPage.height
        if(not height): height=None                        #automatic mode
        FWHM = self.parEditor.guessPage.FWHM
        for i,t in enumerate(l):
            if(t):
                self.pruby[i].guess(height,FWHM)
        self.Update()

    def showPTable(self):
        df = self.pruby.tidy()
        pTable = PressureFrame(None,df,title = "Pressures",size = (600,400))
        pTable.Show()



    




    def OnOpen(self,e):
        """ Open a file"""
        dlg = wx.FileDialog(self, "Choose a file", self.dirname, "", "*.*", wx.FD_MULTIPLE)
        if dlg.ShowModal() == wx.ID_OK:
            filenames = dlg.GetFilenames()
            self.dirname = dlg.GetDirectory()
            for filename in filenames:
                self.browserList.InsertItem(sys.maxsize,filename)
                filename = self.dirname + "/" + filename
                self.pruby.add_spectra(files = [filename])
        dlg.Destroy()

    def OnExport(self,e):
        """ Export a pressure file"""
        with wx.FileDialog(self, "Choose a file name", self.dirname, "", "*.txt", wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as dlg:

            if dlg.ShowModal() == wx.ID_CANCEL:
                return
            path = dlg.GetPath()
            df = self.pruby.tidy()
            df.to_csv(path,index = None,sep = "\t")


    def OnExit(self,e):
        self.Close(True)  # Close the frame.

    def plot(self,data):
        self.axes.clear()
        data.plot(ax=self.axes)
        self.canvas.draw()


    def onListBox(self, event):
        self.index_selected = event.GetIndex()
        self.plot(self.pruby[self.index_selected])
        self.parEditor.Update(self.pruby[self.index_selected])


    #---------------listener event functions----------------
    def mod_fitPar(self,arg1,col, row):
        """
        Modify the pruby element when modification in the fit table are made 
        """
        self.pruby[self.browserList.GetFocusedItem()]["fit_par"][col * 3 +row] = arg1
        self.pruby[self.browserList.GetFocusedItem()].update_function()
        self.Update()

    def calcP(self,val,laser):
        l = self.getSelected()
        for i,t in enumerate(l):
            if(t):
                self.pruby[i].calc_P(val,laser)
                self.parEditor.Update(self.pruby[i])
    #DEPRECATED only act on one element
    # def calcP(self,val,laser): 
    #     self.pruby[self.browserList.GetFocusedItem()].calc_P(val,laser)
    #     self.parEditor.Update(self.pruby[self.browserList.GetFocusedItem()])
        


    def Update(self):
        index = self.browserList.GetFocusedItem()
        self.plot(self.pruby[index])
        self.parEditor.Update(self.pruby[index])





class fitPanel(wx.Panel):
    """
    Class describing the panel used for fitting
    """
    def __init__(self,parent):
        wx.Panel.__init__(self,parent)

        self.parGrid = grid.Grid(self)        
        self.parGrid.CreateGrid(3, 3)
        self.parGrid.SetColFormatFloat(0,100,2)
        self.parGrid.SetColFormatFloat(1,100,2)
        self.parGrid.SetColFormatFloat(2,100,2)
        self.parGrid.SetColLabelValue(0,"BG")        
        self.parGrid.SetColLabelValue(1,"R1")
        self.parGrid.SetColLabelValue(2,"R2")
        self.fitButton =wx.Button(self, label="Fit",size = (100,40))
        
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.parGrid, 1, wx.EXPAND)
        sizer.Add(self.fitButton, 0)

        self.SetSizer(sizer)
        self.Bind(wx.EVT_BUTTON, parent.parent.fitEvent,self.fitButton)
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.cellChange,self.parGrid)


    def cellChange(self,event):
        
        col = event.GetCol()
        row = event.GetRow()
        val = float(self.parGrid.GetCellValue(row,col))

        pub.sendMessage('fitTable', arg1=val,col= col, row = row)


    def Update(self,pars):
        self.parGrid.SetCellValue(0,0,str(pars[0]))
        self.parGrid.SetCellValue(1,0,str(pars[1]))
        self.parGrid.SetCellValue(2,0,str(pars[2]))
        self.parGrid.SetCellValue(0,1,str(pars[3]))
        self.parGrid.SetCellValue(1,1,str(pars[4]))
        self.parGrid.SetCellValue(2,1,str(pars[5]))
        self.parGrid.SetCellValue(0,2,str(pars[6]))
        self.parGrid.SetCellValue(1,2,str(pars[7]))
        self.parGrid.SetCellValue(2,2,str(pars[8]))



class guessPanel(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self,parent)

        self.height = None
        self.FWHM = 5

        self.guessButton =wx.Button(self, label="guess",size = (100,40))

        self.t1 = wx.StaticText(self,label = "Height threshold (0 == auto)") 
        self.sc1 = wx.SpinCtrl(self, min = 0, max = int(10e8), initial = 0, size = (200,40))
        self.sc1.Bind(wx.EVT_SPINCTRL, self.OnSpinChange)

        self.t2 = wx.StaticText(self,label = "FWHM threshold") 
        self.sc2 = wx.SpinCtrl(self, min = 1, max = 500, initial = self.FWHM,size = (200,40))
        self.sc2.Bind(wx.EVT_SPINCTRL, self.OnSpinChange)

        self.layout()
        self.Bind(wx.EVT_BUTTON, parent.parent.guessEvent,self.guessButton)

    def layout(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(0, 5, 0)
        sizer.Add(self.t1,1)
        # sizer.Add(self.t1, .8)
        # sizer.Add(self.sc1, 1.5)
        sizer.Add(self.sc1, 2)
        sizer.Add(0, 5, 0)
        # sizer.Add(self.t2, .8)
        sizer.Add(self.t2, 1)
        # sizer.Add(self.sc2, 1.5)
        sizer.Add(self.sc2, 2)
        sizer.Add(0, 5, 0)
        sizer.Add(self.guessButton, 0)
        self.SetSizer(sizer)





    def OnSpinChange(self,event):
        obj = event.GetEventObject()
        val = obj.GetValue()

        if obj.GetId() == self.sc1.GetId():
            self.height = val
        else:
            self.FWHM = val


class PPanel(wx.Panel):
    def __init__(self,parent):
        wx.Panel.__init__(self,parent)
        self.p0Dict = {}


        self.lab = wx.StaticText(self,label = "Raman Shift at P00 (cm-1)")
        self.w0Text = wx.SpinCtrlDouble(self, min = 0., max = 100000,  inc = .01, initial = 0., size = (200,40))
  
        self.lab2 = wx.StaticText(self,label = "Laser wl (nm)")
        self.laser = wx.SpinCtrlDouble(self, min = 0., max = 2000, inc = .01, initial = 531.87, size = (200,40))
  

        self.P = wx.StaticText(self,label = f"P = 0 GPa",size = (200,100),style = wx.ALIGN_CENTRE_HORIZONTAL)
        self.P.SetFont(wx.Font(16,wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False))

        # self.w0List=wx.ListCtrl(self,-1,style = wx.LC_REPORT|wx.BORDER_SUNKEN,size = (300,100))
        # self.w0List.InsertColumn(0, 'Ruby Id',width = 100)
        # self.w0List.InsertColumn(1, 'Value',width = 200)


        
        self.pButton =wx.Button(self, label="Compute P",size = (100,40))
        self.tButton =wx.Button(self, label="Show Table",size = (100,40))
        self.Bind(wx.EVT_BUTTON, self.onPButton,self.pButton)
        self.Bind(wx.EVT_BUTTON, self.onTButton,self.tButton)
        self.layout()

    def layout(self):
        sizerV = wx.BoxSizer(wx.VERTICAL)
        sizerV.Add(0, 5, 0)
        sizerV.Add(self.lab, 1)
        sizerV.Add(self.w0Text, 2)
        sizerV.Add(0, 5, 0)
        sizerV.Add(self.lab2, 1)
        sizerV.Add(self.laser, 2)
        sizerV.Add(0, 5, 0)
        sizerV.Add(self.pButton, 0)

        sizerV2 = wx.BoxSizer(wx.VERTICAL)
        sizerV2.Add(0,0,1,wx.EXPAND)
        sizerV2.Add(self.P, 0)
        sizerV2.Add(0,0,1,wx.EXPAND)

        sizerV3 = wx.BoxSizer(wx.VERTICAL)
        sizerV3.Add(0,0,1,wx.EXPAND)#add two spacers of undifined equal size to center the button (w,h,ratio,expand)
        sizerV3.Add(self.tButton, 0)
        sizerV3.Add(0,0,1,wx.EXPAND)


        sizerH = wx.BoxSizer(wx.HORIZONTAL)
        sizerH.Add(sizerV, 1,wx.EXPAND)
        sizerH.Add(sizerV2, 1,wx.EXPAND)
        sizerH.Add(sizerV3, 0,wx.EXPAND)

        self.SetSizer(sizerH)

    def onPButton(self,event):
        w0 = self.w0Text.GetValue()
        laser = self.laser.GetValue() * 1e-9
        pub.sendMessage('calcP', val=w0 , laser = laser)


    def onTButton(self,event):
        pub.sendMessage('showPTable')


    def Update(self,pars):
        pass





class parNotebook(wx.Notebook):

    def __init__(self,parent):
        self.parent = parent
        self.data = None

        wx.Notebook.__init__(self,parent)
        self.fitPage = fitPanel(self) 
        self.guessPage = guessPanel(self)
        self.PPage = PPanel(self)
        self.AddPage(self.fitPage,"Fit") 
        self.AddPage(self.guessPage,"Guess") 
        self.AddPage(self.PPage,"Pressure") 

    def Update(self, data):
        P = data.get("P")
        self.data = data 
        self.fitPage.Update(data["fit_par"])
        self.PPage.P.SetLabel(f"P = {P:.2f} GPa") if P !=None else self.PPage.P.SetLabel(f"P = N.C.")



