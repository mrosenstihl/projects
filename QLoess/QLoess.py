import numpy as N
import numpy.polynomial.polynomial as Poly
#import scipy.odr as O
import csv
import sys, os
from PyQt4.QtCore import *
from PyQt4.QtGui import *

import matplotlib
params = {
        "font.family": 'sans-serif',
        "xtick.major.size": 5.0,
        "xtick.minor.size": 3.0,
        "ytick.major.size": 5.0,
        "ytick.minor.size": 3.0,
        "axes.linewidth" : 1.0,
        "lines.linewidth": 1.0,
        'axes.labelsize': 10,
        'axes.titlesize':10,
        'text.fontsize': 10,
        'legend.fontsize': 8,
        'legend.titlesize':9,
        'legend.numpoints': 1,
        'legend.handletextpad': 0.2,# *pt pad between handle and text
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'figure.facecolor': (0.91,0.91,0.91),
#        'text.usetex': True,
#       'figure.edgecolor' : 'None',
#       'figure.figsize': (figx,figy),  
#       'figure.subplot.top' : 0.70,}
        'lines.markersize' : 4.0,
        'lines.markeredgecolor' : 'k',
        'lines.markeredgewidth' : 0.3,
        'figure.subplot.hspace' : 0.0,
        'figure.subplot.bottom' : 0.125,
        'figure.subplot.top' : 0.95,
        'figure.subplot.left' : 0.125,
        'figure.subplot.right' : 0.95}
matplotlib.rcParams.update(params)




from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure

def median_resampling(x,y):
    median = N.median(N.abs(N.diff(x)))
    new_points = int(x.ptp()/median)
    if N.isinf(new_points):
        new_points = len(x)
    x_new = N.linspace(x.min(),x.max(), new_points )
    y_new = N.interp(x_new, x[x.argsort()],y[x.argsort()])
    return x_new,y_new

def B(res):
    s = N.median(N.abs(res))
    return N.clip((1-(res/(6*s))**2)**2,0,1)
    
def model(p, x):
    return p[1]*x + p[0]

def triangle(x,x0):
    # weight function triangular
    return N.interp(x_selected,
                            [x_selected.min(),x_val,x_selected.max()],
                            [0,1.0,0])
def bicube(x,x0):
    return (1-( (x-x0)/(x.max()-x.min()) )**2)**2
    
def tricube(x,x0):
    tric = (1-N.abs( (x-x0)/(x.max()-x.min()) )**3)**3
    #tric /= tric.max()
    return tric


def bootstrap(xs,ys,window,robust_iterations=1, resampling=False, num=500):
    results = []
    i = 0
    while i < num:
        index = N.random.randint(0,len(ys)-1,len(ys))
        x,y = xs[index],ys[index]
        y_loess  = lowess(x,y, window,robust_iterations)
        if not N.any(N.isnan(y_loess)):
            results.append(y_loess[x.argsort()])
            i += 1
    results = N.array(results)
    return results

