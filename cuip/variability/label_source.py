#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import numpy as np
import geopandas as gp
import scipy.ndimage.measurements as ndm

# -- read in the labels
print("getting labels...")
nrow = 2160
ncol = 4096
buff = 20
wins = os.path.join(os.getenv("CUIP_SUPPLEMENTARY"), "window_labels.out")
srcs = np.zeros((nrow, ncol), dtype=bool)
srcs[buff:-buff, buff:-buff] = np.fromfile(wins, int) \
    .reshape(nrow - 2 * buff, ncol - 2 * buff) \
    .astype(bool)
labs = ndm.label(srcs)
nlab = labs[1]

# -- get source locations
print("getting source locations...")
rr, cc = np.array(ndm.center_of_mass(labs[0] > 0, labs[0], 
                                     np.arange(1, nlab + 1))).T \
                                     .round().astype(int)


# -- get the BBL labels
bname = os.path.join(os.getenv("CUIP_SUPPLEMENTARY"), 
                     "12_3_14_bblgrid_clean.npy")
bbls  = np.zeros((nrow, ncol), dtype=int)
bbls[buff:-buff, buff:-buff] = np.load(bname)


# -- label each source with BBL
src_bbls = bbls[rr, cc]


# -- get type of building from PLUTO data
pname = os.path.join(os.getenv("CUIP_SUPPLEMENTARY"), "pluto", "mappluto", 
                     "Manhattan", "MNMapPLUTO.shp")
pluto = gp.GeoDataFrame.from_file(pname)
pluto.set_index(pluto.BBL.astype(int), inplace=True)
src_landuse = np.array([0.0 if i == 0 else int(pluto.ix[i].LandUse) for i in 
                        src_bbls])

foo = []
bad = []
for ii in src_bbls:
    try:
        foo.append(pluto.ix[ii].LandUse)
    except:
        bad.append(ii)
        foo.append(0)


# -- write labels to file
