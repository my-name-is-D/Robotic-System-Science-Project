#! /usr/bin/env python

import rospy
from nav_msgs.msg import OccupancyGrid
from nav_msgs.msg import Odometry #to get his position
import matplotlib.pyplot as plt
import numpy as np
#from rss_project.srv import *
from rss_project.srv import find_goals, find_goalsResponse
import time

resolution = 0.05	# resolution of the image in m/px
offsetX = -15		# offset of the reduced map
offsetY = -15
fullSizeX = 4000	# Size in pixel of the map 4000px <-> 200m
fullSizeY = 4000
reducedSizeX = 600	# size of the map once reduced in px 600px <-> 30m
reducedSizeY = 600

cell_size = 2
""" test with another map, the first one of the arena
resolution = 0.05	# resolution of the image in m/px
offsetX = -13.8#-15		# offset of the reduced map
offsetY = -15.4#-15
reducedSizeX = 544	# size of the map once reduced in px 600px <-> 30m
reducedSizeY = 544 #size of the map once reduced in px 100px<->5.2m
fullSizeX = 544	# Size in pixel of the map 4000px <-> 200m
fullSizeY = 544 #Size in pixel of the map 544px <-> 27.2m
"""
#odometry
poseX=0
poseY=0

class get_final_map():

	def __init__(self,start):
		self.occupiedCells= []
		self.freeCells= []
		self.unknowncells= []
		self.coastmap= []
		self.start=start
		#self.sub = rospy.Subscriber('/ros_ass_world', the_map, self.callback)
		#self.sub = rospy.Subscriber('/map', OccupancyGrid, self.callback)
		#self.sub2=rospy.Subscriber('/odom', Odometry, self.callback_odom)
		self.pathX=[]
		self.pathY=[]
		self.done=False
		#self.pub= rospy.Publisher("/project_g",the_map,queue_size=10)


	def my_return(self): 
		time_begin = rospy.Time.now()
		if self.start==True: # if the service sent the order to start
			doneOnce=False
			if doneOnce==False: #we start those callback only once
				sub2=rospy.Subscriber('/odom', Odometry, self.callback_odom)
				sub = rospy.Subscriber('/map', OccupancyGrid, self.callback)
				doneOnce=True
				print("in")#check
			while self.done==False:
				check=1 #just so it isn't empty
			""" in case it was too long, done because of bugs resolved now
			while self.pathX==[]:
				time_end = rospy.Time.now()
				if (time_end-time_begin).to_sec()> 10:
					rospy.loginfo("check_map reacting too slow")
					break
			"""
		
		return self.pathX, self.pathY	
			
	def callback_odom(self,msg): #get odometry
		if self.start==True:
			global poseX
			global poseY
			poseX,poseY=convert_xy_to_px(msg.pose.pose.position.x,msg.pose.pose.position.y)	 		


	def callback(self,msg): #get trajectoy
		global poseX
		global poseY
		fpathX,fpathY=[],[] #final_path lists
		if self.start==True:
			print ("on it")
			grid_px = msg.data  #data is the map 
			grid_2D = convert_1D_to_2D(grid_px)
			coastmap = create_final_coastmap(grid_2D)
			
			startx=poseX #we get the position of the robot
			starty=poseY
			print (startx,starty) #check
			
			goals=map_division(coastmap,startx,starty) #we select a bunch of goals to travel through
			if len(goals)>0: #check if list is empty or not
				#print("still in")
				for g in range(len(goals)):
					#print(g)
					pathX,pathY=move(coastmap,startx,starty,goals[g][0],goals[g][1])
					fpathX.extend(pathX) #each new trajectory from 1goal to the next is added to he same list 
					#fpathX.extend([1000]) #at first intended to turn 360 after each goal reached
					fpathY.extend(pathY)
					#fpathY.extend([1000])

					#shapeX=np.shape(fpathX) 
					#print("shapeX")
					#print(shapeX)
					#self.pathX.reshape(1,shapeX[0]*shapeX[1]) #resolved
					startx,starty=goals[g][0],goals[g][1] #first starting point, odometry, then the last goal reached
				self.pathX=fpathX #update full path with new completed list
				self.pathY=fpathY
		

			"""
			for i in range(len(path[0])):
				print (convert_px_to_xy(path[0][i],path[1][i],cell_size))
			print ("done")

			plt.scatter(path[0],path[1])
			#plt.scatter(occupiedCells[0],occupiedCells[1],'r')
			#plt.scatter(unknownCells[0],unknownCells[1],'b')
			plt.grid(which='major',linestyle='-', alpha=0.5)
			plt.minorticks_on()
			plt.grid(which='minor', linestyle='-', alpha=0.5)
			plt.show()
			"""
		self.done=True