def lowess(x, y, f=2./3., iter=1): 
    """lowess(x, y, f=2./3., iter=3) -> yest 
 
    Lowess smoother: Robust locally weighted regression. 
    The lowess function fits a nonparametric regression curve to a scatterplot. 
    The arrays x and y contain an equal number of elements; each pair 
    (x[i], y[i]) defines a data point in the scatterplot. The function returns 
    the estimated (smooth) values of y. 
 
    The smoothing span is given by f. A larger value for f will result in a 
    smoother curve. The number of robustifying iterations is given by iter. The 
    function will run faster with a smaller number of iterations. 
 
    x and y should be N float arrays of equal length.  The return value is 
    also a N float array of that length. 
 
    e.g. 
    >>> import N 
    >>> x = N.array([4,  4,  7,  7,  8,  9, 10, 10, 10, 11, 11, 12, 12, 12, 
    ...                 12, 13, 13, 13, 13, 14, 14, 14, 14, 15, 15, 15, 16, 16, 
    ...                 17, 17, 17, 18, 18, 18, 18, 19, 19, 19, 20, 20, 20, 20, 
    ...                 20, 22, 23, 24, 24, 24, 24, 25], N.float) 
    >>> y = N.array([2, 10,  4, 22, 16, 10, 18, 26, 34, 17, 28, 14, 20, 24, 
    ...                 28, 26, 34, 34, 46, 26, 36, 60, 80, 20, 26, 54, 32, 40, 
    ...                 32, 40, 50, 42, 56, 76, 84, 36, 46, 68, 32, 48, 52, 56, 
    ...                 64, 66, 54, 70, 92, 93, 120, 85], N.float) 
    >>> result = lowess(x, y) 
    >>> len(result) 
    50 
    >>> print "[%0.2f, ..., %0.2f]" % (result[0], result[-1]) 
    [4.85, ..., 84.98] 
    """ 
    n = len(x) 
    r = int(N.ceil(f*n)) 
    h = [N.sort(N.abs(x-x[i]))[r] for i in xrange(n)] 
    w = N.clip(N.abs(([x]-N.transpose([x]))/h),0.0,1.0) 
    w = 1-w*w*w 
    w = w*w*w 
    yest = N.zeros(n) 
    delta = N.ones(n) 
    for iteration in xrange(iter): 
        for i in xrange(n): 
            weights = delta * w[:,i] 
            weights_mul_x = weights * x 
            b1 = N.dot(weights,y) 
            b2 = N.dot(weights_mul_x,y) 
            A11 = N.sum(weights) 
            A12 = N.sum(weights_mul_x) 
            A21 = A12 
            A22 = N.dot(weights_mul_x,x) 
            determinant = A11*A22 - A12*A21 
            beta1 = (A22*b1-A12*b2) / determinant 
            beta2 = (A11*b2-A21*b1) / determinant 
            yest[i] = beta1 + beta2*x[i] 
        residuals = y-yest 
        s = N.median(N.abs(residuals)) 
        delta[:] = N.clip(residuals/(6*s),-1,1) 
        delta[:] = 1-delta*delta 
        delta[:] = delta*delta 
    return yest 


def mrlowess(xs,ys,window,robust_iterations=1):
    """
    window in same units of x, i.e. years
    """
    # sort the data
    #print x,y
    tmp = xs[:]
    data = N.zeros(len(xs))
    orig_index = tmp.argsort()
    x = xs[orig_index]
    y = ys[orig_index]
#   print xs is x
    for i,x_val in enumerate(x):
        ind = (x>=x_val-window/2.)&(x<=x_val+window/2.)
        x_selected = x[ind] 
        y_selected = y[ind]
        n = len(x_selected)
        if len(set(x_selected)) > 1:
            delta = N.ones( n )
            weights = tricube(x_selected, x_val)
            #print weights

            for j in xrange(robust_iterations):
        #       print x_selected,y_selected
                weights *= delta
                #weights /= weights.sum()
                
                #print x_selected, y_selected
                #beta = Poly.polyfit(x_selected,y_selected,1, w=weights)
                dat = O.Data(x_selected,y_selected,we = weights)
                mod = O.Model(model)
                odr = O.ODR(dat,mod,[1,1],ifixx=(0,))
                odr.run()
                beta = odr.output.beta
                res = y_selected - Poly.polyval([x_val],beta)
                delta = B(res)
                
                if i == 2000:
                    print x_val
                    print x_selected
                    print y_selected
                    print "delta",delta
                    print weights
            y_loess = Poly.polyval([x_val],beta)
        else:
            y_loess = list(y_selected)[0]
        data[i] = y_loess
    return data[orig_index]

