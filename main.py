import numpy as np
import pandas as pd
import cv2
from os import listdir
import os.path
from PIL import Image, ExifTags
from itertools import chain

#MAIN PROGRAM!

class WondCarousel(object):

	def __init__(self):

		#default settings
		self.imgDir     = 'fotos/'
		self.imgExts    = ['.png','.jpg','.jpeg']
		self.dataPath   = 'measurements.csv'
		self.sizeFactor = 4 #2.2
		self.maxRulers  = 2
		self.maxwLines  = 2
		self.defaultTicks=5
		self.keys = {
				'next':[63235], #>
				'prev':[63234], #< 
				'escape':[27,113], #esc, q
				'ruler+':[61], #+
				'ruler-':[45], #-
				'ignore':[13], #return
				'info':[105], #i
				'save':[115] #s
		}

		#initialise variables
		self.curID      = 0
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
				self.data = pd.read_csv(self.dataPath, index_col=0)
			except:
				#TODO: Initialise ruler and wondname columns here!
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


		#Find first image that is not completed yet and set this to curID
		cols = []
		for n in range(self.maxRulers):
			cols += WondCarousel.getRulerCols(n)
		for n in range(self.maxwLines):	
			cols += WondCarousel.getwLineCols(n)

		indices = [False]*len(self.data)

		try:
			for col in cols:
				indices = indices | (self.data[col].apply(np.isnan))
			indices = indices & (self.data['ignore'] == 0)	
			notDone = self.data[indices].index.values
			if len(notDone) > 0:
				self.curID = notDone[0]
		except:
			pass

	@staticmethod
	def getRulerCols(n):
		return ["r%ix1" % n,
					"r%iy1" % n,
					"r%ix2" % n,
					"r%iy2" % n,
					"r%iticks" % n ]

	@staticmethod
	def getwLineCols(n):
		return ["l%ix1" % n,
				"l%iy1" % n,
				"l%ix2" % n,
				"l%iy2" % n]

	def getRulers(self,id=None):
		id = self.curID if id is None else id
		rulers = []
		for n in range(self.maxRulers):
				cols = WondCarousel.getRulerCols(n)

				try:
					r = self.data.loc[id,cols].tolist()
					if not np.isnan(r).any():
						r = [int(ri) for ri in r]
						rulers.append(
							((r[0],r[1]),(r[2],r[3]),r[4])
							)
				except:
					pass
		return rulers

	def getwLines(self,id=None):
		id = self.curID if id is None else id
		wLines = []

		for n in range(self.maxwLines):
			cols = WondCarousel.getwLineCols(n)
			try:
				l = self.data.loc[id,cols].tolist()
				if not np.isnan(l).any():
					l = [int(li) for li in l]
					wLines.append(
						((l[0],l[1]),(l[2],l[3]))
						)
			except:
				pass
		return wLines	

					

	def loadRulers(self,id=None):
		id = self.curID if id is None else id
		self.rulers = self.getRulers(id)

	def loadwLines(self,id=None):
		id = self.curID if id is None else id
		self.wLines = self.getwLines(id)

		
	def bufferImage(self,id=None):

		id = self.curID if id is None else id
		if not self.bufferID == id:
			img = cv2.imread(self.imgDir + self.data.imgPath[id])

			#TODO: resize image to fit window
			newx,newy = int(img.shape[1]/self.sizeFactor),int(img.shape[0]/self.sizeFactor) #new size (w,h)
			img = cv2.resize(img,(newx,newy))

			#also load ruler and line data . . .
			self.loadRulers()
			self.loadwLines()

			self.bufferImg = img
			self.bufferID  = id

		return self.bufferImg.copy()

	def resetIDlist(self):
		self.IDlist = self.data[self.data.ignore == 0].index.values

	def getDoneList(self):
		indices = [True]*len(self.data)
		cols = []
		for n in range(self.maxRulers):
			cols += WondCarousel.getRulerCols(n)
		for n in range(self.maxwLines):	
			cols += WondCarousel.getwLineCols(n)
		try:
			for col in cols:
				indices = indices & ~(self.data[col].apply(np.isnan))
				notDone = self.data[indices].index.values
			if len(notDone) > 0:
				return notDone
		except:
			pass


	def nextImg(self):
		allowedNext = self.IDlist[self.IDlist > self.curID]
		#print self.curID, allowedNext[0:20]
		if len(allowedNext) > 0:
		 	self.curID = allowedNext[0]
		 	self.renderImage()

	def prevImg(self):
		allowedPrev = self.IDlist[self.IDlist < self.curID]
		#print self.curID, allowedPrev[0:20]
		if len(allowedPrev) > 0:
			self.curID = allowedPrev[-1]
			self.renderImage()

	def ignoreImg(self):
		#self.data.ignore[self.curID] = 1
		self.data.loc[self.curID,'ignore'] = 1
		self.resetIDlist()
		self.nextImg()


	def saveCurLines(self):
		for n, ruler in enumerate(self.rulers):
			#Flatten the rulers first
			cols = WondCarousel.getRulerCols(n)
			ruler =  list(ruler[0]) + list(ruler[1]) + [ruler[2]]
			for i in range(len(cols)):
			 	self.data.loc[self.curID,cols[i]] = ruler[i]
			#self.data.loc[self.curID,cols] = list(ruler[0]) + list(ruler[1]) + [ruler[2]]

		for n, line in enumerate(self.wLines):
			#Flatten the rulers first
			cols = WondCarousel.getwLineCols(n)
			line = list(line[0]) + list(line[1])
			for i in range(len(cols)):
			 	self.data.loc[self.curID,cols[i]] = line[i]
			#self.data.loc[self.curID,cols] = list(ruler[0]) + list(ruler[1]) + [ruler[2]]


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
					self.saveCurLines()
				elif len(self.wLines) < self.maxwLines:
					self.wLines.append((self.bufferPoint,(x,y)))
					self.saveCurLines()
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

	def printInfo(self):
		id=self.curID
		print "Image #%i (%s)" % (id, self.data.loc[id,'imgPath'])
		print "Rulers:"
		print self.rulers
		print "wLines:"
		print self.wLines
		print "Stats:"
		print self.statsFromLines()

	def saveData(self):
		self.data.to_csv(self.dataPath)
		print "Saved data!"
			
	
	def statsFromLines(self,id=None):
		id = self.curID if id is None else id

		wLines = self.getwLines(id)
		rulers = self.getRulers(id)

		if len(wLines) == self.maxwLines and len(rulers) == self.maxRulers:
			#calculate mm to coordinate ratio
			ratios = []
			for ruler in rulers:
				#calculate length of line and divide by ticks
				ratios.append(np.linalg.norm(np.array(ruler[1]) - np.array(ruler[0])) / ruler[2])
			ratio = np.mean(ratios)
			std   = np.std(ratios)

			wLengths = []
			wStds    = []
			for wLine in wLines:
				#divide wline lenght in px by ratio to get std in cm : xm = px/(px/cm)
				wLength = np.linalg.norm(np.array(wLine[1]) - np.array(wLine[0])) / ratio
				wLengths.append(wLength)
				wStds.append(wLength/ratio)

			return wLengths[0], wStds[0], wLengths[1], wStds[1]

		else:
			return False

		



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

			#print k

			if k in self.keys['escape']:
				if self.bufferPoint:
					self.bufferPoint = None
				else:
					running=False
			elif k in self.keys['save']:
				self.saveData()
			elif k in self.keys['info']:
				self.printInfo()
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

	#now make the graph
	ids = w.getDoneList()
	lengths1 = []
	lengths2 = []
	stds1 = []
	stds2 = []
	times = []

	for id in ids:
		l1,std1,l2,std2 = w.statsFromLines(id)
		lengths1.append(l1)
		lengths2.append(l2)
		stds1.append(std1)
		stds2.append(std2)
		times.append(w.data.loc[id].datetime)

	print lengths1
	print lengths2
	print stds1
	print stds2
	print times




	#print w.data
	

if __name__ == '__main__':
	main()

