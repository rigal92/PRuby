import wx
import sys
from pruby.graphics.mainFrame import MainFrame


def main():
    app = wx.App()
    frame = MainFrame(None)
    app.MainLoop()


sys.exit(main())