import numpy as np
import cv2
from os import listdir
import os.path

fotopath = 'fotos/'
imageExts = ['.png','.jpg','.jpeg']

imPaths= [ fotopath + f for f in listdir(fotopath) if os.path.isfile(os.path.join(fotopath,f)) and os.path.splitext(os.path.join(fotopath,f))[1].lower() in imageExts ]


print imPaths[0]
sizeFactor = 4

ignoreKey = 13 #return key
escapeKey = 27



rulers = []

def refreshImg(id):
	global imPaths, rulers

	#TODO: load and resize only if necsacey store in buffer otherwise

	img = cv2.imread(imPaths[id])

	#resize image
	newx,newy = img.shape[1]/sizeFactor,img.shape[0]/sizeFactor #new size (w,h)
	img = cv2.resize(img,(newx,newy))

	for ruler in rulers:
		c = (1,0,0)
		if len(ruler) > 1:
			cv2.line(img, ruler[0], ruler[1],c)
		elif len(ruler) > 0:
			#show point
			cv2.circle(img, ruler[0], 5, c)

	cv2.imshow('image',img)		



def click_and_crop(event, x, y, flags, param):
	global rulers, n

	# grab references to the global variables

	#mousemove

	if event == cv2.EVENT_LBUTTONDOWN:
		print "CLICK!"

		print rulers

		#are there rulers allready?
		if len(rulers) > 0:
			#are they finished allready?
			if len(rulers[-1]) == 1:
				#add second point
				rulers[-1] = rulers[-1] + ((x,y),)
			else:
				rulers.append(((x,y),))
				#create point
		else:
			rulers.append(((x,y),))
			#create point

		print rulers

		refreshImg(n)






cv2.namedWindow('image',cv2.WINDOW_NORMAL)
cv2.setMouseCallback("image", click_and_crop)

for n in range(100):

	refreshImg(n)


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