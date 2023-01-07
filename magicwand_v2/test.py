from magicwand import SelectionWindow
import cv2 as cv
img = cv.imread("readme-example.png")
window = SelectionWindow(img)
window.show()
print(f"Selection mean: {window.mean[:, 0]}.")