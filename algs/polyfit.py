# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
import numpy as np
def fit(X33):
    X, Y = np.meshgrid([-1,0,1], [-1,0,1], copy=False)

    X = X.flatten()
    Y = Y.flatten()

    A = np.vstack([X**2, X*Y, Y**2 , X , Y , np.ones(len(X))]).T
    B = X33.flatten()

    cf, r, rank, s = np.linalg.lstsq(A, B, rcond=None)
    #print(cf)
    #super sumple
    ax,ay=np.linspace(-1, 1, 11),np.linspace(-1, 1, 11)
    XX,YY = np.meshgrid(ax,ay,copy=False)
    ZZ = cf[0]*(XX**2)+cf[1]*(XX*YY)+cf[2]*(YY**2)+cf[3]*XX+cf[4]*YY# no need for +cf[5]
    if 0:
        import pylab
        pylab.imshow(ZZ)
        pylab.show()
    ix,iy = np.unravel_index(np.argmax(ZZ, axis=None), ZZ.shape)
    return ax[ix],ay[iy]

if __name__=='__main__':
    t=np.zeros((3,3))
    t[1,1]=1
    print(fit(t))
    
    t=np.zeros((3,3),dtype='uint8')
    t[2,0]=5
    t[2,1]=8
    t[2,2]=1
    print(fit(t))
    
     
