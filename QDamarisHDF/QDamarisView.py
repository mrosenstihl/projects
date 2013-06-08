#!/usr/bin/env python
# -*- coding: utf-8 -*-
from PyQt4 import QtCore, QtGui, Qt
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure
import numpy as N
import mainwindow as M
import scipy.odr as O

DEBUG = True

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class H5TreeItem(QtGui.QTreeWidgetItem):
    def __init__(self, a_node=None):
        QtGui.QTreeWidgetItem.__init__(self)
        self.setText(0, a_node._v_name)
        self.node = a_node
        self.pathname = a_node._v_pathname


def add_treeItems(parent_item, parent_group):
    """
    This creates the displayed tree, only hdf groups are shown, arrays are ignored
    recursively walk through the data_pool adding items
    """
    for group in parent_group:
        if type(group) == T.group.Group:
            child = QtGui.QTreeWidgetItem(parent_item)
            child.setText(0,group._v_name)
            child.node = group
            parent_item.addChild(child)
            add_treeItems(child,group)

def recurse_selected_items(items,alist):
    """
    returns a list of all children of  selected group(s)
    """
    for item in items:
        if item.childCount()==0:
            "only remmber the leafs"
            alist.append(item)
        else:
            "take the children"
            children = [item.child(i) for i in xrange( item.childCount())]
            recurse_selected_items(children,alist)
    return alist


class CustomToolbar(NavigationToolbar):
    # our spanChanged signal
    spanSelectedTrigger = QtCore.pyqtSignal(int, int, name='spanChanged')
    def __init__(self, plotCanvas, plotWidget):
        NavigationToolbar.__init__(self, plotCanvas, plotWidget, coordinates=True)
        self.canvas = plotCanvas
        # Span select Button
        self.span_button = QtGui.QAction(QtGui.QIcon("border-1d-right-icon.png" ), "Span", self)
        self.span_button.setCheckable(True)
        
        self.cids = []
        self.cids.append(self.canvas.mpl_connect('button_press_event', self.press))
        self.cids.append(self.canvas.mpl_connect('motion_notify_event', self.onmove))
        self.cids.append(self.canvas.mpl_connect('button_release_event', self.release))
        self.cids.append(self.canvas.mpl_connect('draw_event', self.update_background))
        

        #    act.setCheckable(True)
        # add actions before the coordinates widget 
        self.insertAction(self.actions()[-1], self.span_button)

        self.buttons={}
        self._pressed = False
        self.background = None
        self.span = None
        self.istart = 0
        self.iend = 0
        self.xstart = 0
        self.xend = 0

    def set_span(self,x1,x2):
        #trans = blended_transform_factory(self.axes.transData, self.axes.transAxes)
        cur = self.span.get_xy()
        cur[0,0] = x1
        cur[1,0] = x1
        cur[2,0] = x2
        cur[3,0] = x2
        self.span.set_xy(cur)

    def ignore(self, event):
        # 'return ``True`` if *event* should be ignored'
        return  event.inaxes!=self.axes or event.button !=1

    def update_background(self, event):
        if self.axes is None:
            raise SyntaxError,"Need an axes reference!"
        self.background = self.canvas.copy_from_bbox(self.axes.bbox)

    def press(self, event):
        if self.span_button.isChecked():
            #if self.background is None:
            #    self.background = self.canvas.copy_from_bbox(self.axes.bbox)
            #else:
            self.canvas.restore_region(self.background)
            self.xstart = event.xdata
            self.istart = event.x
            if self.span is None:
                self.span = self.axes.axvspan(event.xdata, event.xdata, alpha = 0.35, color = "g")
            else:
                self.set_span(event.xdata, event.xdata)
            self._pressed = True
    
    def onmove(self,event):
        if self.span_button.isChecked() and self._pressed and not self.ignore(event): 
            self.set_span(self.xstart, event.xdata)
            self.update()

    def update(self):
        self.canvas.restore_region(self.background)
        self.axes.draw_artist(self.span)
        self.canvas.blit(self.axes.bbox)

    def release(self,event):
        self.span_button.setChecked(False)
        self.xend = event.xdata
        self.iend = event.x
        if self.iend < self.istart:
            self.iend,self.istart = self.istart,self.iend
        print "released",self.xstart,self.xend
        if self._pressed:
            if self.ignore(event):
                self.istart = 0
            self.spanSelectedTrigger.emit(self.istart,self.iend)
            self._pressed = False



