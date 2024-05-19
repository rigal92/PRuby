import wx
from wx import grid
from pubsub import pub
import sys

from pruby.core.pruby import PRuby



class PressureFrame(wx.Frame):

    """
    Frame that will contain a grid that summarize pressures.
    """
    def __init__(self,parent,data,title = "Pressure Table",size = (800,600)):
        
        self.data = data
        # initialize the frame 
        wx.Frame.__init__(self,parent,title = title, size = size )

        #initialize the grid 
        self.pgrid = grid.Grid(self)
        table = PTable(data)
        self.pgrid.SetTable(table,True)#True is needed to avoid segmentation fault. It takes care of cleaning somehow.

        self.mergeText = wx.StaticText(self,label = f"Columns combine")
        self.mergeText.SetFont(wx.Font(12,wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False))

        self.computeButton = wx.Button(self, label="Compute",size = (100,40))
        self.checkboxes()
        
        self.layout()

        #events
        self.Bind(wx.EVT_BUTTON, self.onComputeButton,self.computeButton)




    def layout(self):
        """
        Define frame's layout 
        """
        sideSizer = wx.BoxSizer(wx.VERTICAL)
        sideSizer.Add(self.mergeText,0)
        for i in self.groupOptions:
            sideSizer.Add(i,0)
        sideSizer.Add(self.computeButton,0)


        mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        mainSizer.Add(self.pgrid,1,wx.EXPAND)
        mainSizer.Add(sideSizer,0,wx.EXPAND)


        self.SetSizer(mainSizer)


    def checkboxes(self):
        """
        Define checkboxes to use for mean P computing from DataFrame column names. name and P are excluded from the combination options.
        """ 
        self.groupOptions = [wx.CheckBox(self, label=i) for i in self.data.columns.drop(["name","P"],errors = "ignore")]



    def grouping(self):
        """
        group pressure by the names that are active in the checkbox.
        
        Parameters
        --------------
        None

        Returns
        --------------
        pd.DataFrame:
            A new dataframe grouped

        """

        #get the active checkboxes labels 
        active = [x.GetLabelText() for x in self.groupOptions if x.IsChecked()]

        #grouping and flatening indexes
        df = self.data.groupby(active,as_index = False).agg(["mean","std"])
        df.columns = df.columns.map("_".join)
        df = df.reset_index()
        return df


    def onComputeButton(self,event):
        """
        Compute grouping when pressed and creates a new table frame.
        """
        df = self.grouping()
        pTable = PressureFrame(None,df,title = "Pressures",size = (600,400))
        pTable.Show()





class PTable(grid.GridTableBase):
    """
    Abstract table containing the pressure data. 
    It describs the methods to convert the DataFrame output of PRuby.tidy() to wx.grid.Grid.
    """

    def __init__(self,data):
        grid.GridTableBase.__init__(self)
        self.data = data
        self.colnames = data.columns
        self.ncols = len(self.colnames)
        self.nrows = len(data)

    #Overdriving methods in order to be able to read the pandas.DataFrame and convert it to a virtual table fo wx
    #Initialisation will call the getters 
    def GetNumberRows(self):
        return self.nrows

    def GetNumberCols(self):
        return self.ncols

    def GetColLabelValue(self, col):
            return self.colnames[col].capitalize()

    def GetValue(self, row, col):
        return str(self.data.iloc[row, col])

    def SetValue(self, row, col,value):
        self.data.iloc[row, col] = value




