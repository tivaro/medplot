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

		self.keys = {
				'next':[63235,13], #>, return
				'prev':[63234], #< 
				'escape':[27], #esc
				'ruler+':[61], #+
				'ruler-':[45], #-
				'ignore':[13], #return
		}

		#initialise variables
		self.curImg = 0
		self.bufferID = None

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
								'relevant':1})

		if len(newData) > 0:
			self.data = self.data.append(newData)
			print "Loaded %i new images" % len(newData)

		self.data['datetime'] = pd.to_datetime(self.data['datetime'])
		self.data = self.data.sort('datetime')
		self.data.reset_index()


		#load images, and measurement data if it exists yet

	def bufferImage(self,id=None):

		id = id or self.curImg
		if not self.bufferID == id:
			img = cv2.imread(self.imgDir + self.data.imgPath[id])

			#TODO: resize image to fit window
			sizeFactor = 3
			newx,newy = img.shape[1]/sizeFactor,img.shape[0]/sizeFactor #new size (w,h)
			img = cv2.resize(img,(newx,newy))

			self.bufferImg = img

		return self.bufferImg






	def renderImage(self,id=None):

		img = self.bufferImage(id)

		cv2.imshow('image',img)	





	def run(self):
		"""
		Runs the program until it is closed by user!
		"""

		running = True

		cv2.namedWindow('image',cv2.WINDOW_NORMAL)
		#cv2.namedWindow('graph',cv2.WINDOW_NORMAL)
		#cv2.namedWindow('controls',cv2.WINDOW_NORMAL)
		#cv2.setMouseCallback("image", click_and_crop)

		while running:

			self.renderImage()

			#register which key was pressed
			k = cv2.waitKey(0)

			if k in self.keys['escape']:
				running=False
			elif k in self.keys['next'] and self.curImg < len(self.data):
				self.curImg += 1
				self.renderImage()
			elif k in self.keys['prev'] and self.curImg > 0:
				self.curImg -= 1
			elif k in self.keys['next']:
				print "Ignore this picture!"
			else:
				pass





		





def main():
	w = WondCarousel()
	print w.data
	w.run()
	#w.data.to_csv(w.dataPath)
	

if __name__ == '__main__':
	main()

