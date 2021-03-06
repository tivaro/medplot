import numpy as np
import pandas as pd
import cv2
from os import listdir
import os.path
from PIL import Image, ExifTags
from itertools import chain
import matplotlib
import matplotlib.pyplot as plt
import datetime, time

#MAIN PROGRAM!

class WondCarousel(object):

	def __init__(self):

		#default settings
		self.imgDir     = 'fotos/'
		self.imgExts    = ['.png','.jpg','.jpeg']
		self.dataPath   = 'measurements.csv'
		self.sizeFactor = 2.8
		self.maxRulers  = 2
		self.maxwLines  = 2
		self.defaultTicks=5
		self.keys = {
				'next':[63235], # arrow>
				'prev':[63234], # arrow< 
				'escape':[27,113], #esc, q
				'ruler+':[61], #+
				'ruler-':[45], #-
				'ignore':[13], #return
				'info':[105], #i
				'save':[115], #s
				'graph':[103], #g
				'reset':[127], #backspace
				'resetRuler':[114], #r
				'resetwLine':[119], #w
		}

		#initialise variables
		self.curID      = 0
		self.bufferID    = None
		self.bufferPoint = None
		self.rulers		 = []
		self.wLines		 = []
		self.curTicks    = None
		self.graphFig    = None
		self.resetLines  = False

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
			self.data = self.data.append(newData,ignore_index=True)
			print "Loaded %i new images" % len(newData)

		self.data['datetime']  = pd.to_datetime(self.data['datetime'])
		self.data['timestamp'] = self.data['datetime'].apply(WondCarousel.toTimestamp)
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
		return []

	def setCurID(self,id):
	 	self.curID = id
	 	self.renderImage()
	 	self.updateGraph()


	def nextImg(self):
		allowedNext = self.IDlist[self.IDlist > self.curID]
		if len(allowedNext) > 0:
		 	self.setCurID(allowedNext[0])

	def prevImg(self):
		allowedPrev = self.IDlist[self.IDlist < self.curID]
		if len(allowedPrev) > 0:
			self.setCurID(allowedPrev[-1])

	def ignoreImg(self):
		self.data.loc[self.curID,'ignore'] = 1
		self.resetIDlist()
		self.nextImg()


	def saveCurLines(self):
		for n in range(self.maxRulers):
			cols = WondCarousel.getRulerCols(n)
			if n < len(self.rulers):
				ruler = self.rulers[n]
				self.data.loc[self.curID,cols] = list(ruler[0]) + list(ruler[1]) + [ruler[2]]
			else:
				self.data.loc[self.curID,cols] = [None]*len(cols)

		for n in range(self.maxwLines):
			cols = WondCarousel.getwLineCols(n)
			if n < len(self.wLines):
				line = self.wLines[n]
				self.data.loc[self.curID,cols] = list(line[0]) + list(line[1])
			else:
				self.data.loc[self.curID,cols] = [None]*len(cols)


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

		#TODO: add Text of available keys / info		


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

	@staticmethod
	def toTimestamp(datetime):
		return time.mktime(datetime.timetuple())

	@staticmethod
	def fromTimestamp(timestamp):
		return datetime.datetime.fromtimestamp(timestamp)

	def printInfo(self):
		id=self.curID
		print "Image #%i (%s)" % (id, self.data.loc[id,'imgPath'])
		print "Rulers:"
		print self.rulers
		print "wLines:"
		print self.wLines
		print "Stats:"
		print self.statsFromLines()
		print "Date"
		print self.data.loc[id,'datetime']

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
			std   = np.std(ratios) + 1

			wLengths = []
			wStds    = []
			for wLine in wLines:
				#divide wline lenght in px by ratio to get std in cm : xm = px/(px/cm)
				wLength = np.linalg.norm(np.array(wLine[1]) - np.array(wLine[0])) / ratio
				wLengths.append(wLength)
				wStds.append(wLength/ratio*std)

			return wLengths[0], wStds[0], wLengths[1], wStds[1]

		else:
			return False

	def plotGraph(self,id=None,fig=None):
		ids = self.getDoneList()
		lengths1 = []
		lengths2 = []
		stds1 = []
		stds2 = []
		datetimes  = []
		timestamps = []

		if fig is None:
			fig = plt.figure()
		ax = plt.gca()

		for cid in ids:
			l1,std1,l2,std2 = self.statsFromLines(cid)
			lengths1.append(l1)
			lengths2.append(l2)
			stds1.append(std1)
			stds2.append(std2)
			datetimes.append(self.data.loc[cid].datetime)
			timestamps.append(self.data.loc[cid].timestamp)


		plt.errorbar(timestamps,lengths1, yerr=stds1, marker='.', label='lengte',  color='purple')
		plt.errorbar(timestamps,lengths2, yerr=stds2, marker='.', label='breedte', color='pink')
		

		#Hightlight a specific image in the graph
		if id:
			xlim = plt.xlim()
			ylim = plt.ylim()

			if id in ids:
				ix = np.where(ids == id)[0][0]
				plt.errorbar(timestamps[ix],lengths1[ix],yerr=stds1[ix],marker='.',color='green')
				plt.errorbar(timestamps[ix],lengths2[ix],yerr=stds2[ix],marker='.',color='green')
				d = datetimes[ix]
				t = timestamps[ix]
				plt.annotate("", xy=(0, lengths1[ix]), xytext=(-25, 0), 
					xycoords=('axes fraction', 'data'), textcoords='offset points', arrowprops=dict(arrowstyle="->",
					connectionstyle="arc3",color='purple'))
				plt.annotate("", xy=(0, lengths2[ix]), xytext=(-25, 0), 
					xycoords=('axes fraction', 'data'), textcoords='offset points', arrowprops=dict(arrowstyle="->",
					connectionstyle="arc3",color='pink'))
			else:
				d = self.data.loc[self.curID].datetime
				t = self.data.loc[self.curID].timestamp

			#plot date string, at Location relative to line.
			if t > (((xlim[1] - xlim[0]) / 2) + xlim[0]):
				al = -1
				align = 'right'
			else:
				al = 1
				align = 'left'
			plt.plot([t,t],ylim,color='green')
			ax.text(t+al*0.01*(xlim[1]-xlim[0]), ylim[0]+0.01*(ylim[1]-ylim[0]), d.strftime('%Y-%m-%d %H:%M:%S'),
			verticalalignment='bottom', horizontalalignment=align, color='green', fontsize=11)

		xTicks  =  ax.get_xticks()
		xLabels = [WondCarousel.fromTimestamp(x).strftime('%Y-%m-%d') for x in xTicks]
		plt.xticks(xTicks, xLabels, rotation=30,ha='right')

		plt.ylabel('Grootte (cm)')
		if len(ids) > 0:
			plt.legend(loc=2,numpoints=1)

		return fig

	def toggleGraph(self):
		#TODO: don't is is None, try to see if figure exists (because we can also press the close button)
		if self.graphFig is None:
			self.graphFig = plt.figure()
			self.updateGraph()
			#TODO: The warning seems to be generated by showing the plot . . .
			plt.show(block=False)
			cid = self.graphFig.canvas.mpl_connect('button_press_event', self.clickGraph)
		else:	
			plt.close(self.graphFig)
		 	self.graphFig = None
			
		pass	

	def updateGraph(self):
		if self.graphFig is not None:
			fig = self.graphFig
			fig.clear()
			self.plotGraph(id=self.curID,fig=fig)
			plt.draw()


	def clickGraph(self,event):
		#Find closest x
		if event.xdata is not None:
			timestamps = self.data.loc[self.IDlist,'timestamp'].values
			closestIx = min(range(len(timestamps)), key=lambda i: abs(timestamps[i]-event.xdata))
			self.setCurID(self.IDlist[closestIx])
		

	def run(self):
		"""
		Runs the program until it is closed by user!
		"""

		running = True

		cv2.namedWindow('image',cv2.WINDOW_AUTOSIZE)
		cv2.setMouseCallback("image", self.mouseCallback)

		while running:

			if not self.bufferPoint:
				self.renderImage()

			#register which key was pressed
			k = cv2.waitKey(0)

			if self.resetLines:
				if k in self.keys['escape']:
					self.resetLines = False
				elif k in self.keys['resetwLine']:
					self.wLines = []
					self.saveCurLines()
					self.updateGraph()
					self.resetLines = False
				elif k in self.keys['resetRuler']:
					self.rulers = []
					self.saveCurLines()
					self.updateGraph()
					self.resetLines = False
				else:
					print "please press [r] for rulers, [w] for wlines, [esc] or [q] to cancel"

			else:

				if k in self.keys['reset'] and (len(self.wLines) > 0 or len(self.rulers) > 0):
					self.resetLines = True
					print "RESET? press [r] for rulers, [w] for wlines, [esc] to cancel"
				elif k in self.keys['escape']:
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
					#TODO: call renderImage(mouse=(x,y))
					#TODO: find out how to get mouse position in opencv / store it manarrly
				elif k in self.keys['ruler-'] and self.curTicks > 1:
					self.curTicks -= 1
				elif k in self.keys['graph']:
					self.toggleGraph()
				else:
					print "Key %i not recognised" % k

			self.updateGraph()	

