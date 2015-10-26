import numpy as np
import cv2
from os import listdir
import os.path

class Ruler(object):  

	def __init__(self,point=None,color=(1,0,0)):
		self.length = 5 #length in cm
		self.unit   = 'cm'
		self.tick   = 1
		self.points = []
		self.color  = color

		if point:
			self.addPoint(point)

	def isDone(self):
		return len(self.points) == 2

	def addPoint(self,point):
		if len(self.points) > 1:
			return False
		else:
			self.points.append(point)
			return True

	def __repr__(self):
		return "...".join([str(p) for p in self.points])


	def printRuler(self, img):
		if len(self.points) > 1:
			cv2.line(img, self.points[0], self.points[1],self.color)
		elif len(self.points) > 0:
			cv2.circle(img, self.points[0], 5, self.color)

		return img



class Wondimage(object):

	maxRulers = 2
	maxWLines = 2

	def __init__(self,imPath):
		self.imPath   = imPath
		self.rulers = [Ruler()]
		self.wLines = [Ruler()]

	def onClick(self,point):
		if len(self.rulers) < self.maxRulers or not self.rulers[-1].isDone():
			lastruler = self.rulers[-1]
			#ruler fase or ruler not yet finished
			if not lastruler.addPoint(point):
				self.rulers.append(Ruler(point))

		else:
			print "Wondline fase!!"
			#wondline fase


	def loadBuffer(self):
		self.img = cv2.imread(self.imPath)

		#resize image (TODO: ONLY WHEN NECECAIRY AND KEEP TRACK OF THIS TO CONVERT COORDINATES)
		sizeFactor = 4
		newx,newy = img.shape[1]/sizeFactor,self.img.shape[0]/sizeFactor #new size (w,h)
		self.img = cv2.resize(img,(newx,newy))


	def rmBufffer():
		pass

	def showImage(self,window='image'):

		img = self.img.copy()
		#TODO: add rulers/etc to image
		for ruler in rulers:
			img = ruler.printRuler(img)

		cv2.imshow(window,self.img)
		



class Program():
	fotopath = 'fotos/'
	imageExts = ['.png','.jpg','.jpeg']

	def __init__(self):
		self.images= [ Wondimage(self.fotopath + f) for f in listdir(self.fotopath) if os.path.isfile(os.path.join(self.fotopath,f)) and os.path.splitext(os.path.join(self.fotopath,f))[1].lower() in self.imageExts ]



w = Wondimage('fefe')
w.onClick((1,2))
w.onClick((2,5))
w.onClick((2,5))
w.onClick((1,2))
w.onClick((6,8))
w.onClick((3,8))
w.onClick((3,8))
w.onClick((3,8))
print w.rulers

p = Program()


cv2.namedWindow('image',cv2.WINDOW_NORMAL)
cv2.setMouseCallback("image", mouseTrack)

for image in p.images:

	image.showImage()

	#register which key was pressed
	k = cv2.waitKey(0)

	if k == escapeKey:
		break
	elif k == ignoreKey:
		print "Ignore this picture!"
	else:
		#display same image again!
		pass


	rulers = []	

	

cv2.destroyAllWindows()

