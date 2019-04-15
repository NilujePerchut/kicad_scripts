#!/usr/bin/env python

# Teardrop for pcbnew using filled zones
# This is the plugin WX dialog
# (c) Niluje 2019 thewireddoesntexist.org
#
# Based on Teardrops for PCBNEW by svofski, 2014 http://sensi.org/~svo

import wx
from teardrops.teardrop_gui import teardrop_gui
from teardrops.td import SetTeardrops, RmTeardrops, __version__

class TeardropDialog(teardrop_gui):
    """Class that gathers all the Gui control"""

    def __init__(self, board):
        """Init the brand new instance"""
        super(TeardropDialog, self).__init__(None)
        self.board = board
        self.SetTitle("Teardrops (v{0})".format(__version__))
        self.rbx_action.Bind(wx.EVT_RADIOBOX, self.onAction)
        self.Bind(wx.EVT_CLOSE, self.onCloseWindow)
        self.but_cancel.Bind(wx.EVT_BUTTON, self.onCloseWindow)
        self.but_ok.Bind(wx.EVT_BUTTON, self.onProcessAction)

    def onAction(self, e):
        """Enables or disables the parameters elements"""
        params_group = [self.st_hpercent, self.sp_hpercent, self.st_vpercent,
                        self.sp_vpercent, self.st_nbseg, self.sp_nbseg]
        for i, el in enumerate(params_group):
            if self.rbx_action.GetSelection() == 0:
                el.Enable()
            else:
                el.Disable()

    def onProcessAction(self, event):
        """Executes the requested action"""
        if self.rbx_action.GetSelection() == 0:
            count = SetTeardrops(self.sp_hpercent.GetValue(),
                                 self.sp_vpercent.GetValue(),
                                 self.sp_nbseg.GetValue(),
                                 self.board)
            wx.MessageBox("{0} Teardrops inserted".format(count))
        else:
            count = RmTeardrops(pcb=self.board)
            wx.MessageBox("{0} Teardrops removed".format(count))
        self.Destroy()

    def onCloseWindow(self, event):
        self.Destroy()


def InitTeardropDialog(board):
    """Launch the dialog"""
    tg = TeardropDialog(board)
    tg.Show(True)
    return tg
