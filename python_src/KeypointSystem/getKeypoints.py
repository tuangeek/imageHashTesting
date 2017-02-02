import numpy as np
import cv2
import shapeDrawerWithDebug as d
from utils import basicImageOperations as BIO
from utils import basicShapeOperations as BSO
from random import randint
import itertools
import math
import sys
import fragProcessing as fs
import time
#####rules
import keypoints as kp

	

def isGoodFrag(tri):
	return True

def getDist(pnt1, pnt2):
	x1, y1 = pnt1
	x2, y2 = pnt2
	return math.sqrt( (x2 - x1)**2 + (y2 - y1)**2 )
	

def getClosesetXPoints(pnt, points):
	cpy = list(points)
	ret = []
	for pt in points:
		#require the point to be a minimum distance away
		if getDist(pnt, pt) > 200 and getDist(pnt, pt) < 300:	
			ret.append(pt)

	return ret

def getIndexOfClosestPoint(pnt, points):

	dist = getDist(pnt, points[0])
	retIndex = 0
	for i in range(len(points)-1):
		if getDist(pnt, points[i+1]) < dist:
			dist = getDist(pnt, points[i+1])
			retIndex = i+1

	return retIndex

def getTriangles(points):
	#return itertools.combinations(points, 3)
	
	retTris = []
	cpy = list(points)
	outside = list(cpy)
	for pnt in points:
		cpy = outside

		if len(cpy) < 3:
			break

		del cpy[0]#remove the current point

		tempPnts = getClosesetXPoints(pnt, cpy)
		outside = list(cpy)


		tempTris = itertools.combinations(tempPnts, 2)
		for tri in tempTris:
			###convert
			finTri = []
			for ver in tri:
				finTri.append(ver)
			finTri.append(pnt)
			###convert
			retTris.append(finTri)

	return retTris

def trianglesPostFiltering(tris):
	ret = []
	for tri in tris:
		if isGoodFrag(tri):
			ret.append(tri)
	return ret

def getAllValidPointsForTargetPoint(targetPoint, points, pointsToIgnore, lower=598, upper=600):
	
	ret = []
	for point in points:
		if point in pointsToIgnore:
			continue
		dist = getDist(point, targetPoint)
#		print dist
		if dist > lower and dist < upper:
			ret.append(point)
	return ret

def getAllTrianglesForTargetPoint(pt1, validPoints, lowerUsed, upperUsed):
	import itertools
	
	ret = []
	for pt2 in validPoints:
		validPoints2nd = getAllValidPointsForTargetPoint(pt2, validPoints, [pt2], lower=lowerUsed, upper=upperUsed)
		tempTris = []
		for pt3 in validPoints2nd:
			tempTris.append( [pt1, pt2, pt3] )
		
		ret.extend( tempTris )

	return ret