class test(QtGui.QMainWindow):    
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.ui = M.Ui_MainWindow()
        self.ui.setupUi(self)
        self.nodes = []
        #QtGui.QMainWindow.__init__(self)


        self.chooser = QtGui.QAction("Extract amplitudes ...", self)
        self.ui.treeData.addAction(self.chooser)
        
        # connections
        self.ui.loadFile.triggered.connect( self.file_selected )
        self.ui.treeData.itemSelectionChanged.connect( self.nodeSelectionChanged )
        #self.ui.treeData.itemDoubleClicked.connect( self.nodeDoubleClicked )
        
        self.chooser.triggered.connect( self.nodeDoubleClicked )
        self.ui.fitFunc.textChanged.connect( self.fitfunc_defined )
        self.ui.startParams.textChanged.connect( self.beta0_defined )


        
        self.dpi = 100
        self.fit = Figure()
        self.fit_canvas = FigureCanvas(self.fit)
        self.fit_canvas.figure.set_facecolor((0.91,0.91,0.91))
        self.fit_canvas.setParent(self.ui.DataPlot)

        # Since we have only one plot, we can use add_axes 
        # instead of add_subplot, but then the subplot
        # configuration tool in the navigation toolbar wouldn't
        # work.
        #
        self.fit_axes = self.fit.add_subplot(111)

        #
        # Create the navigation toolbar, tied to the canvas
        #
        self.fit_toolbar = NavigationToolbar(self.fit_canvas, self.ui.DataPlot)
        self.fit_toolbar.axes = self.fit_axes
        

        #
        # Layout canvas and toolbar
        #
        fit_vbox = QtGui.QVBoxLayout()
        fit_vbox.addWidget(self.fit_canvas)
        fit_vbox.addWidget(self.fit_toolbar)
        self.ui.DataPlot.setLayout(fit_vbox)

		#
		# Variables for fit data, line will be the interpolated values of the fit
		#
        self.fit_line = None
        self.fit_data = None

    def fitfunc_defined(self):
        try:
            self.fitfunc_str = str( self.ui.fitFunc.document().toPlainText())
            print "F",self.fitfunc_str
        except Exception,e:
            print e

    def fitfunc(self,p,x):
        return eval(self.fitfunc_str)
    
        

    def beta0_defined(self):
        try:
            self.beta0 = [ float(i) for i in str( self.ui.startParams.text() ).split(',') ]
            print self.beta0
            print self.fitfunc(self.beta0,1)
            self.t = []
            self.sig = []
            for node in self.nodes:
                x,y = self.getData(node)
                self.t.append(node._v_attrs['description_'+ str( self.ui.xSelector.currentText() )])
                self.sig.append(y.real[:100].mean())
            self.fit_axes.plot(self.t,self.sig,'o')
            self.fit_axes.autoscale_view()
            self.fit_canvas.draw()

        except Exception,e:
            print e
            self.beta0 = []
    
    
    def getData(self,node, s=None,e=None):
        if node.accu_data.shape[1] == 4:
            im = 2
        else:
            im =1
        if s == None or e == None:
            data = node.accu_data.read()[:,0] + 1j* node.accu_data.read()[:,im]
        else:
            data = node.accu_data.read()[s:e,0] + 1j* node.accu_data.read()[s:e,im]
        
        dw = node.indices.col('dwelltime')
        n_points = node.indices.col('length')
        t = N.arange(0,n_points*dw,dw)
        return t,data

    def on_pick(self,event):
        print "HUH"
        print event.x, event.y

    def updateQuickPlot(self, node):
        try:
            t,data = self.getData(self.nodes[self.qp_cb.currentIndex()])
            self.qp_canvas.updatePlot(t,data.real,data.imag)
        except Exception,e:
            print e
            pass
        self.qp.show()

    def nodeDoubleClicked(self):
        self.qp = SelectablePlotWidget(nodes=self.nodes)
        self.qp.qp_toolbar.spanSelectedTrigger.connect(self.updateFitTab)

    def nodeSelectionChanged(self):
        self.ui.treeData.resizeColumnToContents(0)
        self.ui.tableCommonAttrs.clearContents()
        self.ui.tableVariableAttrs.clearContents()
        self.ui.xSelector.clear()
        self.variable_attrs = set()
        self.common_attrs = {}
        self.nodes = []
        selected = []

        items =  self.ui.treeData.selectedItems() 
        selected =  recurse_selected_items(items, selected)
        
        # get the common attributes for fitting
        for i,item in enumerate(selected):
            node = item.node
            attrs = node._v_attrs._v_attrnamesuser
            self.nodes.append(node) # append h5 node to list of selected nodes
            for j,attr in enumerate(attrs):
                value = node._v_attrs[attr]
                if i == 0:
                # add all attributes from the first selected node
                    self.common_attrs[attr] = value
                else:
                    if  ( attr in self.common_attrs.keys()) and (self.common_attrs[attr] == value):
                        self.common_attrs[attr] = value
                    elif (attr in self.common_attrs.keys()) and ( self.common_attrs[attr] != value):
                        self.common_attrs.pop(attr)
                        if attr not in ["oldest_time","earliest_time"]:
                            self.variable_attrs.add(attr)
                    else:
                        #self.common_attrs.pop(attr,0)
                        #self.variable_attrs.remove(attr)
                        pass

        #self.variable_attrs = [i.replace('description_','') for i in variables]
        #self.common_attrs= [i.replace('description_','') for i in common_attrs]
        for row_c,attr in enumerate( self.common_attrs ):
            if row_c >=  self.ui.tableCommonAttrs.rowCount():
                self.ui.tableCommonAttrs.insertRow(row_c)
            self.ui.tableCommonAttrs.setItem(row_c,0,QtGui.QTableWidgetItem(attr.replace('description_','')))
            self.ui.tableCommonAttrs.setItem(row_c,1,QtGui.QTableWidgetItem(self.common_attrs[attr]))
        for row_v,attr in enumerate( list(self.variable_attrs)):
            if row_v >=  self.ui.tableVariableAttrs.rowCount():
                self.ui.tableVariableAttrs.insertRow(row_v)
            self.ui.tableVariableAttrs.setItem(row_v,0,QtGui.QTableWidgetItem(attr.replace('description_','')))
            if row_v == 0:
                self.variable =  str( self.ui.tableVariableAttrs.currentItem() )
            #self.ui.tableVariableAttrs.setItem(row,1,QtGui.QTableWidgetItem(self.variable_attrs[attr]))
        #for i in xrange(row_c+1, self.ui.tableCommonAttrs.rowCount()):
        #    self.ui.tableCommonAttrs.removeRow(i)
        #for i in xrange(row_v+1, self.ui.tableVariableAttrs.rowCount()):
        #    self.ui.tableVariableAttrs.removeRow(i)
        
        self.ui.xSelector.addItems([at.replace('description_','') for at in self.variable_attrs])    

        #[item.setSelected(True) for item in selected]

    def file_selected(self):
		# setup tree view of hdf file
        if DEBUG:
            path = 'test.h5'
            self.nodes = []
            self.ui.treeData.clear()
        else:
            path = unicode(QtGui.QFileDialog.getOpenFileName(self, 
                        'Load file',filter="HDF5 files (*.h5 *.hdf)"))
        self.hdffile  = T.openFile(path)
        #head = QtGui.QTreeWidgetItem(self.ui.treeData)
        head = H5TreeItem(a_node = self.hdffile.root.data_pool)
        #head.setText(0,"/data_pool")
        self.ui.treeData.addTopLevelItem(head)
        add_treeItems(head,self.hdffile.root.data_pool)

    def updateFitTab(self,s,e):
        print "fit tab updated",s,e
        xlabel = str( self.ui.xSelector.currentText() )
        self.t = []
        self.sig= []
        self.fit_axes.set_xlabel(xlabel)
        for node in self.nodes:
            self.t.append(node._v_attrs['description_'+ xlabel ])
            t,dat = self.getData(node,s,e)
            if self.qp:
                dat *= N.exp(1j*N.pi/180.*self.qp.phase)
            self.sig.append(dat.real.mean())
        if not self.fit_data:
            self.fit_data, = self.fit_axes.plot(self.t,self.sig,'o')
        else:
            self.fit_data.set_ydata(self.sig)
            self.fit_data.set_xdata(self.t)
        self.fit_axes.autoscale_view()
        self.fit_canvas.draw()
        self.ui.tabWidget.setCurrentIndex(1)
        self.ui.tabWidget.raise_()
        pass
        

