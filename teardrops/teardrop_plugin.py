#!/usr/bin/env python

# Teardrop for pcbnew using filled zones
# This is the action plugin interface
# (c) Niluje 2017 thewireddoesntexist.org
#
# Based on Teardrops for PCBNEW by svofski, 2014 http://sensi.org/~svo

import wx
from pcbnew import ActionPlugin, GetBoard

from teardrops.teardrop_dialog import InitTeardropDialog

class TeardropPlugin(ActionPlugin):
    """Class that gathers the actionplugin stuff"""
    def defaults(self):
        self.name = "Teardrops"
        self.category = "Modify PCB"
        self.description = "Manages teardrops on a PCB"

    def Run(self):
        InitTeardropDialog(GetBoard())