class AppForm(QMainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self.full_data = []
        self.data = N.array([[],[]])
        self.smoothed_data = N.array([[],[],[],[],[]])
        self.selectable_columns = []
        self.setWindowTitle('LOESS Smoothing')
        self.data_loaded = True

        self.create_menu()
        self.create_main_frame()
        self.create_status_bar()

        self.textbox.setText('2500')
        self.on_draw()

    def save_plot(self):
        self.mpl_toolbar.save_figure()

    def save_data(self):
        print "Saving data ..."
        path = unicode(QFileDialog.getSaveFileName(self, 
                        'Save file to ...', filter="Data files (*.txt *.csv *.dat)"))
        fname = os.path.splitext(path)[0] + ".csv"
        i=0
        while os.path.exists(fname):
            fname = os.path.splitext(fname)[0] + "_%i.csv"%i
            i += 1
        print "... to %s"%fname
        f = open(fname , 'w')
        csv_writer = csv.writer(f,dialect='excel') #excel
        csv_writer.writerow([self.axes.get_xlabel(), "Smoothed data", self.axes.get_ylabel(), "CI(lower)", "CI(upper)"])
        csv_writer.writerows(list(self.smoothed_data.T))
        f.close()
        # x, y_loess, y, y_loess_min, y_loess_max
         

    def load_data(self):
        
        path = unicode(QFileDialog.getOpenFileName(self, 
                        'Load file',filter="Data files (*.txt *.csv *.dat)"))
        if path:
            self.set_x_column.clear()
            self.set_y_column.clear()
            f = open(path)
            # read the first non empty line, assuming it is the header line
            line = f.readline()
            while line == "":
                line = f.readline()
            self.selectable_columns = line.split(',')
            self.set_x_column.addItems(self.selectable_columns)
            self.set_y_column.addItems(self.selectable_columns)
        
            # load the rest
            self.full_data = [line.split(',') for line in f.readlines() if line]
            self.data_loaded = True
        else:
            self.data_loaded=False

    def on_select_data(self):
        if self.data_loaded:
            raw_data =  [( row[self.set_x_column.currentIndex()], row[self.set_y_column.currentIndex()] ) for row in self.full_data]
            sanitized_data = [[],[]]
            for values in raw_data:
                for i, value in enumerate(values):
                    if value == "":
                        continue
                        #sanitized_data[i].append(0)
                    else:
                        try:
                            sanitized_data[i].append(float(value))
                        except ValueError:
                            raise ValueError, value
            self.data = N.array(sanitized_data)
            self.data[1,:] = self.data[1,self.data[0,:].argsort()]
            self.data[0,:] = self.data[0,self.data[0,:].argsort()]
            #if self.data.shape[1] != 0:
            #    minimum,maximum = (N.abs(N.diff(self.data[0,:] ) ).min()*1.5, self.data[0,:].max()/5)
            #    self.slider.setRange(minimum,maximum)
            #    self.slider.setValue((maximum-minimum)/2)



    def on_about(self):
        msg = """ A demo of using PyQt with matplotlib:
        
         * Use the matplotlib navigation bar
         * Add values to the text box and press Enter (or click "Draw")
         * Show or hide the grid
         * Drag the slider to modify the width of the bars
         * Save the plot to a file using the File menu
         * Click on a bar to receive an informative message
        """
        QMessageBox.about(self, "About the demo", msg.strip())
    

    def on_pick(self, event):
        # The event received here is of the type
        # matplotlib.backend_bases.PickEvent
        #
        # It carries lots of information, of which we're using
        # only a small amount here.
        # 
        box_points = event.artist.get_bbox().get_points()
        msg = "You've clicked on a bar with coords:\n %s" % box_points
        
        QMessageBox.information(self, "Click!", msg)

    def window_changed(self):
        self.statusBar().showMessage("Calculating ... ", 2000)
        if self.median_cb.isChecked():
            x,y = median_resampling(self.data[0,:], self.data[1,:])
        else:
            x,y = (self.data[0,:], self.data[1,:])
        try:
            window = float(self.textbox.text())
            f =  window/x.ptp()
            robust_iters =  self.robust_iteration_spinbox.value()
            y_loess = lowess(x,y,f,robust_iters)
            # confidence intervals via bootstrap
            if self.ci_cb.isChecked():
                ci = float(self.cibox.text())
                bootstrap_results = bootstrap(x,y,f, robust_iters, False, num=600)
                y_loess_min = N.percentile(bootstrap_results,100-ci, axis=0)
                y_loess_max = N.percentile(bootstrap_results,ci, axis=0)
                y_loess_bsmean = bootstrap_results.mean(axis=0)
                # check if CI have to be switched
                if y_loess_min[0] > y_loess_max[0]:
                    y_loess_min, y_loess_max = y_loess_max,y_loess_min
                print "Bias:",N.sum(y_loess_bsmean-y_loess)
            else:
                y_loess_min = N.zeros(len(x))
                y_loess_max = N.zeros(len(x))
            self.smoothed_data = N.array([ x, y_loess, y, y_loess_min, y_loess_max])
            self.statusBar().showMessage("Calculating finnished", 2000)
            self.on_draw()

        except Exception,e:
            self.statusBar().showMessage("Aborted", 2000)
            self.ci_cb.setCheckState(False)
            self.on_draw()
            print e


    def on_draw(self):
        """ Redraws the figure
        """
        
        x = self.data[0,:]
        y = self.data[1,:]
        y = y[x.argsort()]
        x = x[x.argsort()]

        # clear the axes and redraw the plot anew
        #
        self.axes.clear()        
        self.axes.grid(self.grid_cb.isChecked())

        x_smoothed = self.smoothed_data[0,:]
        y_smoothed = self.smoothed_data[1,:]
        y_smoothed_original = self.smoothed_data[2,:]
        self.axes.plot(x,y, picker=5, color='b',ls='-')
        if self.median_cb.isChecked():
            self.axes.plot(x_smoothed,y_smoothed_original, color='g',ls='--', label="Resampled data")
        if self.ci_cb.isChecked():
            y_ci1 = self.smoothed_data[3,:]
            y_ci2 =  self.smoothed_data[4,:]
            self.axes.plot(x_smoothed, y_ci1, lw=0.5, color='r')
            self.axes.plot(x_smoothed, y_ci2, lw=0.5, color='r')
            self.axes.fill_between(x_smoothed, y_ci1, y_ci2, where=None, color='r', alpha=0.1)
        self.axes.plot(x_smoothed,y_smoothed,color='r',markeredgecolor="r", ls='-', lw=1.5, marker='None',markersize=2.5, label="LOESS %s"%(str(self.textbox.text()).strip()))
        self.axes.set_xlabel(self.set_x_column.currentText())
        self.axes.set_ylabel(self.set_y_column.currentText())
        self.axes.legend()
        if y != []:
            self.axes.set_ylim(y.min(),y.max()*1.2)
        self.canvas.draw()
    
    def create_main_frame(self):
        self.main_frame = QWidget()
        
        # Create the mpl Figure and FigCanvas objects. 
        # 5x4 inches, 100 dots-per-inch
        #
        self.dpi = 100
        self.fig = Figure((5.0, 4.0), dpi=self.dpi)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setParent(self.main_frame)
        
        # Since we have only one plot, we can use add_axes 
        # instead of add_subplot, but then the subplot
        # configuration tool in the navigation toolbar wouldn't
        # work.
        #
        self.axes = self.fig.add_subplot(111)
        
        # Bind the 'pick' event for clicking on one of the bars
        #
        #self.canvas.mpl_connect('pick_event', self.on_pick)
        
        # Create the navigation toolbar, tied to the canvas
        #
        self.mpl_toolbar = NavigationToolbar(self.canvas, self.main_frame)
        
        # Other GUI controls
        # 
        textbox_label = QLabel("Window size")
        self.textbox = QLineEdit()
        self.textbox.setMinimumWidth(100)
        self.textbox.setMaximumWidth(100)
        self.connect(self.textbox, SIGNAL('returnPressed ()'), self.window_changed)
        
        self.draw_button = QPushButton("&Draw")
        self.draw_button.setMaximumWidth(100)
        self.connect(self.draw_button, SIGNAL('clicked()'), self.on_draw)
        
        
        spinbox_label = QLabel("Robust iter.")
        self.robust_iteration_spinbox = QSpinBox()
        self.robust_iteration_spinbox.setMinimum(1)
        self.connect(self.robust_iteration_spinbox, SIGNAL('valueChanged(int)'), self.window_changed)

        self.ci_cb = QCheckBox("Confidence interv.")
        self.ci_cb.setChecked(False)
        self.connect(self.ci_cb, SIGNAL('stateChanged(int)'), self.window_changed)

        self.cibox = QLineEdit()
        self.cibox.setMinimumWidth(100)
        self.cibox.setMaximumWidth(100)
        self.connect(self.cibox, SIGNAL('returnPressed ()'), self.window_changed)

        self.grid_cb = QCheckBox("Show &Grid")
        self.grid_cb.setChecked(True)
        self.connect(self.grid_cb, SIGNAL('stateChanged(int)'), self.on_draw)

        self.median_cb = QCheckBox("&Median resampl.")
        self.median_cb.setChecked(True)
        self.connect(self.median_cb, SIGNAL('stateChanged(int)'), self.on_draw)

        self.set_x_column  = QComboBox()
        self.set_x_column.setMinimumWidth(350)
        self.set_x_column.setToolTip("Abscissa")
        self.set_x_column.setMaxVisibleItems(20)
        self.connect(self.set_x_column, SIGNAL('currentIndexChanged(int)'), self.on_select_data)

        self.set_y_column = QComboBox()
        self.set_y_column.setMinimumWidth(350)
        self.set_y_column.setToolTip("Ordinate")
        self.set_y_column.setMaxVisibleItems(20)
        self.connect(self.set_y_column, SIGNAL('currentIndexChanged(int)'), self.on_select_data)
        
        #slider_label = QLabel('Smoothing (units of x-axis):')
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(1, 100)
        self.slider.setValue(20)
        self.slider.setTracking(False)
        self.slider.setTickPosition(QSlider.NoTicks)
        self.connect(self.slider, SIGNAL('valueChanged(int)'), self.window_changed)
        
        #
        # Layout with box sizers
        # 
        hbox = QHBoxLayout()
        hbox = QGridLayout()
        #hbox.addLayout(0,0,2,3)
        
        #for i,w in enumerate( [  self.textbox, self.set_x_column, self.set_y_column, 
        #        self.draw_button, self.grid_cb]):
        #hbox.addWidget(w)
        hbox.addWidget(textbox_label,0,0)
        hbox.setAlignment(textbox_label, Qt.AlignRight)
        hbox.addWidget(self.textbox,0,1)
        hbox.setAlignment(self.textbox, Qt.AlignLeft)

        hbox.addWidget(spinbox_label,0,2)
        hbox.setAlignment(spinbox_label,Qt.AlignRight)
        hbox.addWidget( self.robust_iteration_spinbox,0,3)
        hbox.setAlignment(self.robust_iteration_spinbox,Qt.AlignLeft)
        
        cibox_label = QLabel("Confidence interval (%)")
        hbox.addWidget(cibox_label,1,0)
        hbox.setAlignment(cibox_label, Qt.AlignRight)
        hbox.addWidget(self.cibox,1,1)
        hbox.setAlignment(self.cibox, Qt.AlignLeft)
        hbox.addWidget( self.ci_cb,1,2)
        hbox.setAlignment(self.ci_cb, Qt.AlignVCenter)


        hbox.addWidget(QLabel("Independent variable:"),2,0)
        hbox.addWidget(self.set_x_column,2,1,1,-1)
        hbox.setAlignment(self.set_x_column, Qt.AlignLeft)
        
        hbox.addWidget(QLabel("Dependent variable:"),3,0)
        hbox.addWidget(self.set_y_column,3,1,1,-1)
        hbox.setAlignment(self.set_y_column, Qt.AlignLeft)
        
        hbox.addWidget( self.median_cb,4,0)
        hbox.setAlignment(self.median_cb, Qt.AlignVCenter)
        hbox.addWidget( self.grid_cb,4,1)
        hbox.setAlignment(self.grid_cb, Qt.AlignVCenter)
        hbox.addWidget(self.draw_button,4,3)
        hbox.setAlignment(self.draw_button, Qt.AlignRight)
        #hbox.setAlignment(w, Qt.AlignVCenter)


        
        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addWidget(self.mpl_toolbar)
        vbox.addLayout(hbox)
        
        self.main_frame.setLayout(vbox)
        self.setCentralWidget(self.main_frame)
    
    def create_status_bar(self):
        self.status_text = QLabel("")
        self.statusBar().addWidget(self.status_text, 1)
        
    def create_menu(self):        
        self.file_menu = self.menuBar().addMenu("&File")
        
        save_plot_action = self.create_action("&Save graphics",
            shortcut="Ctrl+G", slot=self.save_plot, 
            tip="Save the plot")

        load_data_action = self.create_action("&Load data",
            shortcut="Ctrl+L", slot=self.load_data, 
            tip="Load data from CSV")
        
        save_data_action = self.create_action("&Save data",
            shortcut="Ctrl+S", slot=self.save_data, 
            tip="Save data to CSV")
        
        quit_action = self.create_action("&Quit", slot=self.close, 
            shortcut="Ctrl+Q", tip="Close the application")
        
        self.add_actions(self.file_menu, 
            (load_data_action, save_data_action, save_plot_action , None, quit_action))
        
        self.help_menu = self.menuBar().addMenu("&Help")
        about_action = self.create_action("&About", 
            shortcut='F1', slot=self.on_about, 
            tip='About the demo')
        
        self.add_actions(self.help_menu, (about_action,))

    def add_actions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)

    def create_action(  self, text, slot=None, shortcut=None, 
                        icon=None, tip=None, checkable=False, 
                        signal="triggered()"):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action


def main():
    app = QApplication(sys.argv)
    form = AppForm()
    form.show()
    form.raise_()
    app.exec_()


if __name__ == "__main__":
    main()




