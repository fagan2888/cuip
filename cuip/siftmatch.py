"""
siftmatch.py
Author: Chris Prince [cmp670@nyu.edu]
Date: 25 May 2016
"""

import cv2
import numpy as np
import pylab as pl

def drawMatches(img1, kp1, img2, kp2, matches):
    """
        Adapted from Ray Phan's code at
        http://stackoverflow.com/questions/20259025/module-object-has-no-attribute-drawmatches-opencv-python

        Implementation of cv2.drawMatches as OpenCV 2.4.9
        does not have this function available but it's supported in
        OpenCV 3.0.0

        This function takes in two images with their associated
        keypoints, as well as a list of DMatch data structure (matches)
        that contains which keypoints matched in which images.

        An image will be produced where a montage is shown with
        the first image followed by the second image beside it.

        Keypoints are delineated with circles, while lines are connected
        between matching keypoints.

        img1,img2 - Grayscale
        kp1,kp2 - Detected list of keypoints through any of the OpenCV keypoint
                  detection algorithms
        matches - A list of matches of corresponding keypoints through any
                  OpenCV keypoint matching algorithm
    """
    # Create a new output image that concatenates the two images together
    # (a.k.a) a montage
    rows1 = img1.shape[0]
    cols1 = img1.shape[1]
    rows2 = img2.shape[0]
    cols2 = img2.shape[1]
    out = np.zeros((max([rows1,rows2]),cols1+cols2,3), dtype='uint8')
    # Place the first image to the left
    out[:rows1,:cols1,:] = np.dstack([img1, img1, img1])
    # Place the next image to the right of it
    out[:rows2,cols1:cols1+cols2,:] = np.dstack([img2, img2, img2])
    # For each pair of points we have between both images
    # draw circles, then connect a line between them
    for mat in matches:

        # Get the matching keypoints for each of the images
        img1_idx = mat.queryIdx
        img2_idx = mat.trainIdx
        # x - columns
        # y - rows
        (x1,y1) = kp1[img1_idx].pt
        (x2,y2) = kp2[img2_idx].pt
        # Draw a small circle at both co-ordinates
        # radius 4
        # colour blue
        # thickness = 1
        cv2.circle(out, (int(x1),int(y1)), 4, (255, 0, 0), 1)
        cv2.circle(out, (int(x2)+cols1,int(y2)), 4, (255, 0, 0), 1)
        # Draw a line in between the two points
        # thickness = 1
        # colour blue
        cv2.line(out, (int(x1),int(y1)), (int(x2)+cols1,int(y2)), (255, 0, 0), 1)
    # Show the image
    return out

def surf_match(img1, img2):
    """
    Find features in images img1 and img2 using SURF, then output a new image
    that shows matching features between the two images.
    """

    #There are other algorithms that we can try here too though the
    #implementation will be different.
    surf = cv2.SURF()

    #The paramters in these dictionaries can and probably should be played with
    index_params = dict(algorithm = 1, trees = 5)
    search_params = dict(checks = 20)

    #FLANN is an optimized matcher (versus brute force), so should play with
    #this as well. Maybe brute force is better if we go with multiple
    #subsamples to register image (instead of entire image)
    flann = cv2.FlannBasedMatcher(index_params, search_params)

    #The actual SIFT computations
    kp1, des1 = surf.detectAndCompute(img1, None)
    kp2, des2 = surf.detectAndCompute(img2, None)

    #The actual matching computation
    matches = flann.knnMatch(des1, des2, k = 1)
    #Need to flatten the match array
    m2 = [matches[i][0] for i in range(len(matches))]

    #Now pass the images with their sets of  SIFT keypoints and the map of
    #matches and return the resulting image
    return drawMatches(img1[:,:,0], kp1, img2[:,:,0], kp2, m2)

def sift_match(img1, img2):
    """
    Find features in images img1 and img2 using SIFT, then output a new image
    that shows matching features between the two images.
    """

    #There are other algorithms that we can try here too though the
    #implementation will be different.
    sift = cv2.SIFT()

    #The paramters in these dictionaries can and probably should be played with
    index_params = dict(algorithm = 1, trees = 5)
    search_params = dict(checks = 20)

    #FLANN is an optimized matcher (versus brute force), so should play with
    #this as well. Maybe brute force is better if we go with multiple
    #subsamples to register image (instead of entire image)
    flann = cv2.FlannBasedMatcher(index_params, search_params)

    #The actual SIFT computations
    kp1, des1 = sift.detectAndCompute(img1, None)
    kp2, des2 = sift.detectAndCompute(img2, None)

    #The actual matching computation
    matches = flann.knnMatch(des1, des2, k = 1)
    #Need to flatten the match array
    m2 = [matches[i][0] for i in range(len(matches))]

    #Now pass the images with their sets of  SIFT keypoints and the map of
    #matches and return the resulting image
    return drawMatches(img1[:,:,0], kp1, img2[:,:,0], kp2, m2)

if __name__ == '__main__':
    #Here's my sample image; could replace with a command line option
    img = np.fromfile('/home/cusp/cmp670/cuip2/temp__2014-09-29-125314-29546.raw',
            dtype=np.uint8)
    img = img.reshape(2160,4096,3)[:,:,::-1]
    im4 = surf_match(img[300:800,300:800,:], img)
    pl.imshow(im4)
    #Assumes the Qt4Agg backend in place for matplotlib
    pl.show()