# mpl widget

class FitWidget:
    def __init__(self):

        pass

class SelectablePlotWidget:  
    def __init__(self, parent = None, nodes=[]):
        # try to bind the getData method
        for widget in QtGui.qApp.topLevelWidgets():
            if widget.objectName() == u'MainWindow':
                self.getData = widget.getData
                break

        if parent is None:
            self.popup = True
            self.qp = QtGui.QWidget()

        # t,real,imag
        self.qp_canvas = BlitQT([0,1],[0,1],[0,1])
        if parent is not None:
            self.popup = False
            self.qp_canvas.setParent( parent )
            self.qp = parent
        self.qp_canvas.figure.set_facecolor((0.91,0.91,0.91))

        #
        # combo box for choosing the displayed node
        #
        self.qp_cb = QtGui.QComboBox()
        self.qp_cb.activated.connect(self.updateView)

        #
        # spin box for phase adjustment
        #
        self.qp_spinbox = QtGui.QDoubleSpinBox()
        self.qp_spinbox.setRange(0,360)
        self.qp_spinbox.setDecimals(2) # default
        self.qp_spinbox.setWrapping(True)
        self.qp_spinbox.valueChanged.connect(self.updateView)
        self.qp_spinbox.setMaximumWidth(80)
        

        #
        # Create the navigation toolbar, tied to the canvas
        #
        self.qp_toolbar = CustomToolbar(self.qp_canvas,
                self.qp)
        #
        # connect the toolbar.axes with our axes in the plot canvas
        #
        self.qp_toolbar.axes = self.qp_canvas.axes

        #
        # Layout canvas and toolbar
        #
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget ( QtGui.QLabel('Data') )
        hbox.addWidget( self.qp_cb )
        hbox.addWidget ( QtGui.QLabel('Phase') )
        hbox.addWidget( self.qp_spinbox )

        vbox = QtGui.QVBoxLayout()
        vbox.addWidget( self.qp_toolbar )
        vbox.addWidget( self.qp_canvas )
        vbox.addLayout(hbox)
        self.qp.setLayout( vbox )
        
        #
        # set the nodes
        #
        self.setNodes( nodes )
        self.updateNodeList( self.nodes )

        if self.popup:
            self.qp.show()

    def setNodes(self, nodes):
        self.nodes = nodes

    def updateView(self, some):
        index = self.qp_cb.currentIndex()
        self.phase = self.qp_spinbox.value()
        try:
            t,data = self.getData(self.nodes[index])
            data *= N.exp(1j*N.pi/180.*self.phase)
            self.qp_canvas.updatePlot(t,data.real,data.imag)
        except Exception,e:
            print e
            pass
        if self.popup:
            self.qp.show()

    def updateNodeList(self, nodes=None):
        print "Update nodes",self.nodes
        self.nodes=nodes
        self.qp_cb.clear()
        self.qp_cb.addItems([n._v_name for n in self.nodes])
        self.updateView(0)




