__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2002 Open Source Applications Foundation"
__license__ = "http://osafoundation.org/Chandler_0.1_license_terms.htm"


from wxPython.wx import *
from application.Application import app
from persistence import Persistent
from persistence.dict import PersistentDict
import application.Application

class SideBar(Persistent):
    """
      SideBar is the side bar in the ChandlerWindow and is the model
    counterpart of the wxSideBar view object (see below)..
    """
    def __init__(self):
        """
          sideBarURLTree is a dict mapping what this instance of SideBar
        has visible to the application's full URLTree.  The dict is a 
        tree of dicts that contain extra data specific to this instance of
        SideBar (like which levels are expanded).
        """
        self.sideBarURLTree = PersistentDict()
        self.ignoreChangeSelect = false
        self.ignoreExpand = false
        self.ignoreCollapse = false
        application.Application.app.model.URLTree.RegisterSideBar(self)
                
    def SynchronizeView(self):
        """
          Notifies the window's wxPython counterpart that they need to
        synchronize themselves to match their peristent model counterpart.
        Whenever the application's URLTree is changed, the sidebar is
        notified with the SynchronizeView to update the sideBarURLTree
        to reflect changes
        """
        if not app.association.has_key(id(self)):
            wxWindow = wxSideBar ()
            app.association[id(self)] = wxWindow
        else:
            wxWindow = app.association[id(self)]
        
        if not hasattr(wxWindow, 'root'):
            wxWindow.root = wxWindow.AddRoot('Root')
        self.__UpdateURLTree(self.sideBarURLTree, '', wxWindow.root)

    def __UpdateURLTree(self, sideBarLevel, parentURL, parentItem):
        """
          Synchronizes the sideBar's URLTree with the application's
        URLTree.  The sideBar only stores a dict mapping visible
        items in the sideBar to their instances in the application.
        """
        
        wxWindow = app.association[id(self)]
        urlList = app.model.URLTree.GetURLChildren(parentURL)
        for name in urlList:
            url = parentURL + name
            urlNoCase = url.lower()
            parcel = app.model.URLTree.URLExists(url)
            children = app.model.URLTree.GetURLChildren(url)
            hasChildren = len(children) > 0            

            if not sideBarLevel.has_key(name):
                itemId = wxWindow.AppendItem(parentItem, name)
                wxWindow.urlDictMap[urlNoCase] = itemId
                wxWindow.SetItemHasChildren(itemId, hasChildren)
                sideBarLevel[name] = URLTreeEntry(parcel, false, 
                                                  PersistentDict(),
                                                  false)
            else:
                if not wxWindow.urlDictMap.has_key(urlNoCase):
                    itemId = wxWindow.AppendItem(parentItem, name)
                    wxWindow.urlDictMap[urlNoCase] = itemId
                else:
                    itemId = wxWindow.urlDictMap[urlNoCase]
                wxWindow.SetItemHasChildren(itemId, hasChildren)
                if sideBarLevel[name].isOpen:
                    self.__UpdateURLTree(sideBarLevel[name].children, 
                                         url + '/', itemId)
                    self.ignoreExpand = true
                    wxWindow.Expand(itemId)
                    self.ignoreExpand = false
                else:
                    self.ignoreCollapse = true
                    wxWindow.Collapse(itemId)
                    self.ignoreCollapse = false
            sideBarLevel[name].isMarked = true
        # Now we clean up items that exist in the dict, but not 
        # in the app's URLTree
        for key in sideBarLevel.keys():
            urlToDelete = parentURL + key
            urlToDelete = urlToDelete.lower()
            item = sideBarLevel[key]
            if not item.isMarked:
                if wxWindow.urlDictMap.has_key(urlToDelete):
                    itemId = wxWindow.urlDictMap[urlToDelete]
                    wxWindow.Delete(itemId)
                    del wxWindow.urlDictMap[urlToDelete]
                del sideBarLevel[key]
            else:
                item.isMarked = false
    
    def SelectURL(self, url):
        """
          Selects the proper url when we have navigated to a different one
        via some tool other than the sideBar.
        """
        # if the url is remote, don't do this
        if app.wxMainFrame.IsRemoteURL():
            return
        
        wxWindow = app.association[id(self)]
        self.ignoreChangeSelect = true
        # FIXME:  If the user types a valid url of an item that has never been
        # displayed in the SideBar (because one of it's ancestors is collapsed)
        # then that item will not yet be in the dict.  We have to recurse
        # through the appURLTree to find the proper item and expand its
        # ancestors if necessary.
        try:
            wxWindow.SelectItem(wxWindow.urlDictMap[url.lower()])
        except:
            pass
        self.ignoreChangeSelect = false

    def ExpandURL(self, url):
        """
          Expands the item representing the given url.  Will also expand 
        any ancestors of the item representing the supplied url.  Returns 
        true if the expansion was successful, false otherwise.
        """
        wxWindow = app.association[id(self)]
        return wxWindow.ExpandURL(url)
        
    def CollapseURL(self, url):
        """
          Collapses the item representing the given url.  Returns true if
        the collapse was successful, false otherwise.
        """
        wxWindow = app.association[id(self)]
        return wxWindow.CollapseURL(url)
    
    def SetURLColor(self, url, color):
        """
          Changes the color of the item representing the url.       
        Returns true if the color was successfully set, false otherwise.
        """
        wxWindow = app.association[id(self)]
        return wxWindow.SetURLColor(url, color)

    def SetURLBold(self, url, isBold=true):
        """
          Sets whether or not the item representing the url should be bold.
        Returns true if the bold state of the item was successfully set,
        false otherwise.
        """
        wxWindow = app.association[id(self)]
        return wxWindow.SetURLBold(url, isBold)
    
        
