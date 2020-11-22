from PyQt5 import QtWidgets, QtGui, QtCore

from apollo.db.library_manager import LibraryManager
from apollo.app.ux_startup import ApolloStartup
from apollo.utils import PlayingQueue, exe_time

class ApolloTabFunctions(ApolloStartup):
    """
    Interface between all the tabs in Apollo. 
    """
    
    def __init__(self):
        super().__init__()
        self.LoadDB()
        self.PlayQueue = PlayingQueue()
        self.LibraryTab = LibraryTab(self)
        self.NowPlayingTab = NowPlayingTab(self)
        
        
    def LoadDB(self):
        """
        Connects to the databse and returns Manager Object to communicate with
        """
        dbname = self.CONF_MANG.Getvalue(path = 'DBNAME')
        self.LIB_MANG = LibraryManager(dbname)
        
        
    def _BindingLineSearch(self, LEDT, TBV):
        """Binds the LineEdit text to a search term and searches in DB and refreshes table"""
        LEDT.returnPressed.connect(lambda: self.LIB_MANG.TableSearch(LEDT, TBV))
        LEDT.textChanged.connect(lambda : self._BindingLineClear(LEDT, TBV))
    
    
    def _BindingLineClear(self, LEDT, TBV):
        """Binds the LineEdit Clear to refresh table"""
        if LEDT.text() == "":
            self.LIB_MANG.TableSearch(LEDT, TBV)
    
    
    def _ColumnSelection(self, TBV, Col):
        """
        Gets Data from the slected items from the QTableView and
        returns data of the requested column
        
        :Args:
            TBV: TableView
                Table to get data from
            Col: String
                Column to get data from
        """
        Col = self.LIB_MANG.db_fields.index(Col)
        selected = TBV.selectedIndexes()[Col::len(self.LIB_MANG.db_fields)]
        return ([index.data() for index in  selected])
        
        
    def _GetSelectionIndexes(self, TBV):
        selected = TBV.selectedIndexes()
        Start = 0
        End = len(self.LIB_MANG.db_fields)
        offset = len(self.LIB_MANG.db_fields)
        Table = []
        mapper = lambda obj: obj.data() 

        for __ in range(int(len(selected) / offset)):
            data = list(map(mapper, selected[Start:End]))
            Start = (Start+offset)
            End = (End+offset)            
            Table.append(data)
            
        return Table
        
        
    def _PlayNow(self, TBV):
        self.PlayQueue.RemoveElements()
        rows = self._ColumnSelection(TBV, "file_id")
        self.PlayQueue.AddElements(rows)
        self.NowPlayingTab.RefreshQueueTable()
        
    def _QueueNext(self, TBV):
        rows = self._ColumnSelection(TBV, "file_id")
        self.PlayQueue.AddNext(rows)
        self.NowPlayingTab.RefreshQueueTable()


    def _QueueLast(self, TBV):
        rows = self._ColumnSelection(TBV, "file_id")
        self.PlayQueue.AddElements(rows)
        self.NowPlayingTab.RefreshQueueTable()

    
        
class LibraryTab:
    
    def __init__(self, UI = None):
        if UI != None:
            self.UI = UI
        else:
            self.UI = ApolloTabFunctions()
        
        self.Init_TableModel("library")
        self.ElementsBindings()
        
    def Init_TableModel(self, tablename):
        """
        initilizes table with database values
        """
        Table = self.UI.LIB_MANG.GetTableModle(tablename)
        self.UI.LIB_MANG.SetTableModle(self.UI.apollo_TBV_LBT_maintable, Table, self.UI.LIB_MANG.db_fields)
        self.UI.apollo_TBV_LBT_maintable.setProperty("DB_Table", tablename)
        self.UI.apollo_TBV_LBT_maintable.setProperty("DB_Columns", self.UI.LIB_MANG.db_fields)
        
        
    def ElementsBindings(self):
        """
        Binds and connects UI Signals to internal functions.
        """
        self.UI._BindingLineSearch(self.UI.apollo_LEDT_LBT_main_search, self.UI.apollo_TBV_LBT_maintable)
        self.UI.apollo_TBV_LBT_maintable.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.UI.apollo_TBV_LBT_maintable.customContextMenuRequested.connect(self.ContextMenu_MainTable)
        self.UI.apollo_PSB_LBT_addtrack.pressed.connect(lambda: print(self.UI.PlayQueue))

    def ContextMenu_MainTable(self):
        """
        Context menu Bindings for the Library Tab MainTable
        """
        
        lv_1 = QtWidgets.QMenu()
        
        (lv_1).addAction("Play Now").triggered.connect(lambda: self.UI._PlayNow(TBV = self.UI.apollo_TBV_LBT_maintable))
        (lv_1).addAction("Queue Next").triggered.connect(lambda: self.UI._QueueNext(TBV = self.UI.apollo_TBV_LBT_maintable))
        (lv_1).addAction("Queue Last").triggered.connect(lambda: self.UI._QueueLast(TBV = self.UI.apollo_TBV_LBT_maintable))
        
        
        cursor = QtGui.QCursor()
        lv_1.exec_(cursor.pos()) 
        
      
class NowPlayingTab:
    ## Issues
    # 1. Columns are sorted and Dont remain As a Queue, 
    #    Database Internally Sorts them
    
    
    def __init__(self, UI):
        if UI != None:
            self.UI = UI
        else:
            self.UI = ApolloTabFunctions()
            
        self.Init_TableModel("nowplaying")
        self.ElementsBindings()
            
    def Init_TableModel(self, tablename):
        """
        initilizes table with a QStandardItemModel
        """
        Table = self.UI.LIB_MANG.GetTableModle(tablename)
        self.UI.LIB_MANG.SetTableModle(self.UI.apollo_TBV_NPQ_maintable, Table, self.UI.LIB_MANG.db_fields)        
        self.UI.apollo_TBV_NPQ_maintable.setProperty("DB_Table", tablename)
        self.UI.apollo_TBV_NPQ_maintable.setProperty("DB_Columns", self.UI.LIB_MANG.db_fields)
        
    def ElementsBindings(self):
        """
        Binds and connects UI Signals to internal functions.
        """    
        self.UI._BindingLineSearch(self.UI.apollo_LEDT_NPQ_main_search, self.UI.apollo_TBV_NPQ_maintable)
        
    def RefreshQueueTable(self):
        """
        Refreshes the NowPlaying Table with Updated Values
        """
        data = self.UI.PlayQueue.GetQueue()
        self.UI.LIB_MANG.CreateView("nowplaying", "file_id", data)
        self.UI.LIB_MANG.Refresh_TableModelData(self.UI.apollo_TBV_NPQ_maintable)
                
                
if __name__ == "__main__":
    from apollo.app.apollo_exe import ApolloExecute
    app = ApolloExecute()
    app.Execute()
