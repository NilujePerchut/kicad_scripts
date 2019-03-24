# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version Oct 26 2018)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc

###########################################################################
## Class teardrop_gui
###########################################################################

class teardrop_gui ( wx.Dialog ):

	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Teardrops", pos = wx.DefaultPosition, size = wx.DefaultSize, style = wx.CAPTION|wx.CLOSE_BOX|wx.DEFAULT_DIALOG_STYLE )

		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

		bvs_main = wx.BoxSizer( wx.VERTICAL )

		rbx_actionChoices = [ u"Set Teardrops", u"Remove All Teardrops" ]
		self.rbx_action = wx.RadioBox( self, wx.ID_ANY, u"Action", wx.DefaultPosition, wx.DefaultSize, rbx_actionChoices, 1, wx.RA_SPECIFY_ROWS )
		self.rbx_action.SetSelection( 0 )
		bvs_main.Add( self.rbx_action, 0, wx.ALL, 5 )

		gs_params = wx.GridSizer( 0, 2, 0, 0 )

		self.st_hpercent = wx.StaticText( self, wx.ID_ANY, u"Horizontal percent", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.st_hpercent.Wrap( -1 )

		gs_params.Add( self.st_hpercent, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )

		self.sp_hpercent = wx.SpinCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 100, 30 )
		gs_params.Add( self.sp_hpercent, 0, wx.ALL|wx.SHAPED, 5 )

		self.st_vpercent = wx.StaticText( self, wx.ID_ANY, u"Vertical percent", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.st_vpercent.Wrap( -1 )

		gs_params.Add( self.st_vpercent, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )

		self.sp_vpercent = wx.SpinCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 100, 70 )
		gs_params.Add( self.sp_vpercent, 0, wx.ALL|wx.SHAPED, 5 )

		self.st_nbseg = wx.StaticText( self, wx.ID_ANY, u"Number of segments", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.st_nbseg.Wrap( -1 )

		gs_params.Add( self.st_nbseg, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.ALL, 5 )

		self.sp_nbseg = wx.SpinCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 2, 100, 10 )
		gs_params.Add( self.sp_nbseg, 0, wx.ALL|wx.SHAPED, 5 )


		bvs_main.Add( gs_params, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALL|wx.EXPAND|wx.SHAPED, 5 )

		bhs_modal = wx.BoxSizer( wx.HORIZONTAL )

		bhs_modal.Add( ( 0, 0), 1, wx.EXPAND, 5 )

		self.but_cancel = wx.Button( self, wx.ID_ANY, u"Cancel", wx.DefaultPosition, wx.DefaultSize, 0 )
		bhs_modal.Add( self.but_cancel, 0, wx.ALIGN_RIGHT|wx.EXPAND, 5 )

		self.but_ok = wx.Button( self, wx.ID_ANY, u"Ok", wx.DefaultPosition, wx.DefaultSize, 0 )
		bhs_modal.Add( self.but_ok, 0, 0, 5 )


		bvs_main.Add( bhs_modal, 0, wx.EXPAND, 5 )


		self.SetSizer( bvs_main )
		self.Layout()
		bvs_main.Fit( self )

		self.Centre( wx.BOTH )

	def __del__( self ):
		pass


