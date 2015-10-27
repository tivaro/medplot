import numpy as np
import pandas as pd
import cv2
from os import listdir
import os.path
from PIL import Image, ExifTags

#MAIN PROGRAM!

class WondCarousel(object):

	def __init__(self):

		#default settings
		self.imgDir    = 'fotos/'
		self.imgExts   = ['.png','.jpg','.jpeg']
		self.dataPath  = 'measurements.csv'
		self.sizeFactor = 5#2.2
		self.maxRulers = 2
		self.maxwLines = 2
		self.defaultTicks=5
		self.keys = {
				'next':[63235], #>
				'prev':[63234], #< 
				'escape':[27,113], #esc, q
				'ruler+':[61], #+
				'ruler-':[45], #-
				'ignore':[13], #return
				'info':[105] #i
		}

		#initialise variables
		self.curImg      = 0
		self.bufferID    = None
		self.bufferPoint = None
		self.rulers		 = []
		self.wLines		 = []
		self.curTicks    = None

		self.loadData()

		#load images

		#try to load data

		#create for data for images that don't exist


	def loadData(self):

		#load image paths
		imgPaths= [f for f in listdir(self.imgDir) if os.path.isfile(os.path.join(self.imgDir,f)) and os.path.splitext(os.path.join(self.imgDir,f))[1].lower() in self.imgExts ]

		#try to load data from file
		if not hasattr(self, 'data'):
			try:
				self.data = pd.read_csv(self.dataPath)
			except:
				self.data = pd.DataFrame(columns=['imgPath'])

		#add images that do not have a record yet 
		newData = []
		for imgPath in imgPaths:
			img = Image.open(self.imgDir + imgPath)
			#Load META-data and convert datetime 
			exif = { ExifTags.TAGS[k]: v for k, v in img._getexif().items() if k in ExifTags.TAGS }
			date,time =  exif['DateTime'].split(' ')
			date = date.replace(':','-')
			datetime = date+" "+time

			if not any(self.data.imgPath ==imgPath):
				newData.append({'imgPath':imgPath,
								'datetime':datetime,
								'ignore':0})

		if len(newData) > 0:
			self.data = self.data.append(newData)
			print "Loaded %i new images" % len(newData)

		self.data['datetime'] = pd.to_datetime(self.data['datetime'])
		self.data = self.data.sort('datetime')
		self.data.reset_index()

		self.resetIDlist()


		#load images, and measurement data if it exists yet


	def bufferImage(self,id=None):

		id = id or self.curImg
		if not self.bufferID == id:
			img = cv2.imread(self.imgDir + self.data.imgPath[id])

			#TODO: resize image to fit window
			newx,newy = int(img.shape[1]/self.sizeFactor),int(img.shape[0]/self.sizeFactor) #new size (w,h)
			img = cv2.resize(img,(newx,newy))

			self.bufferImg = img
			self.bufferID  = id

		return self.bufferImg.copy()

	def resetIDlist(self):
		self.IDlist = self.data[self.data.ignore == 0].index.values


	def nextImg(self):
		allowedNext = self.IDlist[self.IDlist > self.curImg]
		#print self.curImg, allowedNext[0:20]
		if len(allowedNext) > 0:
		 	self.curImg = allowedNext[0]
		 	self.renderImage()

	def prevImg(self):
		allowedPrev = self.IDlist[self.IDlist < self.curImg]
		#print self.curImg, allowedPrev[0:20]
		if len(allowedPrev) > 0:
			self.curImg = allowedPrev[-1]
			self.renderImage()

	def ignoreImg(self):
		#self.data.ignore[self.curImg] = 1
		self.data.loc[self.curImg,'ignore'] = 1
		self.resetIDlist()
		self.nextImg()


	def renderImage(self,id=None,mouse=None):

		img = self.bufferImage(id)

		[WondCarousel.addRuler(img,r[0],r[1],r[2]) for r in self.rulers]
		c = [(240,0,140),(140,0,240)]
		[WondCarousel.addwLine(img,l[0],l[1],c[i]) for i,l in enumerate(self.wLines)]

		if mouse:
			#find out if ruler, or wLine
			if len(self.rulers) < self.maxRulers:
				WondCarousel.addRuler(img,self.bufferPoint, mouse,self.curTicks,c=(180,200,100))
			else:
				WondCarousel.addwLine(img,self.bufferPoint, mouse,c=(20,0,240))


		cv2.imshow('image',img)	

	def mouseCallback(self,event, x, y, flags, param):


		if event == cv2.EVENT_LBUTTONDOWN:

			if self.bufferPoint:
				#finish this line
				if len(self.rulers) < self.maxRulers:
					self.rulers.append((self.bufferPoint,(x,y),self.curTicks))
				elif len(self.wLines) < self.maxwLines:
					self.wLines.append((self.bufferPoint,(x,y)))
					if len(self.wLines) == self.maxwLines:
						self.nextImg()

				self.bufferPoint = None

				self.renderImage()


			else:
				self.bufferPoint = (x,y)
				self.curTicks 	 = self.defaultTicks


		elif self.bufferPoint and self.bufferPoint != (x,y):
			#a line is being dragged right now
			self.renderImage(mouse=(x,y))

	@staticmethod
	def addRuler(img,p1,p2,majorTicks,minorTicks=5,c=(200,180,100)):
		#basic line
		cv2.line(img, p1, p2,c,thickness=2)

		#TICKS
		majorLength = 20
		minorLength = 10


		#find orthonormal vector
		xy = [0,1]
		delta = [ p2[i] - p1[i] for i in xy ]
		ort = np.array([-delta[1],delta[0]])
		ort = ort / np.linalg.norm(ort)

		for m in range(majorTicks+1):

			#major ticks
			m1 = tuple(int(p1[i] + (1.0*m/majorTicks)*delta[i]) for i in xy)
			m2 = tuple(int(m1[i] + ort[i] * majorLength) for i in xy)

			#cv2.line(img, (x1,y1), (x2,y2),c,thickness=2)
			cv2.line(img,m1,m2,c,thickness=2)

			#minor ticks
			if m < majorTicks:
				for n in range(1,minorTicks):
					n1 = tuple(int(m1[i] + (1.0*n/minorTicks)*(delta[i]/majorTicks)) for i in xy)
					n2 = tuple(int(n1[i] + ort[i] * minorLength) for i in xy)
					cv2.line(img, n1, n2,c,thickness=1)

	@staticmethod
	def addwLine(img,p1,p2,c=(20,0,240)):
		#basic line
		cv2.line(img, p1, p2,c,thickness=2)

		#endpoints
		length = 10

		#find orthonormal vector
		xy = [0,1]
		delta = [ p2[i] - p1[i] for i in xy ]
		ort = np.array([-delta[1],delta[0]])
		ort = ort / np.linalg.norm(ort) * length
		cv2.line(img, p1,tuple(int(p1[i] + ort[i]) for i in xy),c,thickness=1)
		cv2.line(img, p2,tuple(int(p2[i] + ort[i]) for i in xy),c,thickness=1)


	def run(self):
		"""
		Runs the program until it is closed by user!
		"""

		running = True
		#print dir(cv2)
		cv2.namedWindow('image',cv2.WINDOW_AUTOSIZE)
		#print cv2.getWindowProperty('image',cv2.WND_PROP_ASPECT_RATIO)
		#cv2.setWindowProperty('image',cv2.WND_PROP_ASPECT_RATIO,cv2.CV_WINDOW_KEEPRATIO)
		#print cv2.getWindowProperty('image',cv2.WND_PROP_ASPECT_RATIO)
		#cv2.namedWindow('graph',cv2.WINDOW_NORMAL)
		#cv2.namedWindow('controls',cv2.WINDOW_NORMAL)
		cv2.setMouseCallback("image", self.mouseCallback)

		while running:

			if not self.bufferPoint:
				self.renderImage()

			#register which key was pressed
			k = cv2.waitKey(0)

			print k

			if k in self.keys['escape']:
				if self.bufferPoint:
					self.bufferPoint = None
				else:
					running=False
			elif k in self.keys['info']:
				print self.rulers
			elif k in self.keys['next']:
				self.nextImg()
			elif k in self.keys['prev']:
				self.prevImg()
			elif k in self.keys['ignore']:
				self.ignoreImg()
			elif k in self.keys['ruler+']:
				self.curTicks += 1
			elif k in self.keys['ruler-'] and self.curTicks > 1:
				self.curTicks -= 1
			else:
				pass


def main():
	w = WondCarousel()
	w.run()
	print w.data
	#w.data.to_csv(w.dataPath)
	

if __name__ == '__main__':
	main()

