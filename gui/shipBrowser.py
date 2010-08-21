import wx
import controller
import bitmapLoader
import gui.mainFrame

class ShipBrowser(wx.Panel):
    def __init__(self, parent):
        self.built = False
        wx.Panel.__init__(self, parent)
        vbox = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(vbox)

        self.shipMenu = ShipMenu(self)
        vbox.Add(self.shipMenu, 0, wx.EXPAND)

        self.shipView = ShipView(self)
        vbox.Add(self.shipView, 1, wx.EXPAND)

        self.shipImageList = wx.ImageList(16, 16)
        self.shipView.SetImageList(self.shipImageList)

        self.shipRoot = self.shipView.AddRoot("Ships")

        self.raceImageIds = {}
        self.races = ["amarr", "caldari", "gallente", "minmatar", "ore", "serpentis", "angel", "blood", "sansha", "guristas"]
        for race in self.races:
            imageId = self.shipImageList.Add(bitmapLoader.getBitmap("race_%s_small" % race, "icons"))
            self.raceImageIds[race] = imageId

        self.races.append("None")
        self.idRaceMap = {}
        self.shipView.races = self.races
        self.shipView.idRaceMap = self.idRaceMap

        self.build()

        #Bind our lookup method to when the tree gets expanded
        self.shipView.Bind(wx.EVT_TREE_ITEM_EXPANDING, self.expandLookup)
        self.shipView.Bind(wx.EVT_TREE_SEL_CHANGED, self.toggleButtons)
        self.shipView.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.changeFitName)
        self.shipView.Bind(wx.EVT_LEFT_DCLICK, self.renameOrExpand)

        #Bind buttons
        self.shipMenu.new.Bind(wx.EVT_BUTTON, self.newFit)
        self.shipMenu.rename.Bind(wx.EVT_BUTTON, self.renameFit)
        self.shipMenu.delete.Bind(wx.EVT_BUTTON, self.deleteFit)
        self.shipMenu.copy.Bind(wx.EVT_BUTTON, self.copyFit)

        #Bind search
        self.shipMenu.search.Bind(wx.EVT_TEXT_ENTER, self.startSearch)
        self.shipMenu.search.Bind(wx.EVT_SEARCHCTRL_SEARCH_BTN, self.startSearch)
        self.shipMenu.search.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN, self.clearSearch)

        self.timer = None

    def build(self):
        if not self.built:
            self.built = True
            cMarket = controller.Market.getInstance()
            shipRoot = cMarket.getShipRoot()
            iconId = self.shipImageList.Add(bitmapLoader.getBitmap("ship_small", "icons"))
            for id, name in shipRoot:
                childId = self.shipView.AppendItem(self.shipRoot, name, iconId, data=wx.TreeItemData(("group", id)))
                self.shipView.AppendItem(childId, "dummy")

        self.shipView.SortChildren(self.shipRoot)

    def toggleButtons(self, event):
        root = self.shipView.GetSelection()
        btns = (self.shipMenu.new, self.shipMenu.rename, self.shipMenu.delete, self.shipMenu.copy)
        if not root.IsOk():
            for btn in btns:
                btn.Enable(False)
        else:
            type, groupID = self.shipView.GetPyData(root)
            if type == "fit":
                for btn in btns:
                    btn.Enable()

            elif  type == "ship":
                for btn in btns:
                    btn.Enable(btn == self.shipMenu.new)

            else:
                for btn in btns:
                    btn.Enable(False)

    def expandLookup(self, event):
        root = event.Item
        child, cookie = self.shipView.GetFirstChild(root)
        self.idRaceMap.clear()
        if self.shipView.GetItemText(child) == "dummy":
            self.shipView.Delete(child)

            cMarket = controller.Market.getInstance()
            cFit = controller.Fit.getInstance()

            type, groupID = self.shipView.GetPyData(root)
            if type == "group":
                for id, name, race in cMarket.getShipList(groupID):
                    iconId = self.raceImageIds[race] if race in self.raceImageIds else -1
                    self.idRaceMap[id] = race
                    childId = self.shipView.AppendItem(root, name, iconId, data=wx.TreeItemData(("ship", id)))
                    for fitID, fitName in cFit.getFitsWithShip(id):
                        self.shipView.AppendItem(childId, fitName, -1, data=wx.TreeItemData("fit", fitID))

            self.shipView.SortChildren(root)

    def newFit(self, event):
        root = self.shipView.GetSelection()
        type, shipID = self.shipView.GetPyData(root)
        if type == "fit":
            root = self.shipView.GetItemParent(root)
            type, shipID = self.shipView.GetPyData(root)

        name = "%s fit" % self.shipView.GetItemText(root)
        cFit = controller.Fit.getInstance()
        fitID = cFit.newFit(shipID, name)
        childId = self.shipView.AppendItem(root, name, -1, data=wx.TreeItemData(("fit", fitID)))
        self.shipView.SetItemText(childId, name)
        self.shipView.SortChildren(root)
        self.shipView.Expand(root)
        self.shipView.SelectItem(childId)
        self.shipView.EditLabel(childId)

    def renameOrExpand(self, event):
        root = self.shipView.GetSelection()
        type, _ = self.shipView.GetPyData(root)
        if type == "fit":
            self.shipView.EditLabel(root)

        event.Skip()


    def renameFit(self, event):
        root = self.shipView.GetSelection()
        type, _ = self.shipView.GetPyData(root)
        if type == "fit":
            self.shipView.EditLabel(root)

    def changeFitName(self, event):
        item = event.Item
        newName = event.Label
        type, fitID = self.shipView.GetPyData(item)
        cFit = controller.Fit.getInstance()
        cFit.renameFit(fitID, newName)
        wx.CallAfter(self.shipView.SortChildren, self.shipView.GetItemParent(item))

    def deleteFit(self, event):
        root = self.shipView.GetSelection()
        type, fitID = self.shipView.GetPyData(root)
        if type == "fit":
            cFit = controller.Fit.getInstance()
            cFit.deleteFit(fitID)
            self.shipView.Delete(root)

    def copyFit(self, event):
        root = self.shipView.GetSelection()
        type, fitID = self.shipView.GetPyData(root)
        if type == "fit":
            cFit = controller.Fit.getInstance()
            newID = cFit.copyFit(fitID)
            parent = self.shipView.GetItemParent(root)
            name = self.shipView.GetItemText(root)
            childId = self.shipView.AppendItem(parent, name, -1, data=wx.TreeItemData(("fit", newID)))
            self.shipView.SetItemText(childId, name)
            self.shipView.SelectItem(childId)
            self.shipView.EditLabel(childId)

    def clearSearch(self, event):
        self.shipMenu.search.Clear()

    def startSearch(self, event):
        text = self.shipMenu.search.GetLineText(0)
        cMarket = controller.Market.getInstance()
        result = cMarket.searchShip(text)
        if result == None:
            return

        groupID, shipID = result
        child, cookie = self.shipView.GetFirstChild(self.shipRoot)
        while child.IsOk():
            _, currGroupID = self.shipView.GetPyData(child)
            if currGroupID == groupID:
                self.shipView.Expand(child)
                shipChild, shipCookie = self.shipView.GetFirstChild(child)
                while shipChild.IsOk():
                    _, currShipID = self.shipView.GetPyData(shipChild)
                    if shipID == currShipID:
                        self.shipView.SelectItem(shipChild)
                        self.SetFocus()
                        break
                    shipChild, shipCookie = self.shipView.GetNextChild(child, shipCookie)
                break

            child, cookie = self.shipView.GetNextChild(self.shipRoot, cookie)

