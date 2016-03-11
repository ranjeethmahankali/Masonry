
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
		elif self.type == 4: # this is a half brick cut along length
			dimension[1] = dimension[1]/2
		
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

#returns length per unit parameter atany point on a curve
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

class bond:
	def __init__(self, courseList,startCourse, endCourse, unitLength, unitHeight, dimension):
		#this list contains all the details of all courses
		self.course = courseList
		self.startBricks = startCourse
		self.endBricks = endCourse
		
		self.unitL = unitLength
		self.unitH = unitHeight
		self.dim = dimension
	
	def placeSampleUnit(self, pos, vec):
		u = rs.VectorUnitize(vec)
		v = rs.VectorUnitize(rs.VectorRotate(vec,90,[0,0,1]))
		
		c = 0
		while c < len(self.course):
			b = 0
			while b < len(self.course[c]):
				p = self.course[c][b][0]
				pVec = rs.VectorAdd(rs.VectorScale(u,p[0]*self.unitL), rs.VectorScale(v,p[1]*self.unitL))
				newPos = rs.VectorAdd(pos,pVec)
				newPos[2] = c*self.unitH
				
				type = self.course[c][b][1]
				orientation = self.course[c][b][2]
				
				newBrick = brick(newPos, list(brickDim), type)
				brickDir = rs.VectorRotate(u,orientation,[0,0,1])
				newBrick.alignWith(brickDir)
				
				b += 1
			c += 1
		
