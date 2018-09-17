# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
# extructed from v3d.py code
#                if args.calc_disparity:
#                    disparity = stereo.compute(preisterproc(imgl),preisterproc(imgr))
#                    disparityu8 = np.clip(disparity,0,255).astype('uint8')
#
                ######################################################################
#disparity from left image to right image

def avg_disp_win(disp,centx,centy,wx,wy,tresh,min_dis=50):
    win=disp[centy-wy//2:centy+wy//2,centx-wx//2:centx+wx//2]
    winf=win.flatten()
    winf=winf[winf>min_dis]
    if len(winf)>tresh:
        #hist,bins=np.histogram(winf,20)
        #b=hist.argmax()
        #val=(bins[b]+bins[b+1])/2
        return winf.mean(),winf.max(),winf.min(),len(winf)
    return -1,-1,-1,-1


def preisterproc(img):
    h=img.shape[0]
    img_shrk = img[h//4:h-h//4,:] 
    #gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #return gray
    return img_shrk

lmap = lambda func, *iterable: list(map(func, *iterable))

# To tun the plotter
#
#    if doplot:
#        plot=ploter()
#        plot.__next__()
#
#    plot.send({'tstemp':time.time()-start,'disp':avg_disp,'corrx':cret[0],'snr_corr':cret[2]})

#    if args.calc_disparity:
#        cv2.imshow('disparity',disparityu8)
#        cv2.rectangle(disparityu8, (centx-wx//2,centy-wy//2) , (centx+wx//2,centy+wy//2) , 255)


def ploter():
    fig = plt.figure(figsize=(8,6))
    ax1 = fig.add_subplot(4, 1, 1)
    ax1.set_title('disp')
    ax2 = fig.add_subplot(4, 1, 2,sharex=ax1)
    ax2.set_title('corrx')
    ax3 = fig.add_subplot(4, 1, 3,sharex=ax1)
    ax3.set_title('snr corr')
    ax4 = fig.add_subplot(4, 1, 4,sharex=ax1)
    ax4.set_title('-')
    ax4.set_ylim(-1,1)
    fig.canvas.draw()   # note that the first draw comes before setting data 
    #fig.canvas.mpl_connect('close_event', handle_close)
    #h1 = ax1.plot([0,1],[0,1],[0,1], lw=3)[0]
    #text = ax1.text(0.8,1.5, '')
    t_start = time.time()
    history=[]

    cnt=0
    mem_len=200
    hdl_list=[]
    alt_ref=None
    last_plot=time.time()
    while True:
        cnt+=1
        data=yield
        if data=='stop':
            break
        history=history[-mem_len:]
        history.append(data) 

        if time.time()-last_plot<0.2 and cnt%10!=0:
            continue        
        last_plot=time.time()

        for hdl in hdl_list:
            hdl[0].remove()
        hdl_list=[]
        
        disp=np.array(lmap(lambda x:x['disp'],history))
        corrx=np.array(lmap(lambda x:x['corrx'],history))
        snr_corr=np.array(lmap(lambda x:x['snr_corr'],history))
        ts=np.array(lmap(lambda x:x['tstemp'],history))

        hdl_list.append(ax1.plot(ts,disp,'-b',alpha=0.5)) 
        hdl_list.append(ax2.plot(ts,corrx,'-b',alpha=0.5)) 
        hdl_list.append(ax3.plot(ts,snr_corr,'-b',alpha=0.5)) 
        ax1.set_xlim(ts.min(),ts.max())        
        #if cnt<100:        
        fig.canvas.draw()
        w=plt.waitforbuttonpress(timeout=0.001)
        if w==True: #returns None if no press
            disp('Button click')
            break
 