def convert_1D_to_2D(data1D):
	grid = np.zeros((reducedSizeX,reducedSizeY))
	x,y = fullSizeX/2-reducedSizeX/2,fullSizeY/2-reducedSizeY/2	#220	# The starting coordinates (0,0) is at the center of the map.
	for i in range(reducedSizeX*reducedSizeY):
		grid[i%reducedSizeX][int(i/reducedSizeY)] = data1D[x+y*fullSizeX]
		x += 1
		if x >= fullSizeX/2+reducedSizeX/2:
			x = fullSizeX/2-reducedSizeX/2
			y += 1
	return grid
	
# Create a coast map from the complete map
def create_final_coastmap(grid):
 
	coastmap = np.zeros((len(grid)/cell_size,len(grid[0])/cell_size))
	cursorX,cursorY = -1,-1
	for i in range(len(grid)):
		if i%cell_size == 0:
			cursorX += 1
		for j in range(len(grid[0])):
			"""try:
				if grid[i][j]<0 and grid[i+1][j+1]<0 and grid[i+1][j]<0 and grid[i][j+1]<0:
					continue
			except IndexError:
				pass
			"""
			if j%cell_size == 0: 
				cursorY += 1
			if cursorY >= len(coastmap):
				cursorY = 0
			
			#print cursorX, cursorY
			coastmap[cursorX][cursorY] += grid[i][j]
	"""
	print("map \n")
	for i in range(len(coastmap)-100):#startY,goalX):
    		for j in range(len(coastmap[0])):#startX,goalX):
			print int(coastmap[i][j]),
		print(" ")
	"""
	return coastmap

#get extremities of the map with the odometry as starting point
# then It regroups cells to form bigger cells, and check if the selected cell isn't close from another goal already selected before chosing it as new goal to reach
#could still be optimised.
def map_division(grid,startX,startY):
    
	searchx=0
	searchy=0
	goals_to_reach=[]

	#To get the extremity of the maps (not good if it's not a squered/rectangle/rond or ovale space) 
	left=0
	right=0
	up=0
	down=0

	while grid[startX-searchx][startY]>=0:
		left=startX-searchx-10 #we take one more position (unknown position), in case the map isn't perfect and starting posotion would lead to a loss of info
		searchx+=1
		
		if grid[startX-searchx][startY]<0: #To avoid stoping the process because of a thick obstacle
			if grid[startX-searchx-4][startY]>=0:
				searchx+=4
    		
	searchx=0
	while grid[startX+searchx][startY]>=0:
		right=startX+searchx+10 #-1 because of the wall present before the unknown area
		searchx+=1

		if grid[startX+searchx][startY]<0: #To avoid stoping the process because of a thick obstacle, Simulation prob, not in real time, because the boxes have "holes"
			if grid[startX+searchx+4][startY]>=0:
				searchx+=4
	
	while grid[startX][startY-searchy]>=0:
		down=startY-searchy-10 #+1 because of the wall present before the unknown area
		searchy+=1
		
		if grid[startX][startY-searchy]<0: #To avoid stoping the process because of a thick obstacle
			if grid[startX][startY-searchy-4]>=0:
				searchx+=4
		
	searchy=0
	while grid[startX][startY+searchy]>=0:
		up=startY+searchy+10 #-1 because of the wall present before the unknown area
		searchy+=1
		if grid[startX][startY+searchy]<0: #To avoid stoping the process because of a thick obstacle (inside unknowns)
			if grid[startX][startY+searchy+4]>=0:
				searchx+=4

	xlen=(right-left)
	ylen=(up-down)
	print(right,left,up,down)
	#if ((up-down) < (left-right)): #useless actually
	map_division = np.zeros((xlen,ylen)) # (x,y)
	for x in range(left, right):
		for y in range(down,up):  			
			#check if a bunch of cells are all free (4x4 cells)
			if grid[x][y]==0 and grid[x-1][y]==0 and grid[x][y-1]==0 and grid[x-1][y-1]==0 and  grid[x+1][y+1]==0 and grid[x+1][y]==0 and grid[x+1][y-1]==0 and grid[x][y+1]==0 and grid[x-1][y+1]==0: #the extremities shouldn't be a problem
				if grid[x+2][y-1]==0 and grid[x+2][y]==0 and grid[x+2][y+1]==0 and grid[x+2][y+2]==0 and grid[x+1][y+2]==0 and grid[x][y+2] ==0 and grid[x-1][y+2]==0:
					map_division[x-left][y-down]=0 #just to visualize it 
					if (len(goals_to_reach)== 0): #if there is already something in goals_to_reach, else prob 
						goals_to_reach.append([x+1, y+1])
					else: #if we have registered some goals then
						goal_too_close=False
						for i in range(len(goals_to_reach)): #check if the point selected isn't too close from a previous goal
							if ((abs((y+1)-goals_to_reach[i][1]) <8) and abs((x+1)-goals_to_reach[i][0]) <8): #if we already have a goal around this pose
								goal_too_close=True
						if (goal_too_close==False):
							goals_to_reach.append([x+1, y+1])
							map_division[x-left][y-down]=5 #to check visually
					#else:
    				#	 goals_to_reach.append([y+1, x+1])
				#else: 
				#	map_division[x-left][y-down]=1 #we will be missing some walls, visually
			else:
				map_division[x-left][y-down]=1 #we will be missing some walls, visually
	"""
	print("map division \n")		
	for i in range(xlen):#startY,goalX):
    		for j in range(ylen):#startX,goalX):
			print int(map_division[i][j]),
		print(" ")
	"""
	
	#print("goals_to reach")
	#print(goals_to_reach)
	print(np.shape(goals_to_reach))

	#If we want we can change the goals position from the closest to the further away to optimize
	#For this we do x+y of each point and get them in an order (the lowest to highest value for ex)
	
	return goals_to_reach

