import cv2 as cv
import numpy as np


SHIFT_KEY = cv.EVENT_FLAG_SHIFTKEY
ALT_KEY = cv.EVENT_FLAG_ALTKEY
CTRL_KEY = cv.EVENT_FLAG_CTRLKEY


def _find_exterior_contours(img):
    ret = cv.findContours(img, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    # print("ret:",len(ret), np.asarray(list(ret[0])), ret[1])
    """
    [, contours[, hierarchy[, offset]]]
    """
    if len(ret) == 2:
        return np.asarray(list(ret[0]))
    elif len(ret) == 3:
        return np.asarray(list(ret[1]))
    raise Exception("Check the signature for `cv.findContours()`.")

def check_intersection(start_point, end_point, check_point):
    # a[0] = x, a[1] = y
    if (check_point[0] >= start_point[0] and check_point[1] >= start_point[1]) and \
        (check_point[0] <= end_point[0] and check_point[1] <= end_point[1]):
        return True
    return False


class SelectionWindow:
    def __init__(self, img, name="Magic Wand Selector", connectivity=4, tolerance=32):
        self.name = name
        h, w = img.shape[:2]
        self.img = img
        self.img_copy = img.copy()
        self.rectangle = img
        # print('original rec', self.rectangle.shape)
        self.draw_rec = False
        self.mask = np.zeros((h, w), dtype=np.uint8)
        self._flood_mask = np.zeros((h + 2, w + 2), dtype=np.uint8)
        self._x = w
        self._y = h
        self._ix = 0
        self._iy = 0
        
        self._flood_fill_flags = (
            connectivity | cv.FLOODFILL_FIXED_RANGE | cv.FLOODFILL_MASK_ONLY | 255 << 8
        )  # 255 << 8 tells to fill with the value 255
        cv.namedWindow(self.name)
        self.tolerance = (tolerance,) * 3
        cv.createTrackbar(
            "Tolerance", self.name, tolerance, 255, self._trackbar_callback
        )
        cv.setMouseCallback(self.name, self._mouse_callback)

        

    def _trackbar_callback(self, pos):
        self.tolerance = (pos,) * 3


    def _mouse_callback(self, event, x, y, flags, *userdata):
        # if event != cv.EVENT_LBUTTONDOWN:
        #     return
        start_point = (self._ix, self._iy)
        end_point = (self._x, self._y)
        check_point = (x,y)
        modifier = flags & (CTRL_KEY + ALT_KEY + SHIFT_KEY)
        if modifier == 0 and event == cv.EVENT_LBUTTONDOWN:
            if check_intersection(start_point, end_point, check_point) == False:
                self.draw_rec = False
                self.rectangle = self.img_copy.copy()
                self._y, self._x = self.img.shape[:2]
                self._ix = 0
                self._iy = 0
                self.mask = np.zeros((self._y, self._x), dtype=np.uint8)
                self._flood_mask = np.zeros((self._y + 2, self._x + 2), dtype=np.uint8)
        if modifier == CTRL_KEY:
            if event == cv.EVENT_LBUTTONDOWN:
                self.mask = np.zeros((self._y, self._x), dtype=np.uint8)
                self._flood_mask = np.zeros((self._y + 2, self._x + 2), dtype=np.uint8)
                self._ix = x
                self._iy = y
            elif event == cv.EVENT_LBUTTONUP:
                self.draw_rec = True
                self._x = x
                self._y = y
                # print("Coordinates 1:", x, y)
                self.rectangle = cv.rectangle(self.img_copy.copy(), (self._ix, self._iy),(self._x, self._y), (255, 38, 0), 1)
            # fill one values
            # self.mask_copy = self.mask.copy()
            # if self._ix <= self._x and self._iy <= self._y:
            #     self.mask[self._ix:self._x, self._iy:self._y] = 1
            # elif self._ix <= self._x and self._iy >= self._y:
            #     self.mask[self._ix:self._x, self._y:self._iy] = 1
            # elif self._ix >= self._x and self._iy >= self._y:
            #     self.mask[self._x:self._ix, self._y:self._iy] = 1
            # elif self._ix >= self._x and self._iy <= self._y:
            #     self.mask[self._x:self._ix, self._iy:self._y] = 1
        elif modifier == (ALT_KEY + SHIFT_KEY):
            floodmask = self._floodfill(event, x, y)
            self.mask = cv.bitwise_and(self.mask, floodmask)
        elif modifier == SHIFT_KEY:
            floodmask = self._floodfill(event, x, y)
            # print("floodmask:",floodmask.shape)
            self.mask = cv.bitwise_or(self.mask, floodmask)
            # print("self.mask:",self.mask.shape)
        elif modifier == ALT_KEY:
            floodmask = self._floodfill(event, x, y)
            self.mask = cv.bitwise_and(self.mask, cv.bitwise_not(floodmask))
        # else:
        #     floodmask = self._floodfill(event)
        #     self.mask = floodmask
        self._update()

    def _floodfill(self, event, x, y):
        floodmask = None
        start_point = (self._ix, self._iy)
        end_point = (self._x, self._y)
        check_point = (x, y)
        # print('rec', self.rectangle.shape)
        # print("Coordinates 2:", start_point, end_point, check_point)
        if event == cv.EVENT_LBUTTONDOWN:
            if check_intersection(start_point, end_point, check_point) == True:
                self._flood_mask[:] = 0
                cv.floodFill(
                    self.rectangle,   
                    self._flood_mask,
                    (x, y),
                    0,
                    self.tolerance,
                    self.tolerance,
                    self._flood_fill_flags,
                )
                # print("Floodfill:",cv.floodFill(
                #     self.rectangle,   
                #     self._flood_mask,
                #     (x, y),
                #     0,
                #     self.tolerance,
                #     self.tolerance,
                #     self._flood_fill_flags,
                # ))
                floodmask = self._flood_mask[1:-1, 1:-1].copy()
        return floodmask

    def _update(self):
        """Updates an image in the already drawn window."""
        viz = self.img.copy()
        if self.draw_rec:
            viz = cv.rectangle(viz, (self._ix, self._iy),(self._x, self._y), (255, 38, 0), 5)
        contours = _find_exterior_contours(self.mask)
        # print("contours:", contours)
        viz = cv.drawContours(viz, contours, -1, color=(255,) * 3, thickness=-1)
        viz = cv.addWeighted(self.img, 0.75, viz, 0.25, 0)
        viz = cv.drawContours(viz, contours, -1, color=(255,) * 3, thickness=1)
        f = open("output.txt", "w")
        dic = dict()
        for x in contours:
            for xx in x:
                for xxx in xx:
                    # Center coordinates
                    f.write(f"({xxx[0]}, {xxx[1]})\n")
                    # print("Hello: ", xx)
                    center_coordinates = (xxx[0], xxx[1])

                    # if (xxx[0], xxx[1]) not in dic:
                    #     dic[(xxx[0], xxx[1])] = 1
                    # else:
                    #     print("Duplicate:", (xxx[0], xxx[1]))
                    
                    # Radius of circle
                    radius = 1
                    
                    # Blue color in BGR
                    color = (255, 0, 0)
                    
                    # Line thickness of 2 px
                    thickness = 1
                    
                    # Using cv2.circle() method
                    # Draw a circle with blue line borders of thickness of 2 px
                    viz = cv.circle(viz, center_coordinates, radius, color, thickness)
        f.close()

        self.mean, self.stddev = cv.meanStdDev(self.img, mask=self.mask)
        meanstr = "mean=({:.2f}, {:.2f}, {:.2f})".format(*self.mean[:, 0])
        stdstr = "std=({:.2f}, {:.2f}, {:.2f})".format(*self.stddev[:, 0])
        cv.imshow(self.name, viz)
        # cv.displayStatusBar(self.name, ", ".join((meanstr, stdstr)))

    def show(self):
        """Draws a window with the supplied image."""
        self._update()
        print("Press [q] or [esc] to close the window.")
        while True:
            k = cv.waitKey() & 0xFF
            if k in (ord("q"), ord("\x1b")):
                cv.destroyWindow(self.name)
                break
