# coding: utf-8

from __future__ import division

import cv2
import numpy as np
from scipy.spatial import Delaunay



def get_aabb(pts):
    x, y = np.floor(pts.min(axis=0)).astype(int)
    w, h = np.ceil(pts.ptp(axis=0)).astype(int)
    return x, y, w, h

def get_vertices(pts):
    return Delaunay(pts).vertices

def normalize(img, aabb):
    x, y, w, h = aabb
    img[y:y+h,x:x+w,0] = cv2.equalizeHist(img[y:y+h,x:x+w,0])
    img[y:y+h,x:x+w,1] = cv2.equalizeHist(img[y:y+h,x:x+w,1])
    img[y:y+h,x:x+w,2] = cv2.equalizeHist(img[y:y+h,x:x+w,2])
    return img

def get_mask(pts, shape):
    pts = pts.astype('int32')
    mask = np.zeros(shape, dtype='uint8')
    hull = cv2.convexHull(pts[:,np.newaxis])
    hull = hull.reshape((hull.shape[0], hull.shape[2]))
    cv2.fillConvexPoly(mask, hull, 255)
    return mask.astype(bool)

# NOTE you should use pyaam.texturemapper.TextureMapper instead
def warp_triangles(img, src, dst):
    result = np.zeros(img.shape, dtype='uint8')
    dsize = (img.shape[1], img.shape[0])
    for s, d in zip(src, dst):
        mask = np.zeros(img.shape[:2], dtype='uint8')
        cv2.fillConvexPoly(mask, d.astype('int32'), 255)
        mask = mask.astype(bool)
        M = cv2.getAffineTransform(s.astype('float32'), d.astype('float32'))
        warp = cv2.warpAffine(img, M, dsize, flags=cv2.INTER_LINEAR)
        result[mask] = warp[mask]
    return result

def pca(M, frac, kmax):
    """principal component analysis"""
    enough_samples = M.shape[1] > M.shape[0]  # each column is a sample
    # covariance matrix
    C = M.dot(M.T) if enough_samples else M.T.dot(M) / M.shape[1]
    u, s, vt = np.linalg.svd(C)
    if not enough_samples:
        u = M.dot(u)
    vsum = s[:kmax].sum()
    v = k = 0
    while True:
        v += s[k]
        k += 1
        # retain fraction `frac` of the variance
        if v/vsum >= frac:
            break
    k = min(k, kmax)
    return u[:,:k]