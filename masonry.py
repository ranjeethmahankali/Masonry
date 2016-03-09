
import rhinoscriptsyntax as rs
import random
import math

# this method returns the component of vec1 along vec2
def component(vec1, vec2):
	dotProduct = rs.VectorDotProduct(vec1, vec2)
	modVec2 = rs.VectorLength(vec2)
	unitVec2 = rs.VectorUnitize(vec2)
	
	component = rs.VectorScale(unitVec2, dotProduct/modVec2)
	
	return component

class brick:
	#initializes a new brick of dimensions - dim, with the center of its base positioned at 'pos'
	#dim is a list of the form [length, width, height]
	# in counter clockwise order, bottomplane first
	
	def __init__(self, pos, dimension, typeOfBrick = 0):
		self.type = typeOfBrick
		
		#Now determining setting the true dimensions of the brick based on its type
		if self.type == 1: # this is a halfBrick
			dimension[0] = dimension[0]/2
		elif self.type == 2: # this is a Quarter brick
			dimension[0] = dimension[0]/4
		elif self.type == 3: # this is a 3/4ths of a brick
			dimension[0] = dimension[0]*3/4
		
		self.dim = dimension
		self.base = pos
		
		u = [self.dim[0], 0, 0]
		v = [0, self.dim[1], 0]
		w = [0, 0, self.dim[2]]
		
		vert = []
		vert.append(pos)
		p = rs.VectorAdd(pos,u)
		vert.append(p)
		p = rs.VectorAdd(p,v)
		vert.append(p)
		p = rs.VectorSubtract(p,u)
		vert.append(p)
		
		i = 0
		while i < 4:
			p1 = rs.VectorAdd(vert[i], w)
			vert.append(p1)
			i += 1
		
		self.id = rs.AddBox(vert)
		clearIsoCurves = rs.SurfaceIsocurveDensity(self.id, 0)
		self.vertex = vert
		self.direction = u
	
	def rotateBrick(self, angle, axis):
		done = rs.RotateObject(self.id, self.base, angle, axis)
		if done:
			self.direction = rs.VectorRotate(self.direction, angle, axis)
			return True
		else:
			return False
	
	#this function aligns the brick with the given vector
	def alignWith(self, vec):
		axis = rs.VectorCrossProduct(self.direction, vec)
		angle = rs.VectorAngle(vec, self.direction)
		
		done = rs.RotateObject(self.id, self.base, angle, axis)
		if done:
			self.direction = rs.VectorRotate(self.direction, angle, axis)
			return True
		else:
			return False
	
	#moves the brick to newPos - base position
	def moveTo(self, newPos):
		translation = rs.VectorSubtract(newPos, self.base)
		self.id = rs.MoveObject(self.id, translation)
		if self.id:
			self.base = newPos
		
	# calculated the intercept of the brick in the direction vec
	def intercept(self, vec):
		aspectAng = math.atan(self.dim[1]/self.dim[0])
		vecAng = math.pi*rs.VectorAngle(self.direction, vec)/180
		
		if vecAng < aspectAng or vecAng > (math.pi-aspectAng):
			return abs(self.dim[0]/math.cos(vecAng))
		elif vecAng > aspectAng and vecAng < (math.pi - aspectAng):
			return self.dim[1]/math.sin(vecAng)

def distRatio(curID, param):
	domain = rs.CurveDomain(curID)
	sample = (domain[1] - domain[0])/1000000
	
	pt = rs.EvaluateCurve(curID, param)
	param2 = param + sample
	pt2 = rs.EvaluateCurve(curID, param2)
	dist = rs.Distance(pt, pt2)
	
	return (dist/sample)
	
