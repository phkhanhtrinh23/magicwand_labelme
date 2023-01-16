import math
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
        h, w = img.shape[:2]
        self.img = img
        self.img_copy = img.copy()
        self.rectangle = img
        self.mask = np.zeros((h, w), dtype=np.uint8)
        self._flood_mask = np.zeros((h + 2, w + 2), dtype=np.uint8)
        self._x = w
        self._y = h
        self._ix = 0
        self._iy = 0

        self.threshold_distance = 50
        self.threshold_angle = 20
        
        self._flood_fill_flags = (
            connectivity | cv2.FLOODFILL_FIXED_RANGE | cv2.FLOODFILL_MASK_ONLY | 255 << 8
        )  # 255 << 8 tells to fill with the value 255
        self.tolerance = (tolerance,) * 3

    
    def _reset_slidewindow(self):
        self.rectangle = self.img.copy()
        self._y, self._x = self.img.shape[:2]
        self._ix = 0
        self._iy = 0
        self.mask = np.zeros((self._y, self._x), dtype=np.uint8)
        self._flood_mask = np.zeros((self._y + 2, self._x + 2), dtype=np.uint8)
    

    def _shift_key(self, x, y):
        self.rectangle = cv2.rectangle(self.img_copy.copy(), (self._ix, self._iy), (self._x, self._y), (255, 38, 0), 1)
        floodmask = self._floodfill(x, y)
        self.mask = cv2.bitwise_or(self.mask, floodmask)
        
        return self._contours()
    

    def _alt_key(self, x, y):
        self.rectangle = cv2.rectangle(self.img_copy.copy(), (self._ix, self._iy), (self._x, self._y), (255, 38, 0), 1)
        floodmask = self._floodfill(x, y)
        self.mask = cv2.bitwise_and(self.mask, cv2.bitwise_not(floodmask))

        pos = QtCore.QPointF(x, y)

        return self._contours(pos)


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

    
    def distance_between_points(self, point_1, point_2):
        vector = [point_2.x()-point_1.x(), point_2.y()-point_1.y()]
        return math.hypot(vector[0], vector[1])


    def angle_between_points(self, point_1, point_2):
        vector_1 = [point_1.x(), point_1.y()]
        vector_2 = [point_2.x(), point_2.y()]

        unit_vector_1 = vector_1 / (np.linalg.norm(vector_1) + 0.001)
        unit_vector_2 = vector_2 / (np.linalg.norm(vector_2) + 0.001)
        dot_product = np.dot(unit_vector_1, unit_vector_2)
        angle = np.arccos(np.clip(dot_product, -1.0, 1.0))

        return angle * 180 / math.pi
    

    def sort_contours(self, contours, center):
        refvec = [0, 1]
        
        def clockwise_sort(point):
            vector = [point.x() - center.x(), point.y() - center.y()]
            len_vector = self.distance_between_points(center, point)
            
            if len_vector == 0:
                return -math.pi, 0

            # Normalize vector: v/||v||
            normalized = [vector[0]/len_vector, vector[1]/len_vector]

            dotprod  = normalized[0] * refvec[0] + normalized[1] * refvec[1] # x1*x2 + y1*y2
            diffprod = refvec[1] * normalized[0] - refvec[0] * normalized[1] # x1*y2 - y1*x2
            angle = math.atan2(diffprod, dotprod) # angle = arctan2(y, x)

            if angle < 0:
                return 2*math.pi + angle, len_vector

            # first is the angle, but if two vectors have the same angle then 
            # the shorter distance should come first.
            return angle, len_vector

        return sorted(contours, key=clockwise_sort)


    def _contours(self, pos=None):
        ret = _find_exterior_contours(self.mask)

        contours = []
        temp_x, temp_y = 0, 0

        for x in ret:
            for xx in x:
                for xxx in xx:
                    contours += [QtCore.QPointF(xxx[0], xxx[1])]
                    temp_x += xxx[0]
                    temp_y += xxx[1]
        
        # calculate coordinates of "center" point
        temp_x, temp_y = temp_x/len(contours), temp_y/len(contours)
        center = QtCore.QPointF(temp_x, temp_y)

        # calculate the average distance of all points from "center" point
        d = 0
        for point in contours:
            vector = [point.x() - center.x(), point.y() - center.y()]
            d += math.hypot(vector[0], vector[1])
        d = d/len(contours)

        # just keep the point having distance > d from center
        temp_contours = []
        for point in contours:
            vector = [point.x() - center.x(), point.y() - center.y()]
            if math.hypot(vector[0], vector[1]) >= d:
                temp_contours += [point]
        contours = temp_contours

        """
        In case: Alt + Left button
        Description: Delete points
        """
        if pos:
            temp_contours = []
            diff_1 = QtCore.QPointF(center.x()-pos.x(), center.y()-pos.y())
            for point in contours:
                diff_2 = QtCore.QPointF(point.x()-pos.x(), point.y()-pos.y())
                if self.angle_between_points(diff_1, diff_2) <= 45:
                    temp_contours += [point]
            contours = temp_contours
        """
        End case.
        """

        contours = self.sort_contours(contours, center)

        current_contours = []
        temp = None
        
        for i, point in enumerate(contours):
            if temp:
                if i >= 3 and len(current_contours) >= 2:
                    diff_1 = QtCore.QPointF(point.x()-current_contours[-1].x(), point.y()-current_contours[-1].y())
                    diff_2 = QtCore.QPointF(current_contours[-2].x()-current_contours[-1].x(), \
                        current_contours[-2].y()-current_contours[-1].y())
                    if self.angle_between_points(diff_1, diff_2) > self.threshold_angle and \
                        self.distance_between_points(temp, point) > self.threshold_distance:
                        current_contours += [point]
                elif len(current_contours) < 2:
                    current_contours += [point]
            temp = point
        
        return current_contours
