#!/usr/bin/env python
import numpy as np
import matplotlib.pyplot as plt
import cv2

from dataclasses import dataclass
from typing import Any, List

@dataclass
class Filter:
  psi: float
  filter: Any

def build_filters():
  filters = []
  ksize = 31

  start = 0
  end = np.pi

  for psi in np.arange(start, end, (end - start) / 16):
    theta = 0.0
    sigma = 6.0
    lambd = 31
    kern = cv2.getGaborKernel((ksize, ksize), sigma, theta, lambd, 0.5, psi, ktype=cv2.CV_32F)
    kern /= 1.5*kern.sum()
    filters.append(Filter(psi,kern))
  return filters

if __name__ == '__main__':
  filters: List[Filter] = build_filters()
  fig, axes = plt.subplots(ncols=4, nrows=4)

  for ida, row in enumerate(axes):
    for idr, ax in enumerate(row):
      f = filters[ida*4+idr]
      ax.set_title("Phase: {:2f}".format(f.psi))
      ax.imshow(f.filter)

  plt.show()

