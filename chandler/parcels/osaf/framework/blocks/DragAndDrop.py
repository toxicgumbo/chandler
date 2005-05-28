__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2003-2004 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"

import wx
import application.Globals as Globals
import osaf.contentmodel.ContentModel as ContentModel
import osaf.contentmodel.ItemCollection as ItemCollection
import time

"""
Overview of Drag and Drop infrastructure:

Two mixin classes are provided that should be mixed in to your widget class:
    Use DraggableWidget for things that export data through Drag
        and Drop or Cut and Copy.  
    Use DropReceiveWidget for things that import data through
        Drag and Drop or Paste.

Since most of Chandler data are Items, the interface is Item-centric by default.
    Widgets that mix in DraggableWidget should implement:
        SelectedItems() to return a list of items currently selected (Copy, Drag)
        DeleteSelection() to remove the selected items (Cut, Move)
    Widgets that mix in DropReceiveWidget should implement:
        AddItems() to insert a list of items (Paste, Drop)
        KindAcceptedByDrop() to specify the Kind of items allowed

It's possible to extend Drag and Drop for different kinds of items or deal with
    non-item data. You will want to override some of these methods: 
        CopyData() is used to get the selected data.
        KindsCreatedByDrag() implements the known Kinds of Items
        PasteData() is used to put the data into the selection.

wxWidgets level:
    * wx.DropSource - the window you are dragging from
    * wx.DropTarget - the window you are dragging to
    * wx.DataObject - the stuff being dragged
    * wx.DataFormat - the format of the DataObject
   
CPIA level:
    * DraggableWidget - class to mixin that makes widget a DropSource
    * DropReceiveWidget - class to mixin to makes widget a DropTarget
    * DropTarget - helper object connected to the DropReceiveWidget
       that converts wxWidget callbacks to CPIA DnD callbacks.
   
       Usually there's a one-to-one correspondence between your CPIA 
    DropReceiveWidget and the wx.DropTarget.  However, the Grid case
    is a little tricky; the wx.DropTarget is the Table, but the
    DropReceiveWidget is an individual Grid element (cell).  This
    allows the Table to decide if the drop should be onto itself
    or onto its Grid elements.  The default table implementation
    drops onto itself, but the Sidebar drops onto its Grid elements.
"""
   
   
class DraggableWidget (object):
    """
    Mixin class for widgets that are draggable.
    Note that you need to list the Mixin before the base class in your
      class declaration for the right method override behavior.
    """
    def DoDragAndDrop(self, copyOnly=None):
        """
        Do a Drag And Drop operation, given the data in the selection.
        If you want to disable Move, pass True for copyOnly.  Passing
           False allows the Move.  Passing None (the default) will
           allow the Move iff you have a DeleteSelection method.
        """
        if copyOnly is None:
            if not hasattr (self, 'DeleteSelection'):
                copyOnly = True
            else:
                copyOnly = False
        # create a DropSource, and put our custom data into it
        # @@@DLD get better icons for the DnD cursors
        iconParams = {'copy': self._DROP_ICON("ApplicationBarSync.png"),
                      'none': self._DROP_ICON("ApplicationDelete.png")}
        if not copyOnly:
            iconParams['move'] = self._DROP_ICON("ApplicationBarSend.png")
        dropSource = wx.DropSource(self, **iconParams)
        dataObject = self.CopyData()
        dropSource.SetData(dataObject)
        # capture the mouse, so mouse moves don't trigger activities
        # in other windows, like the sidebar.
        self.CaptureMouse()
        try:
            # drag and drop the DropSource.  Many callbacks happen here.
            result = dropSource.DoDragDrop(flags=wx.Drag_AllowMove)
        finally:
            if self.HasCapture():
                self.ReleaseMouse()
        # if we moved the item, instead of the usual copy, remove the original
        if not copyOnly and result == wx.DragMove:
            self.DeleteSelection()

    def _DROP_ICON(self, filename):
        # This macro from wxWidgets is going to be in wxPython soon.
        img = wx.GetApp().GetRawImage(filename)
        if wx.Platform == '__WXGTK__':
            return wx.IconFromBitmap(wx.BitmapFromImage(img))
        else:
            return wx.CursorFromImage(img)

    def CopyData(self):
        """
        Called to get a widget's data at the beginning of a Copy or DnD.
        Returns a wxDataObject variant for use in Drag and Drop, or Cut and Paste.
        This implementation deals with Items using UUIDs; override for 
            other kinds of data
        """
        dataObject = wx.DataObjectComposite()
        kindsCreatedByDrag = self.KindsCreatedByDrag()
        for dataKind, itemUUIDList in kindsCreatedByDrag.items():
            kindFormat = wx.CustomDataFormat(dataKind)
            customData = wx.CustomDataObject(kindFormat)
            customData.SetData(','.join(itemUUIDList))
            dataObject.Add(customData)
        return dataObject

    def KindsCreatedByDrag(self):
        """
        Return a dictionary of data that can be dragged from this item.
        Each entry has the Kind as its key, and a list of data (as UUIDs for items) for
          its value.
        Default is to export Item, ContentItem, and ItemCollection (assuming the
          item(s) really are these Kinds).
        """
        def _ExportItem(exportDict, key, itemUUID):
            if not exportDict.has_key(key):
                exportDict[key]=[]
            exportDict[key].append(str(itemUUID))

        exportDict = {}
        items = self.SelectedItems()
        for item in items:
            itemUUID = item.itsUUID
            _ExportItem(exportDict, "Item", itemUUID)
            if isinstance (item, ItemCollection.ItemCollection):
                _ExportItem(exportDict, "ItemCollection", itemUUID)
                # ItemCollections are not considered ContentItems to
                #   keep you from dragging them into themselves.
            elif isinstance (item, ContentModel.ContentItem):
                _ExportItem(exportDict, "ContentItem", itemUUID)
        return exportDict
    
    def CanCopy(self):
        return len(self.SelectedItems()) > 0

    def CanCut(self):
        if not hasattr (self, 'DeleteSelection'):
            return False
        return self.CanCopy()

    def Copy(self):
        clipboard = wx.TheClipboard
        if clipboard.Open():
            data = self.CopyData()
            clipboard.SetData(data)
            clipboard.Close()

    def Cut(self):
        self.Copy()
        try:
            self.DeleteSelection()
        except AttributeError:
            pass # doesn't know DeleteSelection()

