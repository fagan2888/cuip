#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import numpy as np
import matplotlib.pyplot as plt
import scipy.ndimage as nd
import scipy.ndimage.measurements as spm
import uo_tools as ut

def locate_sources(img, hpf=False):
    """
    Extract sources from an image.
    """

    # -- convert to luminosity (high pass filter if desired)
    hpL = (img if not hpf else ut.high_pass_filter(img, 10)).mean(-1)

    # -- get medians and standard deviations of luminosity images
    med = np.median(hpL)
    sig = hpL.std()
    
    # -- get the thresholded images
    thr = hpL > (med + 5.0*sig)

    # -- label the sources
    labs = spm.label(thr)

    # -- get the source sizes
    lsz = spm.sum(thr, labs[0], range(1, labs[1]+1))

    # -- get the positions of the sources
    ind = (lsz > 25.) & (lsz < 400.) 

    return np.array(spm.center_of_mass(thr, labs[0], 
                                       np.arange(1, labs[1]+1)[ind])).T



def get_catalog():
    """
    Return the row/col positions of the catalog sources.

    WARNING: These centroids were identified with a saturated image 
    (November 2, 2013, close to 23:00).  A new catalog should be made 
    with an UNSATURATED image!!!
    """

    rr_cat = np.array([1529.53134328, 1492.16197183, 1490.35830619,
                       1552.85046729, 1587.90461538, 1618.61538462,
                       1651.09454545])
    cc_cat = np.array([1384.45373134, 1378.35211268, 1434.78175896,
                       1480.40809969, 1570.04307692, 1629.33216783,
                       1753.47272727])

    return rr_cat, cc_cat