class Wall:
	def __init__(self, curveID, bondConfig, ht, mortarThickness = 10):
		self.height = ht
		self.mortarT = mortarThickness
		self.pathID = curveID
		self.id = rs.AddGroup()
		
		self.bond = bondConfig
		
		self.courseNum = math.ceil(self.height/self.bond.unitH)
		#print('Hello')
		#print(str(self.courseNum) + ' courses')
		
		self.brickCount = 0
		
		self.bondOptions = []
		
		self.flip = False # make this -90 to flip the wall

	def build(self):
		dom = rs.CurveDomain(self.pathID)
		uL = self.bond.unitL
		
		def placeBricks(startParam, extraCourse, courseNum):
			c = decideCourse(courseNum, len(self.bond.course))
			b = 0
			while b < len(extraCourse[c]):
				posParam = extraCourse[c][b][0]
				type = extraCourse[c][b][1]
				angle = extraCourse[c][b][2]
				
				traverse = traverseTo(posParam, uL, self.pathID, startParam, self.mortarT)
				brickPos = traverse[0]
				newP = traverse[1]
				zShift = [0,0,(courseNum-1)*self.bond.unitH]
				
				if brickPos is None:
					b += 1
				else:
					#print(zShift, brickPos)
					brickPos = rs.VectorAdd(brickPos, zShift)
					
					tangent = rs.CurveTangent(self.pathID, newP)
					u = rs.VectorUnitize(tangent)
					if self.flip:
						u = rs.VectorReverse(u)
					v = rs.VectorRotate(u, 90, [0,0,1])
					
					brickDir = rs.VectorRotate(u, angle, [0,0,1])
					
					newBrick = brick(brickPos, list(brickDim), type)
					rs.AddObjectToGroup(newBrick.id, self.id)
					self.brickCount += 1
					newBrick.alignWith(brickDir)
						
					b += 1
		
		def traverseTo(uv,unitD, curID, startParam, morT):
			dom = rs.CurveDomain(curID)
			p1 = startParam
			uCur = 0
			while uCur < uv[0]:
				pStep = 0.5*unitD/distRatio(curID, startParam)
				p1 += pStep
				
				uCur += 0.5
			
			if p1 > dom[1]:
				return [None, dom[1]]
			
			tan = rs.CurveTangent(curID, p1)
			u = rs.VectorUnitize(tan)
			if self.flip:
				u = rs.VectorReverse(u)
			v = rs.VectorRotate(u, 90, [0,0,1])
			
			pos = rs.EvaluateCurve(self.pathID, p1)
			# now add the vcomponent to the pos
			pos = rs.VectorAdd(pos, rs.VectorScale(v, (uv[1]*unitD)))
			return [pos,p1]
		
		def decideCourse(cNum, bondCourses):
			return (cNum-1)%bondCourses

		cN = 1
		while cN <= self.courseNum:
			c = decideCourse(cN, len(self.bond.course))
			#placing the bricks for a nice finishing at the start of the wall
			placeBricks(dom[0],self.bond.startBricks,cN)
			param = dom[0]
			while param < dom[1]:
				b = 0
				while b < len(self.bond.course[c]):
					#lay this particular brick
					posParam = self.bond.course[c][b][0]
					type = self.bond.course[c][b][1]
					angle = self.bond.course[c][b][2]
					
					traverse = traverseTo(posParam, uL, self.pathID, param,self.mortarT)
					brickPos = traverse[0]
					newP = traverse[1]
					zShift = [0,0,(cN-1)* self.bond.unitH]
					
					if brickPos is None:
						b += 1
					else:
						#print(zShift, brickPos)
						brickPos = rs.VectorAdd(brickPos, zShift)
						
						tangent = rs.CurveTangent(self.pathID, newP)
						u = rs.VectorUnitize(tangent)
						if self.flip:
							u = rs.VectorReverse(u)
						v = rs.VectorRotate(u, 90, [0,0,1])
						
						brickDir = rs.VectorRotate(u, angle, [0,0,1])
						
						newBrick = brick(brickPos, list(brickDim), type)
						rs.AddObjectToGroup(newBrick.id, self.id)
						self.brickCount += 1
						newBrick.alignWith(brickDir)
							
						b += 1
				
				reset = self.bond.dim
				reset[1] = 0
				pNew = traverseTo(reset, uL, self.pathID, param,self.mortarT)[1]
				param = pNew
				#rs.AddPoint(rs.EvaluateCurve(self.pathID, param))
			cN += 1
	
	def buildRandom(self):
		dom = rs.CurveDomain(self.pathID)
		uL = self.bond.unitL
		
		def traverseTo(uv,unitD, curID, startParam, morT):
			dom = rs.CurveDomain(curID)
			p1 = startParam
			uCur = 0
			while uCur < uv[0]:
				pStep = 0.5*unitD/distRatio(curID, startParam)
				p1 += pStep
				
				uCur += 0.5
			
			if p1 > dom[1]:
				return [None, dom[1]]
			
			tan = rs.CurveTangent(curID, p1)
			u = rs.VectorUnitize(tan)
			if self.flip:
				u = rs.VectorReverse(u)
			v = rs.VectorRotate(u, 90, [0,0,1])
			
			pos = rs.EvaluateCurve(self.pathID, p1)
			# now add the vcomponent to the pos
			pos = rs.VectorAdd(pos, rs.VectorScale(v, (uv[1]*unitD)))
			return [pos,p1]
			
		def placeBricks(startParam, extraCourse, courseNum):
			c = decideCourse(courseNum, len(self.bond.course))
			b = 0
			while b < len(extraCourse[c]):
				posParam = extraCourse[c][b][0]
				type = extraCourse[c][b][1]
				angle = extraCourse[c][b][2]
				
				traverse = traverseTo(posParam, uL, self.pathID, startParam, self.mortarT)
				brickPos = traverse[0]
				newP = traverse[1]
				zShift = [0,0,(courseNum-1)*self.bond.unitH]
				
				if brickPos is None:
					b += 1
				else:
					#print(zShift, brickPos)
					brickPos = rs.VectorAdd(brickPos, zShift)
					
					tangent = rs.CurveTangent(self.pathID, newP)
					u = rs.VectorUnitize(tangent)
					if self.flip:
						u = rs.VectorReverse(u)
					v = rs.VectorRotate(u, 90, [0,0,1])
					
					brickDir = rs.VectorRotate(u, angle, [0,0,1])
					
					newBrick = brick(brickPos, list(brickDim), type)
					rs.AddObjectToGroup(newBrick.id, self.id)
					self.brickCount += 1
					newBrick.alignWith(brickDir)
						
					b += 1

		def decideCourse(cNum, bondCourses):
			return (cNum-1)%bondCourses
		
		cN = 1
		while cN <= self.courseNum:
			c = decideCourse(cN, len(self.bond.course))
			#placing the bricks for a nice finishing at the start of the wall
			placeBricks(dom[0],self.bond.startBricks,cN)
			
			param = dom[0]
			while param < dom[1]:
				b = 0
				randNum = random.randint(1,len(self.bondOptions)) - 1
				curBond = self.bondOptions[randNum]
				while b < len(curBond .course[c]):
					#lay this particular brick
					
					posParam = curBond .course[c][b][0]
					type = curBond .course[c][b][1]
					angle = curBond .course[c][b][2]
					
					traverse = traverseTo(posParam, uL, self.pathID, param,self.mortarT)
					brickPos = traverse[0]
					newP = traverse[1]
					zShift = [0,0,(cN-1)*curBond.unitH]
					
					if brickPos is None:
						b += 1
					else:
						#print(zShift, brickPos)
						brickPos = rs.VectorAdd(brickPos, zShift)
						
						tangent = rs.CurveTangent(self.pathID, newP)
						u = rs.VectorUnitize(tangent)
						if self.flip:
							u = rs.VectorReverse(u)
						v = rs.VectorRotate(u, 90, [0,0,1])
						
						brickDir = rs.VectorRotate(u, angle, [0,0,1])
						
						newBrick = brick(brickPos, list(brickDim), type)
						rs.AddObjectToGroup(newBrick.id, self.id)
						self.brickCount += 1
						newBrick.alignWith(brickDir)
							
						b += 1
				
				reset = self.bond.dim
				reset[1] = 0
				pNew = traverseTo(reset, uL, self.pathID, param,self.mortarT)[1]
				param = pNew
				#rs.AddPoint(rs.EvaluateCurve(self.pathID, param))
			cN += 1

