import rhinoscriptsyntax as rs
import random
import math

class brick:
	#initializes a new brick of dimensions - dim, with the center of its base positioned at 'pos'
	#dim is a list of the form [length, width, height]
	# in counter clockwise order, bottomplane first
	
	def __init__(self, pos, dimension):
		halfL = [dimension[0]/2, 0, 0]
		halfW = [0, dimension[1]/2, 0]
		halfH = [0, 0, dimension[2]]
		
		self.dim = dimension
		self.base = pos
		
		vert = []
		p = rs.VectorAdd(pos,halfL)
		p = rs.VectorAdd(p,halfW)
		vert.append(p)
		p = rs.VectorSubtract(pos,halfL)
		p = rs.VectorAdd(p,halfW)
		vert.append(p)
		p = rs.VectorSubtract(pos,halfL)
		p = rs.VectorSubtract(p,halfW)
		vert.append(p)
		p = rs.VectorAdd(pos,halfL)
		p = rs.VectorSubtract(p,halfW)
		vert.append(p)
		
		i = 0
		while i < 4:
			p1 = rs.VectorAdd(vert[i], halfH)
			vert.append(p1)
			i += 1
		
		self.id = rs.AddBox(vert)
		self.vertex = vert
		self.direction = halfL
	
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
		
		blockID = self.rotateBrick(angle, axis)
		if blockID:
			return blockID
		else:
			return None
		
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
			curves.append(curveID)
		
		i += spacing
	
	if layerEven:
		rs.DeleteObject(curveID)
		
	return curves
	
def craziness(iterNum):
	#return 0
	#return 20*math.sin(30*iterNum*math.pi/180)
	#return 15*iterNum
	return 5*iterNum
	#return random.uniform(-10,10)+90
	#return random.uniform(-20,20)
	#return 20

class Wall:
	def __init__(self, curveID, lNum, ht):
		self.height = ht
		self.mortarThickness = 10
		courseNum = ht/(brickDim[2]+self.mortarThickness)
		self.id = rs.AddGroup()
		curveList = makeCurves(curveID, lNum, (brickDim[1]+self.mortarThickness))
		
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
					pShift = (brickDim[0]/2)/distRatio(curID, p)
					p += pShift
			
				n = 0
				while p <= dom[1]:
					pt = rs.EvaluateCurve(curID, p)
					block = brick(pt, brickDim)
					
					tangent = rs.CurveTangent(curID, p)
					axis = rs.VectorCrossProduct(block.direction, tangent)
					tangent = rs.VectorRotate(tangent, craziness(n), axis)
					
					block.alignWith(tangent)
					
					clear = rs.SurfaceIsocurveDensity(block.id, 0)
					rs.AddObjectToGroup(block.id, self.id)
					
					step = (block.intercept(tangent)+self.mortarThickness)/distRatio(curID, p)
					p = p + step
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
rs.EnableRedraw(True)