if __name__=="__main__":

    try:
        img0
    except:
        # -- read in the images
        print("reading raw images...")
        dpath  = "../data"
        fname0 = "oct08_2013-10-25-175504-70917.raw"
        fname1 = "temp__2014-10-31-184833-19155.raw"
        img0   = ut.read_raw(dpath, fname0)
        img1   = ut.read_raw(dpath, fname1)
    
        # -- get positions of the sources
        print("getting positions of apropriately sized sources...")
        t0 = time.time()
        rr1, cc1 = locate_sources(img1)
        print("source extraction time: {0}s".format(time.time()-t0))

    # -- get the catalog positions and distances (squared)
    rr_cat, cc_cat = get_catalog()
    dcat  = np.sqrt(((rr_cat[0] - rr_cat)**2 + (cc_cat[0] - cc_cat)**2)[1:])
    dcatm = np.sqrt((rr_cat[:, np.newaxis] - rr_cat)**2 + 
                    (cc_cat[:,np.newaxis] - cc_cat)**2)

    # -- find the pairwise distance (squared) of all points
    t0 = time.time()
    dist = np.sqrt((rr1[:, np.newaxis] - rr1)**2 + 
                   (cc1[:,np.newaxis] - cc1)**2)

    # -- trim rows that do not have that distance distribution
    buff = 10
    pts  = []

    # -- get all possible points
    allind = np.arange(dist.shape[0])
    p0ind  = allind.copy()
    p1ind  = allind.copy()
    p2ind  = allind.copy()
    p6ind  = allind.copy()

    sub    = dist.copy()
    dcat   = np.sqrt(((rr_cat[0] - rr_cat)**2 + (cc_cat[0] - cc_cat)**2))
    dcat   = dcat[dcat>0]
    for tdist in dcat:
        tind  = (np.abs(sub - tdist) < buff).any(1)
        sub   = sub[tind]
        p0ind = p0ind[tind]

    sub    = dist.copy()
    dcat   = np.sqrt(((rr_cat[1] - rr_cat)**2 + (cc_cat[1] - cc_cat)**2))
    dcat   = dcat[dcat>0]
    for tdist in dcat:
        tind  = (np.abs(sub - tdist) < buff).any(1)
        sub   = sub[tind]
        p1ind = p1ind[tind]


    sub    = dist.copy()
    dcat   = np.sqrt(((rr_cat[2] - rr_cat)**2 + (cc_cat[2] - cc_cat)**2))
    dcat   = dcat[dcat>0]
    for tdist in dcat:
        tind  = (np.abs(sub - tdist) < buff).any(1)
        sub   = sub[tind]
        p2ind = p2ind[tind]


    sub    = dist.copy()
    dcat   = np.sqrt(((rr_cat[6] - rr_cat)**2 + (cc_cat[6] - cc_cat)**2))
    dcat   = dcat[dcat>0]
    for tdist in dcat:
        tind  = (np.abs(sub - tdist) < buff).any(1)
        sub   = sub[tind]
        p6ind = p6ind[tind]


    dcat0 = np.sqrt(((rr_cat[0] - rr_cat)**2 + (cc_cat[0] - cc_cat)**2))
    dcat1 = np.sqrt(((rr_cat[1] - rr_cat)**2 + (cc_cat[1] - cc_cat)**2))
    dcat2 = np.sqrt(((rr_cat[2] - rr_cat)**2 + (cc_cat[2] - cc_cat)**2))

    good01 = []
    for ii in p0ind:
        for jj in p1ind:
            if np.abs(dist[ii,jj]-dcat0[1])<10:
                good01.append([ii,jj])

    good012 = []
    for ii,jj in good01:
        for kk in p2ind:
            flag02 = np.abs(dist[ii,kk]-dcat0[2])<10
            flag12 = np.abs(dist[jj,kk]-dcat1[2])<10
            if flag02 and flag12:
                good012.append([ii,jj,kk])

    good0126 = []
    for ii,jj,kk in good012:
        for mm in p6ind:
            flag06 = np.abs(dist[ii,mm]-dcat0[6])<10
            flag16 = np.abs(dist[jj,mm]-dcat1[6])<10
            flag26 = np.abs(dist[kk,mm]-dcat2[6])<10
            if flag06 and flag16 and flag26:
                good0126.append([ii,jj,kk,mm])

    p0s, p1s, p2s, p6s = np.array(good0126).T

    # -- find the delta angles of the first 2 pairs
    theta01 = np.arccos((rr1[p0s]-rr1[p1s])/dist[p0s,p1s])
    theta02 = np.arccos((rr1[p0s]-rr1[p2s])/dist[p0s,p2s])
    dtheta  = (theta01 - theta02)*180./np.pi

    theta01_cat = np.arccos((rr_cat[0]-rr_cat[1])/dcat0[1])
    theta02_cat = np.arccos((rr_cat[0]-rr_cat[2])/dcat0[2])
    dtheta_cat  = (theta01_cat - theta02_cat)*180./np.pi

    # -- choose the closest delta theta
    guess = np.array(good0126[np.abs(dtheta-dtheta_cat).argmin()])

    print("pattern localization time is {0}".format(time.time() - t0))



    # -- calculate the offset and rotation
    t0 = time.time()
    rrr0, ccc0 = rr_cat[np.array([0,1,2,6])], cc_cat[np.array([0,1,2,6])]
    rrr1, ccc1 = rr1[guess], cc1[guess]

    roff  = img0.shape[0]//2
    coff  = img0.shape[1]//2
    rrr0 -= roff
    rrr1 -= roff
    ccc0 -= coff
    ccc1 -= coff

    mones      = np.zeros(rrr0.size*2+1)
    mones[::2] = 1.0

    pm         = np.zeros([rrr0.size*2,4])
    pm[::2,0]  = rrr0
    pm[1::2,0] = ccc0
    pm[::2,1]  = -ccc0
    pm[1::2,1] = rrr0
    pm[:,2]    = mones[:-1]
    pm[:,3]    = mones[1:]

    bv         = np.zeros([rrr0.size*2])
    bv[::2]    = rrr1
    bv[1::2]   = ccc1

    pmTpm = np.dot(pm.T,pm)
    av    = np.dot(np.linalg.inv(pmTpm),np.dot(pm.T,bv))

    dr, dc = av[-2:]
    dtheta = np.arctan2(av[1],av[0])*180./np.pi

    print("time to solve for orientation: {0}s".format(time.time()-t0))

    # -- test rotation
    rot   = nd.interpolation.rotate(img0.mean(-1), dtheta, reshape=False)
    rot   = nd.interpolation.shift(rot, [dr,dc])
    scl1  = img1.mean(-1)
    scl1 *= rot.mean()/scl1.mean()

    comp  = np.dstack([scl1.clip(0,255).astype(np.uint8),
                       np.zeros(img1.shape[:2],dtype=np.uint8),
                       rot.clip(0,255).astype(np.uint8)])

    # -- overlay
    plt.close("all")
    fig, ax = plt.subplots()
    ax.imshow(comp)
    ax.axis("off")
    fig.canvas.draw()
    plt.show()


    # figure()
    # plot(cc1[p0s],rr1[p0s],'ro',ms=16)
    # plot(cc1[p1s],rr1[p1s],'bo',ms=13)
    # plot(cc1[p2s],rr1[p2s],'go',ms=10)
    # plot(cc1[p6s],rr1[p6s],'mo',ms=7)
    # imshow(img1)



    # # -- plot guess for points 0,1,2,6
    # fig, ax = plt.subplots()
    # ax.plot(cc1[guess], rr1[guess], 'ro')
    # ax.imshow(img1)
    # fig.canvas.draw()
    # plt.show()
