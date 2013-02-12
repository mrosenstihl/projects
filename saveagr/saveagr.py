import matplotlib
import matplotlib.pyplot as P
import numpy as N



class SaveAGR(object):
    def __init__(self):
        self.fname = None
        self.header = ['@version 50122'] # damit wird world beachtet
        self.header = []
        self.custom_colors = []
        self.lineformat = []
        self.labels = []
        self.data_part = []
        self.footer = []
        self.ls_map = {"None":"0", "-":"1", ":":"2", "--":"3", "-.":"4" }
        self.sym_map = {"None":"0", "o":"1", "s":"2", 
                        "d":"3", "D":"4", "2":"5", 
                        "3":"6", "4":"7","1":"8", 
                        "+":"9","x":"10","*":"11"  }
        self.color_map = {"w":"0", "k":"1", "r":"2", "g":"3", "b":"4", "y":"5", "c":"9", "m":"10"  }
        self.scale_map = {"log":"Logarithmic", "linear":"Normal"}
        self._new_colors = []
        self.textscale = 0

    def convert_color(self, color):
        """
        Converts mpl color to grace color
        """
        
        if color not in self.color_map.keys():
            color = [int(i*255) for i in color]
            if color not in self._new_colors:
                # 16 colors are already defined in grace, new colors start with number 16
                color_num = str(len(self._new_colors)+16)
                self._new_colors.append(color)
                r, g, b, alpha = color
                self.custom_colors.append("@map color %s to (%i, %i, %i), \"custom%s\""%(color_num, r, g, b, color_num))
            else:
                color_num = self._new_colors.index(color)+16
        else:
            color_num = self.color_map[color]
        return color_num

    def get_data_part(self, line, line_num=0):
        """
        Extract the data part of the mpl line
        """
        # TODO: errorbars
        x,y = line.get_data()
        self.data_part.append("@target G0.S%i"%line_num)
        for i in xrange(len(x)):
            self.data_part.append("%e %e"%(x[i],y[i]))
        self.data_part.append("&")

    def get_line_format(self, line, line_num=0):
        """
        Get the line format from mpl and convert it to similar grace line format
        """
        mplstyle = line.get_linestyle()
        linestyle =  self.ls_map[mplstyle]
        linewidth =  line.get_linewidth()
        linecolor =  self.convert_color(line.get_color())
        if linestyle != "None":
            self.lineformat.append("@ s%i line linestyle %s"%(line_num, linestyle))
            self.lineformat.append("@ s%i line linewidth %s"%(line_num, linewidth))
            self.lineformat.append("@ s%i line color %s"%(line_num, linecolor))
        
    def get_symbol_format(self, line, line_num=0):
        symstyle =  self.sym_map[line.get_marker()]
        print self.textscale
        symsize =  float(line.get_markersize())
        symedgecolor =  self.convert_color(line.get_markeredgecolor())
        symfacecolor =  self.convert_color(line.get_markerfacecolor())
        if symstyle != "None":
            self.lineformat.append("@ s%i symbol %s"%(line_num, symstyle))
            self.lineformat.append("@ s%i symbol size %f"%(line_num, symsize/10))
            self.lineformat.append("@ s%i symbol color %s"%(line_num, symedgecolor))
            self.lineformat.append("@ s%i symbol fill color %s"%(line_num, symfacecolor))
            self.lineformat.append("@ s%i symbol fill pattern 1"%line_num)
    
    def get_legend(self,line,line_num=0):
        # TODO: obey matplotlib legend setting, including location, numpoints
        label = line.get_label()
        if not label.startswith('_line'):
            self.header.append("@ s%i legend \"%s\""%(line_num,label))

    def get_xylabels(self, a):
        x = a.get_xlabel()
        xfs = a.xaxis.label.get_fontsize()
        y = a.get_ylabel()
        yfs = a.yaxis.label.get_fontsize()
        tls = a.get_xticklabels()[0].get_size()
        self.header.append("@ xaxis label \"%s\""%x)
        self.header.append("@ xaxis label char size %f"%(xfs*self.textscale))
        self.header.append("@ xaxis ticklabel char size %f"%(tls*self.textscale))
        self.header.append("@ yaxis label \"%s\""%y)
        self.header.append("@ yaxis label char size %f"%(yfs*self.textscale))
        self.header.append("@ yaxis ticklabel char size %f"%(tls*self.textscale))
        
        
    def get_title(self,a):
        t = a.get_title()
        fontsize = float(a.title.get_fontsize())
        self.header.append("@ title \"%s\""%t)
        self.header.append("@ title size %f"%(fontsize*self.textscale))
        
    def get_figprops(self, fig):
        # TODO:
        # - ticks, tick label, tck font etc.
        # - errorbar
        x_inches, y_inches = fig.get_size_inches()
        # warum auch immer, xmgrace verwendet bei x11 97 dpi per default
        width, height = (int(x_inches*72), int(y_inches*72))
        longest = max(x_inches,y_inches)
        ax_pos = fig.gca().get_position()
        world_xmin,world_xmax,world_ymin,world_ymax = fig.gca().axis() 
        x_scale = fig.gca().xaxis.get_scale()
        y_scale = fig.gca().yaxis.get_scale()

        x_min = longest/x_inches*ax_pos.min[0]
        y_min = longest/y_inches*ax_pos.min[1]
        x_max = longest/x_inches*ax_pos.max[0]
        y_max = longest/y_inches*ax_pos.max[1]

        self.header.append("@ page size %i, %i"%(width, height))
        self.header.append("@ view %f, %f, %f, %f"%(y_min,x_min, y_max, x_max))
        # wird nicht honoriert, evtl mit ""@with g0"" ?
        self.header.append("@ world xmin %f "%world_xmin)
        self.header.append("@ world ymin %f "%world_ymin)
        self.header.append("@ world xmax %f "%world_xmax)
        self.header.append("@ world xmax %f "%world_ymax)
        self.header.append("@ xaxes scale %s"%(self.scale_map[x_scale]))
        self.header.append("@ yaxes scale %s"%(self.scale_map[y_scale]))
        MAGIC_FONT_SCALE = 0.028 # das kommt aus t1fnts.h von XMGrace
        self.textscale = 1.0/longest

    def clear(self):
        for i in [self.header, self.custom_colors, self.lineformat, self.labels, self.data_part, self.footer]:
            i=[]
            print i

    def saveagr(self, fname):
        self.fname = fname
        self.clear()
        fig = P.gcf()
        self.get_figprops(fig)
        ax = P.gca()
        self.get_xylabels(ax)
        self.get_title(ax)
        all_lines = ax.get_lines()
        # errorbars?
        caplines = []
        errorbars = ax.findobj(matplotlib.collections.LineCollection)
        # find the proper cap lines
        for errorbar in errorbars:
            errb = errorbar.get_paths()
            y_err = N.zeros((2,len(errb)))
            x_pos = N.zeros(len(errb))
            # get the errorbars 
            for i,err in enumerate(errb):
                y_err[:,i] = err.vertices.T[1]
                if err.vertices.T[0,0] == err.vertices.T[0,1]:
                    x_pos[i] = err.vertices.T[0,0]
                else:
                    print err.vertices.T[0,0] == err.vertices.T[0,1]
                    print y_err
                    print N.diff(err.vertices.T[0])
                    raise ValueError, "What??"
            # now remove the line where the end of errorbars match with the y values, this are the end caps
            for line in all_lines:
                    y = line.get_ydata()
                    if line.get_marker() == '_':
                        if N.all((y_err[0]-y) == 0) or N.all((y_err[1]-y)==0):
                            caplines.append(line)

        # loop over all lines except error caps and linecollections
        for i, line in enumerate((l for l in all_lines if l not in (caplines or errorbars))):
            self.get_line_format(line, line_num=i)
            self.get_symbol_format(line, line_num=i)
            self.get_legend(line, line_num=i)
            self.get_data_part(line,line_num=i)
        self.write()
    

    def write(self):
        f = open(self.fname,'w')
        #f.write(header)
        for i in [self.header, self.custom_colors, self.lineformat, self.labels, self.data_part, self.footer]:
            f.writelines([x + "\n" for x in i])
        f.close()

if __name__ == '__main__':
    print "TODO: test/demo"
    pass
