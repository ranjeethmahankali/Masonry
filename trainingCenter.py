import rhinoscriptsyntax as rs
import masonry as ms

#rs.Command('_SelAll _Delete')
#rs.Command('Import') 

i = 0
while True:
	bottomCurve = rs.GetCurveObject('select bottom curve')[0]
	topCurve = rs.GetCurveObject('select top curve')[0]
	
	if bottomCurve and topCurve:
		bottomPlane = rs.CurvePlane(bottomCurve)
		topPlane = rs.CurvePlane(topCurve)
		
		height = topPlane[0][2] - bottomPlane[0][2]
		newWall = ms.Wall(bottomCurve, ms.englishBond, height)
		newWall.flip = newWall.flip
		
		#newWall.bondOptions.append(ms.englishBond)
		newWall.bondOptions.append(ms.WallBond2)
		newWall.bondOptions.append(ms.WallBond3)
		randomWall = rs.GetString('Jagged Wall ?','n')
		
		
		rs.EnableRedraw(False)
		if randomWall == 'y':
			newWall.buildRandom()
		else:
			newWall.build()
		rs.EnableRedraw(True)
		
		i += 1
	else:
		break