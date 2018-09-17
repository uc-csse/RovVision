# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4


def imggetter():
    import glob,re
    #image_fmt='webp'
    #lefts=glob.glob(load+'/l*.png')
    lefts=glob.glob(load+'/l*.'+image_fmt)
    lefts.sort()
    rights=glob.glob(load+'/r*.'+image_fmt)
    rights.sort()
    for l,r in zip(lefts,rights):
        fnum = int(re.findall('0[0-9]+',l)[0])
        yield fnum,cv2.imread(l),cv2.imread(r)


imgget=imggetter()
### fmt_cnt_l,imgl,imgr=imgget.__next__()
###                fmt_cnt_r=fmt_cnt_l
###                img=imgl