englishBondCourses = [
					[#course1
						[[0,0],0,0],
						[[0,1],0,0]
						],
					[#course2
						[[1.5,0,0,0],0,90],
						[[2.5,0,0.5,0],0,90]
						]
					]
					
englishStart = [
				[#course1
					#no starting bricks in 1st course
					],
				[
					[[0.5,0],4,90]
					]
				]
				
englishEnd = [
				[#course1
					[[2.5,0],4,90]
					],
				[#no bricks in course 2
					]
				]

flemishBondCourses = [
					[#course1
						[[0,0],0,0],
						[[0,1],0,0],
						[[3,0],0,90]
						],
					[#course2
						[[1.5,0],0,90],
						[[1.5,0],0,0],
						[[1.5,1],0,0]
						]
					]

bond1Courses = [
				[#course1
					[[0,0],0,0],
					[[0,1],0,0]
					],
				[#course2
					#[[1.5,0],0,90],
					[[2.5,0],0,90]
					]
			]

bond2Courses = [
				[#course1
					[[0,0],0,0]
					,[[0,1],0,0]
					],
				[#course2
					[[1.5,0],3,90]
					,[[2.5,0],0,90]
					,[[1.5,1.5],1,90]
					]
			]

bond3Courses = [
				[#course1
					[[0,0],0,0]
					,[[0,1],0,0]
					],
				[#course2
					[[1.5,0],3,90]
					,[[2.5,0],0,90]
					#,[[1.5,1.5],1,0]
					]
			]

englishBond = bond(englishBondCourses, englishStart, englishEnd, 115, 80, [2,2])
#flemishBond = bond(flemishBondCourses, 115 , 80, [3,2])

# this is an english bond with holes
WallBond1 = bond(bond1Courses, englishStart, englishEnd, 115, 80, [2,2])

# this is an english bond with projections
WallBond2 = bond(bond2Courses, englishStart, englishEnd, 115, 80, [2,2])

# this is an english bond with depressions
WallBond3 = bond(bond3Courses, englishStart, englishEnd, 115, 80, [2,2])

brickDim = [230,115,80]
curve = rs.GetCurveObject('Select Curve')
height = rs.GetInteger('Enter Wall height', 2000)

newWall = Wall(curve[0], englishBond, height)
newWall.bondOptions.append(WallBond2)
newWall.bondOptions.append(WallBond3)

rs.EnableRedraw(False)
newWall.buildRandom()
#newWall.build()
rs.EnableRedraw(True)

#course =  []
#course[i] = []
#course[i][j] = [pos, type, orientation]