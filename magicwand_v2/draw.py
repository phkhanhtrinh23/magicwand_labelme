# import required libraries
import cv2
import numpy as np
drawing = False
ix,iy = -1,-1
rec = None

# define mouse callback function to draw circle
img = np.zeros((20, 20
,3), np.uint8)
img1 = img.copy()
def draw_rectangle(event, x, y, flags, param):
#    global ix, iy, drawing, img
    global ix, iy, img1
    #    drawing = False
    #    ix = -1
    #    iy = -1
    if event == cv2.EVENT_LBUTTONDOWN:
        #   drawing = True
        ix = x
        iy = y
    elif event == cv2.EVENT_LBUTTONUP:
        #   drawing = False
        img1 = img.copy()
        rec = cv2.rectangle(img1, (ix, iy),(x, y),(120, 255, 255),-1)
        print(rec[:, :, 1])
        


# Create a window and bind the function to window
cv2.namedWindow("Rectangle Window")

# Connect the mouse button to our callback function
cv2.setMouseCallback("Rectangle Window", draw_rectangle)

# display the window
while True:
    cv2.imshow("Rectangle Window", img1)
    if cv2.waitKey(10) == 27:
        break
cv2.destroyAllWindows()