class URLTreeEntry(Persistent):
    """
      URLTreeEntry is just a container class for items inserted into the
    SideBar's URLTree dictionary.
    """
    def __init__(self, instance, isOpen, children, isMarked):
        self.instance = instance
        self.isOpen = isOpen
        self.children = children
        self.isMarked = isMarked        

class wxSideBar(wxTreeCtrl):
    def __init__(self):
        """
          wxSideBar is the view counterpart to SideBar. Wire up the wxWindows
        object behind the wxPython object. wxPreFrame creates the wxWindows
        C++ object, which is stored in the this member. _setOORInfo store a
        back pointer in the C++ object to the wxPython object.
        """
        value = wxPreTreeCtrl ()
        self.this = value.this
        self._setOORInfo (self)
        """
          Check to see if we've already created the persistent counterpart,
        if not create it, otherwise get it. Finally add it to the association.
        """
        if not app.model.mainFrame.__dict__.has_key('SideBar'):
            self.model = SideBar()
            app.model.mainFrame.SideBar = self.model
        else:
            self.model = app.model.mainFrame.SideBar
        """
           The model persists, so it can't store a reference to self, which
        is a wxApp object. We use the association to keep track of the
        wxPython object associated with each persistent object.
        """
        app.association[id(self.model)] = self
        self.urlDictMap = {}
        """
           There isn't a EVT_DESTROY function, so we'll implement it do
        what the function would have done.
        """
        EVT_WINDOW_DESTROY (self, self.OnDestroy)
        EVT_TREE_SEL_CHANGED(self, self.GetId(), self.OnSelChanged)
        EVT_TREE_ITEM_EXPANDING(self, self.GetId(), self.OnItemExpanding)
        EVT_TREE_ITEM_COLLAPSING(self, self.GetId(), self.OnItemCollapsing)
        
    def OnSelChanged(self, event):
        """
          Whenever the selection changes in the sidebar we must update the
        current view to visit the proper url.  Right now, it only allows you
        to select parcels, and not visit specific url's, but that is only
        temporary.
        """
        if (not self.model.ignoreChangeSelect) and hasattr(app, 'wxMainFrame'):
            clickedItem = event.GetItem()
            # If the selection change is generated by a right click, we get events
            # that have items without text.  We don't want to respond to these 
            # selection changes.
            if self.GetItemText(clickedItem) != "":
                url = self.BuildURLFromItem(clickedItem)
                app.wxMainFrame.GoToURL(url)
        
    def BuildURLFromItem(self, item, url = ""):
        """
          Given an item in the SideBar hierarchy, builds up that item's url
        and returns it.
        """
        if self.GetRootItem() == item:
            return url
        newURL = self.GetItemText(item)
        if len(url) != 0:
            newURL = newURL + '/' + url
        return self.BuildURLFromItem(self.GetItemParent(item), newURL)

    def OnItemExpanding(self, event):
        """
          Whenever a disclosure box is expanded, we mark it as such in the
        model's dict and call SynchronizeView so we can either get the new
        items that are now visible (from the app) or just display them.
        """
        if self.model.ignoreExpand:
            return
        item = event.GetItem()
        url = self.BuildURLFromItem(item)
        fields = url.split('/')
        entry = self.__GetSideBarURLTreeEntry(fields, self.model.sideBarURLTree)
        entry.isOpen = true
        self.model.SynchronizeView()

    def OnItemCollapsing(self, event):
        """
          Whenever a disclosure box is collapsed, we mark it as such in the
        model's dict.
        """
        item = event.GetItem()
        url = self.BuildURLFromItem(item)
        fields = url.split('/')
        entry = self.__GetSideBarURLTreeEntry(fields, self.model.sideBarURLTree)
        entry.isOpen = false
        
    def ExpandURL(self, url):
        """
          Expands the item representing the given url.  Will also expand 
        any ancestors of the item representing the supplied url.  Returns 
        true if the expansion was successful, false otherwise.
        """
        item = self.__GetItemFromURL(url)
        if item != None:
            fields = url.split('/')
            entry = self.__GetSideBarURLTreeEntry(fields, self.model.sideBarURLTree)
            entry.isOpen = true
            self.Expand(item)
            return true
        return false

    def CollapseURL(self, url):
        """
          Collapses the item representing the given url.  Returns true if
        the collapse was successful, false otherwise.
        """
        item = self.__GetItemFromURL(url)
        if item != None:
            fields = url.split('/')
            entry = self.__GetSideBarURLTreeEntry(fields, self.model.sideBarURLTree)
            entry.isOpen = false
            self.Collapse(item)
            return true
        return false
    
    def SetURLColor(self, url, color):
        """
          Changes the color of the item representing the url.         
        Returns true if the color was successfully set, false otherwise.
        """
        item = self.__GetItemFromURL(url)
        if item != None:
            self.SetItemTextColour(item, color)
            return true
        return false

    def SetURLBold(self, url, isBold=true):
        """
          Sets whether or not the item representing the url should be bold.
        Returns true if the bold state of the item was successfully set,
        false otherwise.
        """
        item = self.__GetItemFromURL(url)
        if item != None:
            self.SetItemBold(item, isBold)
            return true
        return false

    def __GetSideBarURLTreeEntry(self, fields, dict):
        if len(fields) == 1:
            return dict[fields[0]]
        return self.__GetSideBarURLTreeEntry(fields[1:], 
                                             dict[fields[0]].children)
        
    def __GetItemFromURL(self, url):
        urlNoCase = url.lower()
        if not self.urlDictMap.has_key(urlNoCase):
            urlTree = app.model.URLTree
            if urlTree.URLExists(url):
                fields = url.split('/')
                self.__DoExpandURL(fields, self.model.sideBarURLTree)
            else:
                return None
        return self.urlDictMap[urlNoCase]

    def __DoExpandURL(self, fields, dict):
        if not dict[fields[0]].isOpen:
            dict[fields[0]].isOpen = true
            self.model.SynchronizeView()
        if len(fields) > 1:
            self.__DoExpandURL(fields[1:], dict[fields[0]].children)
        
    def OnDestroy(self, event):
        """
          Remove from the association when the sidebar is destroyed.
        """
        del app.association[id(self.model)]
 