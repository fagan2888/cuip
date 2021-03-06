import multiprocessing as mpc
import itertools
import os, sys
import numpy as np
import matplotlib.pyplot as plt
import pickle as pkl
import pylab as pl
from findImageSize import findsize
from scipy.ndimage.filters import gaussian_filter as gf
from joblib import Parallel, delayed
from joblib.pool import has_shareable_memory
#from plm_images import *

MAXPROCESSES = 5
OUTPUTDIR = "./outputs/"
LIM = 15

try:
    DST_WRITE = os.environ['DST_WRITE']
except KeyError:
    DST_WRITE =os.environ['HOME']


class RawImages:
    def __init__(self, fl=None,  lim=-1):
        fl = [f.strip() for f in fl if f.strip().endswith('.raw')][:lim]
        fl0 = os.path.join(DST_WRITE,fl[0])
        self.imsize = findsize(fl0, 
                      filepattern = '-'.join(fl0.split('/')[-1].\
                                             split('.')[0].split('-')[:-2]),
                               outputdir = OUTPUTDIR)
        
        self.imgs = np.zeros([len(fl), self.imsize['nrows'], 
                              self.imsize['ncols'],
                              self.imsize['nbands']])    
        for i,f in enumerate(fl):    
            self.imgs[i] = self.readraw(os.path.join(DST_WRITE,f))

    def readraw(self, imfile):
        rgb = np.fromfile(imfile, dtype=np.uint8).clip(0, 255).\
            reshape(self.imsize['nrows'],
                    self.imsize['ncols'],
                    self.imsize['nbands']).astype(float)
        return rgb

def subforg(frames):
#image loop
    #lf must be odd
    #frames = range(indx - boxsize, ii) + range(indx + 1, ii + boxsize + 1)
    lf = int(len(frames) / 2)
    print('working on {0}'.format(ii), frames)
    dif = (- 1.0 * np.concatenate([frames[:lf], 
                                   frames[(lf+1):]]) + 1.0 * frames[lf])
    #for jj, fr in enumerate(frames):
    #    dif[jj] = 1.0 * raw.imgs[ii] - 1.0 * raw.imgs[fr]
    diffs = abs(dif).min(0)
    return diffs

# -- get the file list
#fl = pkl.load(open(os.path.join(os.environ['DST_WRITE'],'filelist.pkl'),'rb'))
fl = (open(os.path.join(DST_WRITE, 'filelist.txt'), 'rb')).readlines()

# -- get the raw images
raw = RawImages(fl=fl, lim=LIM)
# set the image numbers
lim = LIM-5 if LIM > 0 else len(fl)-5

# -- initialize the the difference image list
difs = np.zeros([lim] + list(raw.imgs[0].shape))
dif  = np.zeros([10] + list(raw.imgs[0].shape))


# -- loop through the images
nps = min(mpc.cpu_count() - 1 or 1, MAXPROCESSES)
#pool = mpc.Pool(processes=nps)
print([raw.imgs[i-5:i+6].flatten().shape for i in range(5, lim)])
#sys.exit()
#tmp = pool.map(subforg, itertools.izip([raw.imgs[i-5:i+6] for i in range(5, lim)], 
#              itertools.repeat(5)))
#pool.close()
#pool.join()

Parallel(n_jobs=nps)(
        delayed(sum(raw.imgs[i-5:i+6]) for i in range(5, lim)))
tmp = np.zeros(100)
difs = tmp 

#calc, itertools.izip(range(NM0, nm), itertools.repeat(second_args)))  # for i in range(nm): result[i] = f(i, second_args)

#for ii in range(5, lim):
#    difs[ii] = subforg(ii, raw, difs[ii])
#difs = difs[5:]

# -- save figures to file
im = pl.imshow(difs[0][:,:,0],clim=[0,5])
for ii in range(len(difs)):
    im.set_data(difs[ii][:,:,0])
    im.set_clim([0,5])
    pl.draw()
    pl.show()
    pl.savefig(OUTPUTDIR + '/difs_'+str(ii).zfill(3)+'.png',clobber=True)


# -- save panel figures to file
pl.figure(2,figsize=[15,15])
pl.subplot(211)
imt = pl.imshow(raw.imgs[5])
pl.axis('off')
pl.subplot(212)
imb = pl.imshow(difs[0][:,:,0],clim=[0,5])
pl.axis('off')
pl.subplots_adjust(0.05,0.05,0.95,0.95,0.05,0.05)
#for ii,jj in enumerate(range(28,42)):
for ii,jj in enumerate(range(5, lim)):
    imt.set_data(raw.imgs[jj])
    pl.draw()
    imb.set_data(difs[ii][:,:,0])
#    imb.set_data(difs[jj-5][:,:,0])
    pl.clim([0,5])
    pl.draw()
    pl.savefig(OUTPUTDIR + '/difs_imgs_' + str(ii).zfill(3) + 
               '.png',clobber=True)