######################## Blitting Plot window ########################

class BlitQT(FigureCanvas):
    """
    This provides a blitting figure canvas for fast drawing of timesignals 
    Methods:
     * updatePlot
    """
    def __init__(self, t=[], real=[], imag=[]):
        FigureCanvas.__init__(self, Figure())

        self.axes = self.figure.add_subplot(111)
        #self.axes.grid()
        #self.axes.set_xlabel("time / s")
        #self.axes.set_ylabel("signal / a.u.")
        # save the current plot 
        #self.axes_background = self.copy_from_bbox(self.axes.bbox)

        self.old_size = self.axes.bbox.width, self.axes.bbox.height
        
        # add a real/imag line
        #self.real_part, = self.axes.plot(t, real, marker=".", ls="-", color='r', label = "Real", animated=True)
        #self.imag_part, = self.axes.plot(t, imag, marker=".", ls="-", color='b', label = "Imag", animated=True)
        #self.axes.legend()
        #self.draw()


        # connections
        self.setFocus()
        self.mpl_connect('button_press_event', self.onclick)
        self.mpl_connect('key_press_event', self.onkey)
        self.mpl_connect('key_release_event', self.offkey)

    def keyPressEvent(self, event):
        print "hier",event
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()


    def offkey(self,event):
        print 'you pressed', event.key, event.xdata, event.ydata

    def onkey(self, event):
        print 'you pressed', event.key, event.xdata, event.ydata
    
    def onclick(self, event):
        print 'button=%d, x=%d, y=%d, xdata=%f, ydata=%f'%(
        event.button, event.x, event.y, event.xdata, event.ydata)
    
    def updatePlot(self, new_t, new_real, new_imag):
        xmin,xmax = min(new_t), max(new_t)
        ymin  = min(min(new_real), min(new_imag))
        ymax  = max(max(new_real), max(new_imag)) 
        axmin, axmax = self.axes.get_xlim()
        aymin, aymax = self.axes.get_ylim()

        current_size = self.axes.bbox.width, self.axes.bbox.height
        if DEBUG: print "updatePlot"
        if (self.old_size != current_size) or xmax >= axmax or ymin <= aymin or ymax >= aymax:
            if DEBUG: 
                print "redraw"
                print len(self.axes.get_lines())
            self.old_size = current_size
            self.axes.clear()
            self.axes.grid()
            self.axes.set_xlim(xmin,xmax*1.1)
            self.axes.set_ylim(ymin,ymax*1.1)
            self.axes.set_xlabel("time / s")
            self.axes.set_ylabel("signal / a.u.")
            # add a real/imag line
            self.real_part, = self.axes.plot(new_t, new_real, marker="", ls="-", color='r', label = "Real", animated=True)
            self.imag_part, = self.axes.plot(new_t, new_imag, marker="", ls="-", color='b', label = "Imag", animated=True)
            self.axes_background = self.copy_from_bbox(self.axes.bbox)
            self.draw()
        self.restore_region(self.axes_background)
        # update the data
        self.real_part.set_ydata(new_real)
        self.real_part.set_xdata(new_t)
        self.imag_part.set_ydata(new_imag)
        self.imag_part.set_xdata(new_t)
        self.axes.legend()
        # just draw the animated artist
        for line in [self.real_part, self.imag_part]:
            self.axes.draw_artist(line)
        self.blit(self.axes.bbox)
    

if __name__ == "__main__":
    import sys
    import tables as T
    if True:
        app = QtGui.QApplication(sys.argv)
        ui = test()
        ui.show()
        ui.raise_()
        if False:
            from IPython.Shell import IPShellEmbed
            ipshell = IPShellEmbed(user_ns = dict(w = ui))
            ipshell()
            
        sys.exit(app.exec_())