def main():
	w = WondCarousel()
	w.run()

	# w.plotGraph()
	# plt.show()
	#print w.data

	#Data van de behandeling!
	plotDiagnostics(w)
	plt.savefig('graph.png')


def plotDiagnostics(w):
	from matplotlib import gridspec
	fig = plt.figure(figsize=(11,6))
	gs = gridspec.GridSpec(1, 2, width_ratios=[3, 1]) 
	ax0 = plt.subplot(gs[0])
	w.plotGraph(fig=fig)

	def toDatetime(string):
		return datetime.datetime.strptime(string, "%Y-%m-%d %H:%M")

	def daysRange(date1,date2=None):
		#returns a range of datetimes for each day in between X
		if not date2:
			date2 = datetime.datetime.now()
		else:
			date2 = toDatetime(date2)
		Ndays = (date2 - toDatetime(date1)).days
		return [toDatetime(date1) + datetime.timedelta(days=n) for n in range(Ndays)]
		

	consults     = [("2015-08-27 10:00",'huisarts'), #nijmegen
					("2015-08-31 10:40",'huisarts'), #mertens
					("2015-09-10  8:40",'huisarts'), #zijlstra
					("2015-09-14 16:15",'huisarts'), #observator
					("2015-09-17 15:30",'chirurgie'), #wondpoli
					("2015-09-22 16:20",'huisarts'), #mertens voor plekken
					("2015-09-25 13:40",'chirurgie'), #duplex onderzoek + chirurg
					("2015-09-28 11:20",'internist'), #internist
					("2015-10-01  9:20",'chirurgie'), #wondpoli
					("2015-10-02  9:30",'dermatoloog'), #dermatoloog
					("2015-10-05  9:10",'internist'), #internist + wondpoli
					("2015-10-12  9:10",'chirurgie'), #chirurgie
					("2015-10-14  9:00",'dermatoloog'), #dermatoloog
					("2015-10-22 15:00",'internist'), #internist
					("2015-10-26 14:30",'huisarts'), #huisarts
					("2015-10-28  9:00",'dermatoloog'), #dermatoloog
					("2015-10-30  9:30",'dermatoloog-vu'), #dermatoloog VU
					("2015-11-18  14:00",'dermatoloog-vu'), #dermatoloog VU, afbouwen prednisone
					("2015-11-30   9:00",'dermatoloog-vu'), #dermatoloog VU, Lisa mee, start cellcept
					("2015-12-10   9:00",'dermatoloog-vu'), #dermatoloog VU, dermofate zalf
					("2015-12-21   8:50",'dermatoloog-vu'), #dermatoloog VU
					("2015-12-29  13:30",'huisarts'), #dermatoloog VU
					("2016-01-04   9:05",'dermatoloog-vu') #dermatoloog VU
					]
	colors = {'huisarts':'r',
			  'chirurgie':'lightsalmon',
			  'internist':'mediumaquamarine',
			  'dermatoloog':'lightblue',
			  'dermatoloog-vu':'pink'}
	markers = {'huisarts':'+',
			  'chirurgie':'.',
			  'internist':'o',
			  'dermatoloog':'*',
			  'dermatoloog-vu':'*'}


	def datesDoseRange(tripleList):
		medDates = []
		medDoses = []
		for date1,date2,dose in tripleList:
			medDates = medDates  + daysRange(date1, date2)
			medDoses = medDoses + [dose] * (len(medDates)-len(medDoses))
		return medDates, medDoses

	prednisone, prednisoneD = datesDoseRange([
					("2015-10-02  9:00", "2015-10-09  9:00", 50),
					("2015-10-10  9:00", "2015-10-17  9:00", 40),
					("2015-10-18  9:00", "2015-11-18  9:00", 60),
					("2015-11-18  9:00", "2015-11-25  9:00", 50),
					("2015-11-25  9:00", "2016-01-28  9:00", 40),
					("2016-01-28  9:00", "2016-02-04  9:00", 50),
					("2016-02-04  9:00", "2016-02-19  9:00", 60),
					("2016-02-19  9:00", "2016-02-21  9:00", 55),
					("2016-02-21  9:00", "2016-02-23  9:00", 50),
					("2016-02-23  9:00", "2016-02-25  9:00", 45),
					("2016-02-25  9:00", "2016-02-28  9:00", 40),
					("2016-02-28  9:00", "2016-03-01  9:00", 35)
					])

	cellcept, cellceptD = datesDoseRange([
					("2015-11-30  9:00", "2015-12-07  9:00", 70),
					("2015-12-07  9:00", "2015-12-14  9:00", 80),
					("2015-12-14  9:00", "2015-12-21  9:00", 90),
					("2015-12-21  9:00", "2016-01-28  9:00", 100),
					("2016-01-28  9:00", "2016-02-19  9:00", 110)
					])

	fraxiparine  = [toDatetime("2015-09-28 18:00") + datetime.timedelta(days=n) for n in range(7*4)]
	antibiotica  = [toDatetime("2015-08-27 10:00") + datetime.timedelta(days=n) for n in range(5)] #eerste keer
	antibiotica += [toDatetime("2015-09-22 16:20") + datetime.timedelta(days=n) for n in range(7)] #fusidine
	antibiotica += [toDatetime("2015-09-25 13:40") + datetime.timedelta(days=n) for n in range(8)] #huidbacterie
	antibiotica += [toDatetime("2015-10-14  9:00") + datetime.timedelta(days=n) for n in range(6)] #zilversulfadiasine
	antibiotica += [toDatetime("2015-10-23  9:00") + datetime.timedelta(days=n) for n in range(7)] #fusidine
	cyclosporine = daysRange("2015-10-18  9:00","2015-11-18  9:00")
	calcichew    = daysRange("2015-11-13  9:00")
	pentostam    = daysRange("2016-02-26  9:00") #pentostam infuus

	#convert everyting to datetime
	prednisone   = [WondCarousel.toTimestamp(d) for d in prednisone]
	cyclosporine = [WondCarousel.toTimestamp(d) for d in cyclosporine]
	fraxiparine  = [WondCarousel.toTimestamp(d) for d in fraxiparine]
	antibiotica  = [WondCarousel.toTimestamp(d) for d in antibiotica]
	calcichew    = [WondCarousel.toTimestamp(d) for d in calcichew]
	cellcept     = [WondCarousel.toTimestamp(d) for d in cellcept]
	pentostam    = [WondCarousel.toTimestamp(d) for d in pentostam]


	ax1 = plt.gca()
	ax2 = ax1.twinx()

	for cType in set([c[1] for c in consults]):
		t = [WondCarousel.toTimestamp(toDatetime(c[0])) for c in consults if c[1] == cType]
		ax2.scatter(t,[0]*len(t),color=colors[cType],label=cType, marker=markers[cType])

	ax2.scatter(antibiotica,[10]*len(antibiotica),color='brown',marker='.')
	ax2.scatter(calcichew,[10]*len(calcichew),color='lightblue',marker='.')
	ax2.scatter(fraxiparine,[20]*len(fraxiparine),color='g',marker='.')
	ax2.scatter(cyclosporine,[30]*len(cyclosporine),color='y',marker='.')
	ax2.scatter(prednisone,prednisoneD,color='b',marker='.')
	ax2.scatter(cellcept,cellceptD,color='r',marker='.')
	ax2.scatter(pentostam,[20]*len(pentostam),color='lightgreen',marker='.')

	#labels
	yOffset = 30
	plt.annotate('dokters bezoeken' , xy=(1, 0), xytext=(yOffset, 0), 
					xycoords=('axes fraction', 'data'), textcoords='offset points')
	plt.annotate('antibiotica' , xy=(1, 10), xytext=(yOffset, 0), color='brown',
					xycoords=('axes fraction', 'data'), textcoords='offset points')
	plt.annotate('calcichew' , xy=(1, 10), xytext=(yOffset+75, 0), color='lightblue',
					xycoords=('axes fraction', 'data'), textcoords='offset points')
	plt.annotate('fraxiparine (0,3 ml)' , xy=(1, 20), xytext=(yOffset, 0), color='g',
					xycoords=('axes fraction', 'data'), textcoords='offset points')
	plt.annotate('cyclosporine (100 mg)' , xy=(1, 30), xytext=(yOffset, 0), color='y',
					xycoords=('axes fraction', 'data'), textcoords='offset points')
	plt.annotate('prednisone (mg)' , xy=(1, 50), xytext=(yOffset, 0), color='b',
					xycoords=('axes fraction', 'data'), textcoords='offset points')
	plt.annotate('mycofenolaat (mg)' , xy=(1, 85), xytext=(yOffset, 0), color='r',
					xycoords=('axes fraction', 'data'), textcoords='offset points')

	ax2.set_ylim([-10,200])
	ax2.set_yticks([40,50,60])
	ax2.yaxis.label.set_color('b')
	ax2.tick_params(axis='y', colors='b')

	plt.legend(scatterpoints = 1,bbox_to_anchor=(1.05, 0.03), loc=2, borderaxespad=0.,fontsize=10,frameon=False)
	fig.set_tight_layout(True)

	ax3 = ax1.twinx()
	ax3.set_ylim([-10,200])
	ax3.set_yticks([70,80,90,100])
	ax3.set_yticklabels([500,1000,1500,2000])
	#ax3.set_yticks([70,80,90,100],[500,1000,1500,2000])
	#TODO:ax3.set_ylabels([500,1000,1500,2000])
	ax3.yaxis.label.set_color('r')
	ax3.tick_params(axis='y', colors='r')


if __name__ == '__main__':
	main()