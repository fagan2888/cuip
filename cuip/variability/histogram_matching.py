from __future__ import print_function

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy.misc import imread
from skimage.data import chelsea, coffee
# -- CUIP imports
from plot import plot_match

plt.style.use("ggplot")


def channel_cdf(channel):
    """Calculate channel's cdf.
    Args:
        Channel (array) - 2D image channel.
    Returns:
        cdf (array) - Normalized cdf (256 bins).
    """
    # -- Calculate cdf.
    cdf = np.cumsum(np.histogram(channel.flatten(), 256, [0, 255])[0])
    # -- Normalize.
    cdf = cdf.astype(float) / cdf.max()
    return cdf


def channel_vals(img_cdf, ref_cdf):
    """Map values from img_cdf to ref_cdf.
    Args:
        ref_cdf (array) - reference channel cdf.
        img_cdf (array) - target channel cdf.
    Returns:
        vals (array) - mapped values for 256 values.
    """
    # -- Map img values to ref.
    vals = [list(ref_cdf >= img_cdf[ii]).index(True) for ii in range(len(img_cdf))]
    return np.array(vals).astype(float)


def channel_match(channel, vals):
    """Replace values in channel with mapped values.
    Args:
        channel (array) - image channel.
        vals (array) - mapped values for 256 values.
    Returns:
        match (array) - image with remapped values.
    """
    # -- Empty array to fill with mapped values.
    match = np.zeros(channel.shape, dtype=np.uint8)
    # -- Map all values in channel to matched values.
    for ii in range(256):
        match[channel == ii] = vals[ii]
    return match


def rgb_cdfs(img):
    """Return cdfs for all img channels.
    Args:
        img (array) - 3D image array.
    Returns:
        cdfs (array).
    """
    cdfs = [channel_cdf(rgb_select(img, ii)) for ii in range(3)]
    return cdfs


def rgb_select(img, ii):
    """Select color channel from 2D or 1D image.
    Args:
        img (array) - 3 color image.
        ii (int) - channel to select.
    Returns:
        chan (array) - selected channel.
    """
    # -- 2D RGB image.
    if len(img.shape) == 3:
        chan = img[:, :, ii]
    # -- 1D RGB 'image'.
    elif len(img.shape) == 2:
        chan = img[:, ii]
    else:
        raise ValueError("Invalid image input.")
    return chan


def rgb_match(img, img_cdfs, ref_cdfs):
    """Histogram matching for 3 color images.
    Args:
        img (array) - target image.
        img_cdf (array)
        ref_cdf (array)
    Returns:
        match (array) - histogram matched target image.
    """
    if np.isnan(np.array(img_cdfs).sum()):
        return np.zeros(np.array(img).shape) - 9999
    # -- Find value map.
    vals = [channel_vals(ii, rr) for ii, rr in zip(img_cdfs, ref_cdfs)]
    # -- Map image values.
    match = [channel_match(rgb_select(img, ii), vals[ii]) for ii in range(3)]
    return np.moveaxis(match, 0, -1)


def demo(img=coffee(), ref=chelsea(), figsize=(6, 6)):
    """Demo the histogram matching.
    Args:
        img (array) - RGB image.
        ref (array) - RGB image to use as reference.
        figsize (tup) - plotting size.
    """
    match = rgb_match(img, rgb_cdfs(img), rgb_cdfs(ref))
    plot_match(img, ref, match, figsize=figsize)


def match_lightcurves(lc, outdir):
    """Perform histogram matching for all lightcurve files.
    Args:
        lc (obj) - LightCurve object.
        outdir (str) - directory to save outputs.
    """
    # -- Get lightcurve paths.
    fnames = sorted(os.listdir(lc.path_lig))
    fpaths = [os.path.join(lc.path_lig, fname) for fname in fnames]
    # -- Load reference image and calculate cdfs.
    ref = np.load(fpaths[-1])
    ref = np.ma.array(ref, mask=ref == -9999).astype(int)
    ref_cdfs = rgb_cdfs(ref[14000, :, :])
    # -- For each lightcurve file...
    for ii, fpath in enumerate(fpaths):
        # -- In and out names.
        bname = os.path.basename(fpath)
        # -- If output does not alread exist.
        if not bname in os.listdir(outdir):
            # -- Print status.
            print("LIGHTCURVES: Histogram matching {}                        " \
                .format(bname))
            sys.stdout.flush()
            # -- Load and mask original lightcurve file.
            lightc = np.load(fpath).astype(int)
            lightc = np.ma.array(lightc, mask=lightc == -9999).astype(int)
            # -- Match source colors to reference.
            ll = lightc.shape[0]
            match_lightc = []
            for ii, src in enumerate(lightc):
                print("LIGHTCURVES: Source ({}/{})                           " \
                    .format(ii + 1, ll), end="\r")
                sys.stdout.flush()
                match_lightc.append(rgb_match(src, rgb_cdfs(src), ref_cdfs))
            # -- Save new ligthcurve array.
            np.save(os.path.join(outdir, bname), np.array(match_lightc))


if __name__ == "__main__":
    demo()
    match_lightcurves(lc, os.path.join(lc.path_out, "histogram_matching"))