def fromPointsToFramenets_justTriangles(points, DEBUG_IMAGE=None, DEBUG_KEYPOINTS=None):

	#print "len of points"
	#print len(points)
	lower=150
	upper=300

	triangles = []
	
	excludeList = []
	for i in range(len(points)):
		targetPoint = points[i]
		DEBUG_IMAGE_copy = DEBUG_IMAGE.copy() if not DEBUG_IMAGE == None else None
		excludeList.append(targetPoint)
		validPoints = getAllValidPointsForTargetPoint(targetPoint, points, excludeList, lower=lower, upper=upper)
		if not DEBUG_IMAGE_copy == None:
			print "len validPoints"
			print len(validPoints)
			targetPoint_cpy = (int(targetPoint[0]), int(targetPoint[1]))
			cv2.circle(DEBUG_IMAGE_copy, targetPoint_cpy, lower, (255,0,0))
			cv2.circle(DEBUG_IMAGE_copy, targetPoint_cpy, upper, (255,0,0))
			cv2.circle(DEBUG_IMAGE_copy, targetPoint_cpy, 10, (255,0,0), 10)
			
			for pt in validPoints:
				cv2.line(DEBUG_IMAGE_copy, targetPoint_cpy, (int(pt[0]), int(pt[1])), (255,0,0))
			
			if not DEBUG_KEYPOINTS == None:
				d.drawKeypoints_obj(DEBUG_IMAGE_copy, DEBUG_KEYPOINTS, (0,255,0))
			
			cv2.imwrite('../frames/frame'+str(i*2)+".png", DEBUG_IMAGE_copy)
			cv2.imshow("DEBUG_IMAGE_copy", DEBUG_IMAGE_copy)
			cv2.waitKey()
		tempTriangles = getAllTrianglesForTargetPoint(targetPoint, validPoints, lowerUsed=lower, upperUsed=upper)
		if not DEBUG_IMAGE_copy == None:
			print "len tempTriangles"
			print len(tempTriangles)
			for tri in tempTriangles:
				d.drawLines(tri, DEBUG_IMAGE_copy, (255,0,0))
			cv2.imwrite('../frames/frame'+str((i*2)+1)+".png", DEBUG_IMAGE_copy)
			cv2.imshow("DEBUG_IMAGE_copy", DEBUG_IMAGE_copy)
			cv2.waitKey()
    			
		triangles.extend(tempTriangles)

	filteredTriangles = trianglesPostFiltering(triangles)

	return filteredTriangles


def getTheKeypoints_justPoints_inner(img):
	gaussW = 21
	#img2 = img.copy()
	img = recolour(img, gaussW)

	b, g, r = cv2.split(img)
	#img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
	img = b
	#cv2.imshow('b',b)
	#cv2.waitKey()
	points1 = []
	points1.extend(getTheKeypoints_justPoints_inner_inner(b))
#	points1.extend(getTheKeypoints_justPoints_inner_inner(g, img2))
#	points1.extend(getTheKeypoints_justPoints_inner_inner(r, img2))
	return points1



def getTheKeypoints_justPoints_inner_inner(channel):
	img = channel
	ret,img = cv2.threshold(img,127,255,cv2.THRESH_BINARY)
	
	#img2 = img.copy()
