#!/usr/bin/env python

# Teardrop for pcbnew using filled zones
# This is the action plugin interface
# (c) Niluje 2019 thewireddoesntexist.org
#
# Based on Teardrops for PCBNEW by svofski, 2014 http://sensi.org/~svo

import wx
import os
from pcbnew import ActionPlugin, GetBoard

from .teardrop_dialog import InitTeardropDialog

class TeardropPlugin(ActionPlugin):
    """Class that gathers the actionplugin stuff"""
    def defaults(self):
        self.name = "Teardrops"
        self.category = "Modify PCB"
        self.description = "Manages teardrops on a PCB"
        self.icon_file_name = os.path.join(os.path.dirname(__file__), 'teardrops.png')
        self.show_toolbar_button = True

    def Run(self):
        InitTeardropDialog(GetBoard())