def makeCurves(curveID, layerNum, spacing):
	dom = rs.CurveDomain(curveID)
	tan = rs.CurveTangent(curveID, dom[0])
	normal = rs.CurveNormal(curveID)
	dir = rs.VectorRotate(normal,90,tan)
	
	layerEven = False
	if layerNum%2:
		offsetBound = spacing*(layerNum-1)/2
	else:
		layerEven = True
		offsetBound = spacing*((layerNum/2)-0.5)
	
	curves = []
	i = -offsetBound
	while i <= offsetBound:
		newCurve = rs.OffsetCurve(curveID, dir, i)
		if newCurve:
			curves.append(newCurve[0])
		else:
			duplicate = rs.CopyObject(curveID, [0,0,0])
			curves.append(duplicate)
		
		i += spacing
	
	if layerEven:
		rs.DeleteObject(curveID)
		
	return curves
	
def craziness(iterNum):
	return 0
	#return 20*math.sin(45*iterNum*math.pi/180)
	#return 15*iterNum
	#return iterNum
	#return random.uniform(-10,10)+90
	#return random.uniform(-20,20)
	#return 20
	
	num = random.randint(0,4)
	if num == 0:
		return 90
	else:
		return 0

class Wall:
	def __init__(self, curveID, lNum, ht):
		self.height = ht
		self.mortarThickness = 10
		self.centerLine = curveID
		courseNum = ht/(brickDim[2]+self.mortarThickness)
		self.id = rs.AddGroup()
		curveList = makeCurves(curveID, lNum, (brickDim[1]+self.mortarThickness))
		
		self.brickCount = 0
		
		isEven = False
		c = 0 # iterating variable representing the current course Number
		while c < courseNum:
			
			layer = 0
			layerEven = False
			while layer < len(curveList):
				curID = rs.CopyObject(curveList[layer], [0,0,0])
				dom = rs.CurveDomain(curID)
				p = dom[0]
				pShiftLayer = (brickDim[0]/2)/distRatio(curID, p)
				if layerEven:
					p += pShiftLayer
				
				if isEven:
					pShift = (brickDim[0]/4)/distRatio(curID, p)
					p += pShift
			
				n = 0
				nLimit = 8
				while p <= dom[1]:
					pt = rs.EvaluateCurve(curID, p)
					block = brick(pt, brickDim)
					self.brickCount += 1
					
					tangent = rs.CurveTangent(curID, p)
					axis = rs.VectorCrossProduct(block.direction, tangent)
					brickDir = rs.VectorRotate(tangent, craziness(n), axis)
					aligned = block.alignWith(brickDir)
					if not aligned:
						print('Something went wrong with the alignment')
					
					#print(block.intercept(brickDir))
					step = (block.intercept(tangent)/2)/distRatio(curID, p)
					p += step
					pt = rs.EvaluateCurve(curID, p)
					block.moveTo(pt)
					
					# checking of the angle between the two vectors is almost 90
					if abs(rs.VectorAngle(tangent, brickDir)-90) < 0.1:
						#vector joining current point to closes point on the center line curve
						unitNormal = rs.VectorUnitize(brickDir)
						
						moveVec = rs.VectorScale(unitNormal, block.dim[0]/4)
						finalPt = rs.VectorAdd(block.base, moveVec)
						
						block.moveTo(finalPt)
					
					rs.AddObjectToGroup(block.id, self.id)
					
					step = ((block.intercept(tangent)/2)+self.mortarThickness)/distRatio(curID, p)
					p += step
					n += 1
				
				layer += 1
				layerEven = not layerEven
				rs.DeleteObject(curID)
				
			c += 1
			isEven = not isEven
			
			zStep = brickDim[2]+self.mortarThickness
			curveList = rs.MoveObjects(curveList, [0,0,zStep])
		
		rs.DeleteObjects(curveList)
		
brickDim = [230,115,80]
curve = rs.GetCurveObject('Select Curve')
layers = rs.GetInteger('Enter Number of Layers',1)
height = rs.GetInteger('Enter Wall height', 2000)

rs.EnableRedraw(False)
newWall = Wall(curve[0], layers, height)
#newBrick = brick([0,0,0], brickDim, 1)
rs.EnableRedraw(True)