#	cv2.imshow('here..'+str(img.shape), img2)
#	cv2.waitKey()
	contours, hierarchy = cv2.findContours(img,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
	
	finCnts = []
	area_here = 400
	area_here_max = 600
	for cnt in contours:
		if cv2.contourArea(cnt) > area_here:
			finCnts.append(cnt)

	contours = finCnts

	finCnts = []
	for cnt in contours:
		M = cv2.moments(cnt)
		cX = int(M["m10"] / M["m00"])
		cY = int(M["m01"] / M["m00"])
		finCnts.append( (cX, cY) )


	#for i in range(len(contours)):
	#	cv2.drawContours(img2, contours, i, (0,0,255), 1)
	#	cv2.circle(img2, finCnts[i], 3, (255, 0, 0), -1)

	#print "len(contours):" + str(len(contours))
	for i in range(len(contours)):
		#continue
		cnt = contours[i]
		#print "cnt"
		#print cnt
		ret = []
		for pnt in cnt:
			pt = pnt[0]
			ret.append( (pt[0], pt[1]) )

		#print ret
		xcoords, ycoords = kp.genImagesWithDisplayFix( np.array(ret) )
	#		print "shape"+str(i)+" = " + str(ret)
		#print xcoords[0]
		#print ycoords[0]

		for i in range(len(xcoords[0])):
			#cv2.circle(img2, ( int(xcoords[0][i]), int(ycoords[0][i]) ), 3, (255, 0, 0), -1)
			xs = xcoords[0][i]
			ys = ycoords[0][i]
			finCnts.append( (xs, ys) )
	#import time		
	#cv2.imshow('t1'+str(time.time()), img2)
	
	print "Number of keypoints: " + str(len(finCnts))
	return finCnts
	# if len(finCnts) > 200:
	# 	return finCnts[0:200]
	# else:
	# 	return finCnts

g_pixelVals = [16, 124, 115, 68, 98, 176, 225, 
55, 50, 53, 129, 19, 57, 160, 143, 237, 75, 164, 
206, 167, 103, 140, 90, 112, 244, 240, 107, 202, 185, 
72, 71, 109, 74, 183, 205, 46, 121, 180, 142, 126, 38, 247, 
166, 144, 67, 134, 194, 198, 23, 186, 33, 163, 24, 117, 37, 
76, 147, 47, 52, 42, 70, 108, 30, 54, 89, 59, 73, 91, 151, 
6, 173, 86, 182, 178, 10, 207, 171, 13, 77, 88, 159, 125, 
11, 188, 238, 41, 92, 118, 201, 132, 48, 28, 195, 17, 119, 64, 
25, 45, 114, 80, 187, 105, 204, 158, 20, 169, 83, 191, 199, 234, 
136, 81, 252, 141, 242, 219, 138, 161, 154, 135, 63, 153, 239, 130, 223, 249, 122, 93, 216, 127, 
111, 15, 12, 8, 44, 193, 245, 0, 235, 120, 31, 
165, 3, 155, 43, 26, 152, 94, 29, 232, 35, 218, 230, 233, 214, 217, 7, 156, 189, 228, 
137, 209, 145, 226, 97, 215, 170, 51, 224, 100, 61, 69, 250, 4, 34, 56, 255, 60, 84, 110, 203, 
222, 133, 248, 106, 212, 87, 253, 208, 101, 116, 251, 190, 99, 32, 113, 157, 27, 79, 82, 146, 149, 
5, 210, 65, 22, 181, 131, 62, 36, 184, 196, 231, 192, 66, 213, 2, 254, 174, 211, 236, 229, 58, 221, 21, 
150, 123, 175, 177, 179, 246, 96, 227, 1, 18, 241, 49, 128, 78, 40, 14, 162, 85, 39, 172, 104, 
9, 200, 220, 139, 168, 95, 243, 197, 148, 102]


def recolour(img, gaussW=41):
	newg_pixelVals = g_pixelVals
	div = 40
	for i in range(len(g_pixelVals)/div):
		for j in range(div):
			newg_pixelVals[i*div + j] = newg_pixelVals[i*div]

		finalCount = (i*div) + div


	for i in range( len(g_pixelVals) - finalCount ):
		newg_pixelVals[ len(g_pixelVals) -1 - i ] = newg_pixelVals[ finalCount ]


	img2 = img
	img2 = cv2.GaussianBlur(img2,(gaussW,gaussW),0)
	img  = cv2.cvtColor(img2,cv2.COLOR_BGR2GRAY)

	height, width= img.shape
	for i in range(0, height):             #looping at python speed...
		for j in range(0, width):     #...
			val = img[i,j]
			val = newg_pixelVals[val]

			if val%3 == 0:
				threeVal = (0,0,val)
			elif val%3 == 1:
				threeVal = (0,val,0)
			else:
				threeVal = (val,0,0)

			img2[i,j] = threeVal

	return img2
#	cv2.imwrite(imgName + 'blur' + str(gaussW) + '_lenna_big_diff_cols.png', img2)
	#cv2.waitKey()

def getTheKeyPoints(img):
	return getTheKeypoints_justPoints_inner(img)

def getTheTriangles(points, DEBUG_IMAGE=None, DEBUG_KEYPOINTS=None):
	return fromPointsToFramenets_justTriangles(points, DEBUG_IMAGE=DEBUG_IMAGE, DEBUG_KEYPOINTS=DEBUG_KEYPOINTS)

def getTheFragments(img):
	points = getTheKeypoints_justPoints_inner(img)
	ret = fromPointsToFramenets_justTriangles(points)
	return ret