class ShipView(wx.TreeCtrl):
    def __init__(self, parent):
        wx.TreeCtrl.__init__(self, parent)
        treeStyle = self.GetWindowStyleFlag()
        treeStyle |= wx.TR_HIDE_ROOT
        self.SetWindowStyleFlag(treeStyle)

    def OnCompareItems(self, treeId1, treeId2):
        child, cookie = self.GetFirstChild(treeId1)
        type1, id1 = self.GetPyData(treeId1)
        type2, id2 = self.GetPyData(treeId2)
        if type1 in ("fit", "group"):
            return cmp(self.GetItemText(treeId1), self.GetItemText(treeId2))
        else:
            c = cmp(self.races.index(self.idRaceMap[id1] or "None"), self.races.index(self.idRaceMap[id2] or "None"))
            if c != 0:
                return c
            else:
                return cmp(self.GetItemText(treeId1), self.GetItemText(treeId2))

class ShipMenu(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.parent = parent

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(sizer)

        size = None
        for name, art in (("new", wx.ART_NEW), ("rename", bitmapLoader.getBitmap("rename", "icons")), ("copy", wx.ART_COPY), ("delete", wx.ART_DELETE)):
            bitmap = wx.ArtProvider.GetBitmap(art, wx.ART_BUTTON) if name != "rename" else art
            btn = wx.BitmapButton(self, wx.ID_ANY, bitmap)
            if size is None:
                size = btn.GetSize()
            else:
                btn.SetMinSize(size)
                btn.SetMaxSize(size)

            btn.Layout()
            setattr(self, name, btn)
            btn.Enable(False)
            btn.SetToolTipString("%s fit." % name.capitalize())
            sizer.Add(btn, 0, wx.EXPAND)

        self.search = wx.SearchCtrl(parent, wx.ID_ANY, style=wx.TE_PROCESS_ENTER)
        self.search.ShowCancelButton(True)
        sizer.Add(self.search, 1, wx.EXPAND)