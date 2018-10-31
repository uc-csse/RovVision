# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import matplotlib.pyplot as plt
from matplotlib.widgets import Button,LassoSelector,TextBox
from matplotlib.path import Path
import numpy as np
import pickle,os

def fname_format(path,fnum):
    return '{}/{:08d}.pkl'.format(path,fnum)

def is_data_file(path,fnum):
    return os.path.isfile(fname_format(path,fnum))

class Polygon:
    def __init__(self,imgs_raw,path,fnum):
        self.imgs_raw=imgs_raw
        self.path=path
        self.fnum=fnum
        self.data_fname=fname_format(path,fnum)
        fig=plt.figure(str(fnum))
        self.sfigs=[]
        self.sfigs+=[plt.subplot(1,2,1)]

        plt.imshow(imgs_raw[0])
        self.sfigs+=[plt.subplot(1,2,2)]
        plt.imshow(imgs_raw[1])
        self.verts_list=[None]*len(imgs_raw)
        self.lasssos = [ LassoSelector(ax, self.on_select, button=3 ) for ax in self.sfigs ]
        
        
        axsave = plt.axes([0.8, 0.05, 0.1, 0.075])
        bsave = Button(axsave, 'Save')
        bsave.on_clicked(self.save)
        
        axadd = plt.axes([0.7, 0.05, 0.1, 0.075])
        badd = Button(axadd, 'Add')
        badd.on_clicked(self.add)

        axdel = plt.axes([0.6, 0.05, 0.1, 0.075])
        bdel = Button(axdel, 'Del')
        bdel.on_clicked(self.delete)

        cid = fig.canvas.mpl_connect('button_press_event', self.onclick)

        axbox = plt.axes([0.1, 0.05, 0.45, 0.075])
        self.text_box = TextBox(axbox, '', initial='?')
        #text_box.on_submit(submit)

        try:
            self.object_list=pickle.load(open(self.data_fname,'rb'))
        except:
            print('no data file for fnum=',fnum)
            self.object_list=[]
        self.objects_hdls=None
        self.draw_objs()

        self.selected_obj_ind=-1

        plt.show()

    def on_select(self,verts):
        print('selecing in',self.last_ind_ax)
        verts.append(verts[0])
        #verts=Path(verts,closed=True).cleaned().vertices
        self.verts_list[self.last_ind_ax]=verts

    def draw_objs(self,selected=-1):
        if self.objects_hdls is not None:
            for h in self.objects_hdls:
                #print('----',h)
                h[0].remove()
        
        self.objects_hdls=[]

        h=self.objects_hdls

        for ind,obj in enumerate(self.object_list):
            for find,subp in enumerate(self.sfigs):
                data = obj['pts'][find]
                if data is not None:
                    xs,ys=np.array(data).T
                    h.append(subp.plot(xs,ys,'y'))
                    h.append(subp.plot(xs[0],ys[0],'or' if selected==ind else 'oy',alpha=0.5))

    def get_closest(self,x,y,ax_ind):
        max_ind=-1
        max_val=30 #minmal distance to accept click
        for ind,obj in enumerate(self.object_list):
            vrts= obj['pts'][ax_ind]
            if vrts is not None:
                d = abs(vrts[0][0]-x) + abs(vrts[0][1]-y)
                if d< max_val:
                    max_val=d
                    max_ind=ind
        return max_ind

    def delete(self,event):
        if self.selected_obj_ind != -1:
            self.object_list.pop(self.selected_obj_ind)
            self.selected_obj_ind=-1
            self.verts_list=[None]*len(self.verts_list)
            self.draw_objs()
            plt.draw()
    
    def save(self,event):
        with open(self.data_fname,'wb') as fd:
            pickle.dump(self.object_list,fd)



    def add(self,event):
        #import pdb;pdb.set_trace()
        if any(self.verts_list):
            obj = {}
            obj['pts'] = self.verts_list.copy()
            obj['desc'] = self.text_box.text
            self.object_list.append(obj)
            print('len of object_list',len(self.object_list))
            self.draw_objs() 
            plt.draw()
            self.verts_list=[None]*len(self.verts_list)


    def onclick(self,event):
        #print('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
        #          ('double' if event.dblclick else 'single', event.button,
        #                     event.x, event.y, event.xdata, event.ydata))
        ind=self.sfigs.index(event.inaxes) if event.inaxes in self.sfigs else -1
        print('inaxes',ind)
        x,y=event.xdata,event.ydata
        #self.sfigs[ind].plot(x,y,'or')
        if ind >= 0:
            self.last_ind_ax=ind
            cind=self.get_closest(x,y,ind)
            self.selected_obj_ind=cind
            if cind>-1:
                self.draw_objs(cind)
                self.text_box.set_val(self.object_list[cind]['desc'])
                plt.draw()
            
        #plt.draw()
        

def plot_raw_images(imgs_raw,path,fnum):
    Polygon(imgs_raw,path,fnum)


def plot_graphs(md_hist,vis_hist):
    fnums=[md['fnum'] for md in md_hist]
    fb_cmd=[md['fb_cmd'] for md in md_hist]
    js_gain=np.array([md['js_gain'] for md in md_hist]).reshape((-1,1))
    fb_pid=np.array([md['fb_pid'] for md in md_hist])*1000*js_gain
    lr_cmd=[md['lr_cmd'] for md in md_hist]
    lr_pid=np.array([md['lr_pid'] for md in md_hist])*1000*js_gain

    ranges=np.array([(vs['fnum'],vs['range']) for vs in vis_hist])
    avg_ranges=np.array([(vs['fnum'],vs['range_avg']) for vs in vis_hist if 'range_avg' in vs])
    dxs=np.array([(vs['fnum'],vs['dx']) for vs in vis_hist if 'dx' in vs])
    

    plt.figure('commands')
    ax=plt.subplot(3,2,1)
    plt.title('fb')
    plt.plot(fnums,fb_cmd,'-.')
    plt.plot(fnums,-fb_pid) #- since the direction is -
    plt.legend(list('cpid'))
    plt.subplot(3,2,3,sharex=ax)
    plt.title('lr')
    plt.plot(fnums,lr_cmd,'-.')
    plt.plot(fnums,-lr_pid)
    plt.legend(list('cpid'))
    plt.subplot(3,2,5,sharex=ax)
    plt.title('horizontal gain')
    plt.plot(fnums,js_gain)
    
    plt.subplot(3,2,2,sharex=ax)
    plt.title('ranges')
    plt.plot(ranges[:,0],ranges[:,1])
    plt.plot(avg_ranges[:,0],avg_ranges[:,1])

    if len(dxs)>0:
        plt.subplot(3,2,4,sharex=ax)
        plt.title('dx')
        plt.plot(dxs[:,0],dxs[:,1])


    plt.show()
