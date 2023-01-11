import cv2
import numpy as np
from qtpy import QtCore


SHIFT_KEY = cv2.EVENT_FLAG_SHIFTKEY
ALT_KEY = cv2.EVENT_FLAG_ALTKEY
CTRL_KEY = cv2.EVENT_FLAG_CTRLKEY


def _find_exterior_contours(img):
    ret = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    """
    [, contours[, hierarchy[, offset]]]
    """
    if len(ret) == 2:
        return list(ret[0])
    elif len(ret) == 3:
        return list(ret[1])
    raise Exception("Check the signature for `cv2.findContours()`.")


def check_intersection(start_point, end_point, check_point):
    # a[0] = x, a[1] = y
    if (check_point[0] >= start_point[0] and check_point[1] >= start_point[1]) and \
        (check_point[0] <= end_point[0] and check_point[1] <= end_point[1]):
        return True
    return False


class SelectionWindow:
    def __init__(self, img, connectivity=4, tolerance=32):
        # self.name = name
        h, w = img.shape[:2]
        self.img = img
        # print("img:", self.img.shape)
        self.img_copy = img.copy()
        self.rectangle = img
        # print("original rectangle:", self.rectangle.shape)
        # self.draw_rec = False
        self.mask = np.zeros((h, w), dtype=np.uint8)
        self._flood_mask = np.zeros((h + 2, w + 2), dtype=np.uint8)
        self._x = w
        self._y = h
        self._ix = 0
        self._iy = 0
        
        self._flood_fill_flags = (
            connectivity | cv2.FLOODFILL_FIXED_RANGE | cv2.FLOODFILL_MASK_ONLY | 255 << 8
        )  # 255 << 8 tells to fill with the value 255
        # cv.namedWindow(self.name)
        self.tolerance = (tolerance,) * 3
        # cv.createTrackbar(
        #     "Tolerance", self.name, tolerance, 255, self._trackbar_callback
        # )
        # cv.setMouseCallback(self.name, self._mouse_callback)


    # def _trackbar_callback(self, pos):
    #     self.tolerance = (pos,) * 3

    
    def _reset_slidewindow(self):
        self.rectangle = self.img.copy()
        self._y, self._x = self.img.shape[:2]
        self._ix = 0
        self._iy = 0
        self.mask = np.zeros((self._y, self._x), dtype=np.uint8)
        self._flood_mask = np.zeros((self._y + 2, self._x + 2), dtype=np.uint8)


    # def _mouse_callback(self, event, x, y, flags, *userdata):
    #     # if event != cv.EVENT_LBUTTONDOWN:
    #     #     return
    #     start_point = (self._ix, self._iy)
    #     end_point = (self._x, self._y)
    #     check_point = (x,y)
    #     modifier = flags & (CTRL_KEY + ALT_KEY + SHIFT_KEY)
    #     if modifier == 0 and event == cv.EVENT_LBUTTONDOWN:
    #         if check_intersection(start_point, end_point, check_point) == False:
    #             self.draw_rec = False
    #             self.rectangle = self.img_copy.copy()
    #             self._y, self._x = self.img.shape[:2]
    #             self._ix = 0
    #             self._iy = 0
    #             self.mask = np.zeros((self._y, self._x), dtype=np.uint8)
    #             self._flood_mask = np.zeros((self._y + 2, self._x + 2), dtype=np.uint8)
    #     if modifier == CTRL_KEY:
    #         if event == cv.EVENT_LBUTTONDOWN:
    #             self.mask = np.zeros((self._y, self._x), dtype=np.uint8)
    #             self._flood_mask = np.zeros((self._y + 2, self._x + 2), dtype=np.uint8)
    #             self._ix = x
    #             self._iy = y
    #         elif event == cv.EVENT_LBUTTONUP:
    #             self.draw_rec = True
    #             self._x = x
    #             self._y = y
    #             self.rectangle = cv.rectangle(self.img_copy.copy(), (self._ix, self._iy),(self._x, self._y), (255, 38, 0), 1)
    #     elif modifier == (ALT_KEY + SHIFT_KEY):
    #         floodmask = self._floodfill(event, x, y)
    #         self.mask = cv.bitwise_and(self.mask, floodmask)
    #     elif modifier == SHIFT_KEY:
    #         floodmask = self._floodfill(event, x, y)
    #         self.mask = cv.bitwise_or(self.mask, floodmask)
    #     elif modifier == ALT_KEY:
    #         floodmask = self._floodfill(event, x, y)
    #         self.mask = cv.bitwise_and(self.mask, cv.bitwise_not(floodmask))

    #     self._update()
    

    def _shift_key(self, x, y):
        self.rectangle = cv2.rectangle(self.img_copy.copy(), (self._ix, self._iy), (self._x, self._y), (255, 38, 0), 1)
        floodmask = self._floodfill(x, y)
        self.mask = cv2.bitwise_or(self.mask, floodmask)

        return self._contours()
    

    def _alt_key(self, x, y):
        self.rectangle = cv2.rectangle(self.img_copy.copy(), (self._ix, self._iy), (self._x, self._y), (255, 38, 0), 1)
        floodmask = self._floodfill(x, y)
        self.mask = cv2.bitwise_and(self.mask, cv2.bitwise_not(floodmask))

        return self._contours()


    def _floodfill(self, x, y):
        floodmask = None
        self._flood_mask[:] = 0
        cv2.floodFill(
            self.rectangle,
            self._flood_mask,
            (x, y),
            0,
            self.tolerance,
            self.tolerance,
            self._flood_fill_flags,
        )
        floodmask = self._flood_mask[1:-1, 1:-1].copy()
        return floodmask


    def _contours(self):
        ret = _find_exterior_contours(self.mask)

        contours = []

        for x in ret:
            for xx in x:
                for xxx in xx:
                    contours += [QtCore.QPointF(xxx[0], xxx[1])]
        
        return contours