#decide the trajectory from one goal to the next with the wavefront technique
def move(grid,startX,startY,goalX,goalY):

	distance_map = np.zeros((len(grid),len(grid[0])))# create the map which takes the distance values from the start point. All the non calculated cells are set at 0.
	distance_map[startX][startY] = -1	# Initialize the start at -1
	lastDistX = [startX]
	lastDistY = [startY]#[38]
	
	distance=0
	next_goal=10

	free_cell=True
	
	newDistX, newDistY = [],[]
	goal_found=False
	

	while goal_found != True:
		distance+=1
		# For each cells with the highest distance:
		for i in range(len(lastDistX)):
			# Checks the 8 cells around each cell
			for m in range(3):
				for n in range(3):
					if goal_found==True:
						continue
					elif lastDistX[i]+m-1 == goalX and lastDistY[i]+n-1==goalY :
						distance_map[lastDistX[i]+m-1][lastDistY[i]+n-1] = distance
						newDistX.append(lastDistX[i]+m-1)
						newDistY.append(lastDistY[i]+n-1)	
						goal_found=True
						continue
					else:
						if grid[lastDistX[i]+m-1][lastDistY[i]+n-1] > 0 or grid[lastDistX[i]+m-1][lastDistY[i]+n-1] <0 : #in case we see through the arena
							distance_map[lastDistX[i]+m-1][lastDistY[i]+n-1] = len(grid)*len(grid[0])+1
						#give high value to cell

						# if cell not already filled, put the value of the distance to the cell in the distance_map, then ad the coordinate of the cell in newDist
						elif distance_map[lastDistX[i]+m-1][lastDistY[i]+n-1] == 0:
							canGo = True
							for p in range(5):
								for q in range(5):
									if  grid[lastDistX[i]+m-1+p-2][lastDistY[i]+n-1+q-2] > 0:
										canGo = False
							distance_map[lastDistX[i]+m-1][lastDistY[i]+n-1] = distance
							newDistX.append(lastDistX[i]+m-1)
							newDistY.append(lastDistY[i]+n-1)

		lastDistX = newDistX
		lastDistY = newDistY
	### END WHILE ###
	# Find the path to follow to reach the goal:
	pathX = [goalX]
	pathY = [goalY]
	while distance >= 2:
		distance -= 1
		nextStepFound = False
		for m in range(3):
			for n in range(3):
				if nextStepFound == True:
					continue
				elif distance_map[pathX[-1]+m-1][pathY[-1]+n-1] == distance: 
					nextStepFound = True
					pathX.append(pathX[-1]+m-1)
					pathY.append(pathY[-1]+n-1)
	"""
	print (distance)
	print ("-------------------------------------------------")
	for i in range(30,50):#startY,goalX):
		for j in range(30,50):#startX,goalX):
			print int(distance_map[j][i]),
		print(" ")
	"""
	pathX.reverse()
	pathY.reverse()
	for i in range(len(pathX)):
		pathX[i],pathY[i]=convert_px_to_xy(pathX[i],pathY[i])
		pathY[i]=-pathY[i]

	return (pathX,pathY)

# cell_size represents the number of pixel that form a cell (ex: if a cell is composed of 8x8 pixels, cell_size = 8) 
def convert_px_to_xy(x_px,y_px):
	x = x_px * resolution*cell_size + offsetX
	y = reducedSizeY*resolution - y_px * resolution*cell_size + offsetY
	return x,y

def convert_xy_to_px(x,y):
	x_px = int((x-offsetX)/(resolution*cell_size))
	y_px = int((y-offsetY)/(resolution*cell_size))
	return(x_px,y_px)

if __name__ == '__main__':
	rospy.init_node('recheck_map', anonymous=True)
	get_final_map=get_final_map()

	try:
		get_final_map.my_return()
		rospy.spin()
	#rospy.spin()
	except rospy.ROSInterruptException:
		pass
	
			