class DropReceiveWidget (object):
    """
    Mixin class for widgets that want to receive drag and drop events.
    Note that you need to list the Mixin before the base class in your
      class declaration for the right method override behavior.
    """
    def __init__(self, *arguments, **keywords):
        super (DropReceiveWidget, self).__init__ (*arguments, **keywords)
        self.dropTarget = DropTarget(self)
        # If it is a grid, then we need to use grid window rather than self
        try:
            window = self.GetGridWindow()
        except AttributeError:
            window = self
        window.SetDropTarget(self.dropTarget)
        
    def KindAcceptedByDrop(self):
        """
          Override to define which kinds you allow to be dropped.
        """
        return "ContentItem" # Default is only ContentItems
    
    def OnRequestDrop(self, x, y):
        """
          Override this to decide whether or not to accept a dropped 
        item.
        """
        return True
        
    def AddItems(self, itemList):
        """
          Override this to add the dropped items to your widget.
        """
        pass
    
    def OnHover(self, x, y):
        """
          Override this to perform an action when a drag action is
        hovering over the widget.
        """
        pass

    def CanPaste(self):
        clipboard = wx.TheClipboard
        formatWeCanPaste = wx.CustomDataFormat(self.KindAcceptedByDrop())
        supportsOurKinds = clipboard.IsSupported(formatWeCanPaste)
        return supportsOurKinds

    def Paste(self):
        clipboard = wx.TheClipboard
        if clipboard.Open():
            acceptedFormat = wx.CustomDataFormat(self.KindAcceptedByDrop())
            dataToPaste = wx.CustomDataObject(acceptedFormat)
            if clipboard.GetData(dataToPaste):
                self.PasteData(dataToPaste)
            clipboard.Close()

    def PasteData(self, data):
        """
        Paste the supplied data into ourself, either
        because of a Paste operation, or a Drag and Drop.
        Assumes that the data are Items, override for other kinds.
        """
        itemUUIDList = data.GetData()
        itemList = []
        for itemUUID in itemUUIDList.split(','):
            item = self.blockItem.findUUID(itemUUID)
            if item is not None:
                itemList.append(item)
        if len(itemList)>0:
            self.AddItems(itemList)
            
class DropTarget(wx.DropTarget):
    """
        An instance of this class is a helper object that associates
        a wx.DropTarget with a receiver - a DropReceiveWidget.
        Usually these are the same object, but for Grids, they are not;
        the DropTarget is the Table, and the Grid element is the receiver.
    """
    def __init__(self, receiver):
        super (DropTarget, self).__init__ ()
        self.receiver = receiver
        # declare the kind of data we'll accept
        kindAllowed = receiver.KindAcceptedByDrop()

        self.data = wx.CustomDataObject(wx.CustomDataFormat(kindAllowed))
        self.kindAllowed = kindAllowed # @@@DLD - remove
        self.SetDataObject(self.data)
    
    def OnDrop(self, x, y):
        return self.receiver.OnRequestDrop(x, y)
    
    def OnData(self, x, y, d):
        if self.GetData():
            dataToPaste = self.data
            self.receiver.PasteData(dataToPaste)
        return d
    
    def OnDragOver(self, x, y, d):
        self.receiver.OnHover(x, y)
        return d
        
    def OnEnter(self, x, y, d):
        self.enterTime = time.time()
        return d

    def OnLeave(self):
        try:
            leaveMethod = self.receiver.OnHoverLeave
        except AttributeError:
            pass
        else:
            leaveMethod()

