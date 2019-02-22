# encoding: utf-8

import gvsig
from gvsig.geom import *
import math
from java.awt import Color
from org.gvsig.symbology.fmap.mapcontext.rendering.legend.impl import VectorialIntervalLegend, SingleSymbolLegend
from org.gvsig.symbology.fmap.mapcontext.rendering.legend.styling import LabelingFactory
import pdb
# math.radians(x)
from org.gvsig.expressionevaluator import ExpressionEvaluatorLocator
from org.gvsig.fmap.dal import DALLocator

to_radian = lambda degree: math.pi / 180.0 * degree
# math.degrees(x)
to_degree = lambda radian: radian * (180.0 / math.pi)

# create_point
def create_point(centroid, radian, radius):
    dx = math.cos(radian) * radius
    dy = math.sin(radian) * radius
    x = centroid.getX()
    y = centroid.getY()
    return createPoint(D2, x + dx, y + dy)
    
# create_ring_cell
def create_ring_cell(centroid, from_deg, to_deg, from_radius, to_radius, default_segs):
  step = abs(to_deg - from_deg) / default_segs
  radian = 0.0
  outer_ring = []
  # first interior
  first = True
  for index in xrange(default_segs+1):
    radian = to_radian(from_deg - (index * step))
    outer_ring.append(create_point(centroid, radian, from_radius))
    if first==True:
      point1 = create_point(centroid, radian, from_radius)
      first = False
  
  # second outer
  for index in xrange(default_segs,-1,-1):
    radian = to_radian(from_deg-(index * step))
    outer_ring.append(create_point(centroid, radian, to_radius))

  outer_ring.append(point1)
  polygon = createPolygon(D2, outer_ring)
  #print polygon
  #g = createGeometry(POLYGON, D2)
  #for i in outer_ring:
  #  g.addVertex(i)
  return polygon
    
def getInsidePoint(fgeom, ring):
    if fgeom.contains(fgeom.centroid()):
      return fgeom.centroid()
    else:
      #try:
      #  modifyGeom = fgeom.buffer(-fgeom.perimeter()*0.01)
      #  points = modifyGeom.closestPoints(fgeom) #getInteriorPoint()
      #  distPoint = False
      #  index = 0
      #  for i in range(0, len(points)):
      #    p = points[i]
      #    if distPoint==False or p.distance(ring) < distPoint:
      #      distPoint = p.distance(ring)# < distPoint
      #      index = i
      #  return points[index]
      #except:
       
      return fgeom.getInteriorPoint()
                

def getClosest(featureList, prering):
  closest = None
  mindist = 99999999999999999
  for i in range(0,len(featureList)):
      
      geomFeature = featureList[i].getFeature().getDefaultGeometry()
      if geomFeature.centroid().intersects(geomFeature):
          interiorPoint = geomFeature.centroid()
      else:
          interiorPoint = geomFeature.getInteriorPoint()
      fdist = interiorPoint.distance(prering.centroid())
      if fdist < mindist:
          mindist = fdist
          closest = i
  return featureList.pop(closest).getFeature()

def getRingCentroid(ring, centroid, r, rk,from_deg, to_deg, factorReduction):
  d = (from_deg + to_deg)/2
  radius = r + (rk/factorReduction)
  radian = to_radian(d)
  point = create_point(centroid, radian, radius)
  return point

def getRadiusFromEnvelope(envelope):
  minx = envelope.getLowerCorner().getX()
  miny = envelope.getLowerCorner().getY()
  maxx = envelope.getUpperCorner().getX()
  maxy = envelope.getUpperCorner().getY()
  radius = (((maxx - minx)**2 + (maxy - miny)**2) **0.5) / 2.0
  return radius
  
def createRingMap(
        store, 
        table, 
        idStore, 
        idTable, 
        fields, 
        default_segs, 
        gaps, 
        half_step, 
        internalRadius, 
        radiusInterval,
        centerTopSector,
        labelOnlyFirstSector,
        labelIdSector,
        createSectorLabel):
  # Pre vars
  ring_num = len(fields) # number fileds
  if store.getFeatureSelection().getSize()>0:
    featureSet = store.getSelection()
  else:
    featureSet = store.getFeatureSet()

  feature_count = featureSet.getSize()
  featureList = []

  envelopeSelection = GeometryLocator.getGeometryManager().createEnvelope(D2)
  for feature in featureSet:
    featureList.append(feature.getReference())
    envelopeSelection.add(feature.getDefaultGeometry().getEnvelope())
    
  # Prepare radius from envelope
  envelope = envelopeSelection #store.getEnvelope()
  
  centroid = envelope.getGeometry().centroid()
  
  if centroid.isValid()==False and featureSet.getSize()==1:
      centroid = featureList[0].getFeature().getDefaultGeometry().getInteriorPoint()

  if internalRadius > 0:
    radius = internalRadius
  else: 
    radius = getRadiusFromEnvelope(envelope)
   
    if radius==0: # radius can be 0 from extent of a single point
        radius=getRadiusFromEnvelope(store.getEnvelope())
        
        
  # Prepare radiusInterval
  if radiusInterval > 0:
      radius_interval = radiusInterval
  else:
      radius_interval = radius / ring_num

  # Prepare schema
  newSchema = gvsig.createFeatureType()
  newSchema.append("LABEL", "STRING", 20)
  newSchema.append("VALUE", "DOUBLE", 20,5)
  newSchema.append("NUMSECTOR", "INTEGER", 10)
  newSchema.append("NUMRING", "INTEGER", 10)
  newSchema.append("ROTATION", "DOUBLE", 10,5)
  newSchema.append("GEOMETRY", "GEOMETRY")
  newSchema.get("GEOMETRY").setGeometryType(POLYGON, D2)
  ringShape = gvsig.createShape(newSchema)
  

  # Line shape
  lineSchema = gvsig.createFeatureType(table.getDefaultFeatureType())
  rm = lineSchema.getEditableAttributeDescriptor("GEOMETRY")
  if rm!=None:
    lineSchema.remove(rm)
  lineSchema.append("GEOMETRY", "GEOMETRY")
  lineSchema.get("GEOMETRY").setGeometryType(LINE, D2)
  lineShape = gvsig.createShape(lineSchema)
  lineShape.edit()
  
  # Point-label shape
  pointSchema = gvsig.createFeatureType(ringShape.getFeatureStore().getDefaultFeatureType())
  pointSchema.append("STRVALUE", "STRING", 20)
  pointSchema.get("GEOMETRY").setGeometryType(POINT, D2)
  pointShape = gvsig.createShape(pointSchema)
  pointStore=pointShape.getFeatureStore()
  pointShape.edit()
  
  # Vars
  ringStore = ringShape.getFeatureStore()
  ringShape.edit()

  step_angle = 360.0 / feature_count

  if centerTopSector:
    half_step = half_step + (step_angle/2) #-((default_segs*gaps)/2)

  idx_side = 0

  correction_from_deg = (((step_angle/default_segs)*gaps)/2)
  correction_to_deg = (((step_angle/default_segs)*gaps)/2)
  
  for i in xrange(0, feature_count):
    from_deg = half_step - (idx_side * step_angle) - correction_from_deg
    to_deg = half_step - ((idx_side + 1) * step_angle) + correction_to_deg
    
    # Get closest
    rin = radius+(radius_interval*(1))
    rout = radius

    prering = create_ring_cell(centroid, from_deg, to_deg, rin, rout, default_segs).centroid()
    feature = getClosest(featureList, prering)
    builder = store.createExpressionBuilder()
    for iring in xrange(0, len(fields)):
      #featureIdValues = table.findFirst(str(idTable)+"="+str(feature.get(idStore)))
          # QUERY
      
      ## Eq expression
      expFilter = builder.eq(
            builder.column(idTable),
            builder.constant(feature.get(idStore))
            ).toString()
      #exp = ExpressionEvaluatorLocator.getManager().createExpression()
      #exp.setPhrase(expFilter)
      #evaluator = DALLocator.getDataManager().createExpresion(exp)
      #featureIdValues = table.findFirst(evaluator)
      featureIdValues = table.findFirst(expFilter)

      #fq1 = store.createFeatureQuery()
      #fq1.setFilter(evaluator)
      #fq1.retrievesAllAttributes()
      
      new = ringStore.createNewFeature()
      rin = radius+(radius_interval*(iring+1))
      rout = radius+(radius_interval*iring)
      ring = create_ring_cell(centroid, from_deg, to_deg, rin, rout,  default_segs)
      new.set("LABEL", fields[iring])
      new.set("VALUE", feature.get(fields[iring]))
      rotation = ((from_deg + to_deg) / 2)-90
      if -90 < rotation < -240:
        rotation+=180
      new.set("ROTATION", rotation)
      new.set("NUMSECTOR", i)
      new.set("NUMRING", iring)
      new.set("GEOMETRY", ring)
      ringStore.insert(new)
      if iring==0:
        featureGeometryCentroid  = getInsidePoint(feature.getDefaultGeometry(), ring)
        centroidRing = getRingCentroid(ring,centroid, radius,radius_interval, from_deg, to_deg, 4)
        line = createLine(D2, [centroidRing,featureGeometryCentroid])
        newFeatureLine = lineShape.getFeatureStore().createNewFeature(featureIdValues)
        newFeatureLine.set("GEOMETRY", line)
        lineShape.getFeatureStore().insert(newFeatureLine)
        
      if labelIdSector==True:
        pointLocation = getRingCentroid(ring,centroid, rout,radius_interval, from_deg, to_deg, 2)
        newFeaturePoint = pointStore.createNewFeature()
        newFeaturePoint.set("LABEL", fields[iring])
        newFeaturePoint.set("VALUE", feature.get(fields[iring]))
        newFeaturePoint.set("STRVALUE", str(feature.get(fields[iring])))
        newFeaturePoint.set("ROTATION", rotation)
        newFeaturePoint.set("NUMSECTOR", i)
        newFeaturePoint.set("NUMRING", iring)
        newFeaturePoint.set("GEOMETRY", pointLocation)
        pointStore.insert(newFeaturePoint)
        
    if createSectorLabel==True:# iLabel==True and 
        pointLocation = getRingCentroid(ring,centroid, rout+radius_interval,radius_interval, from_deg, to_deg, 5)
        newFeaturePoint = pointStore.createNewFeature()
        newFeaturePoint.set("LABEL", feature.get(idTable))
        newFeaturePoint.set("VALUE", 0)
        newFeaturePoint.set("STRVALUE", str(feature.get(idTable)))
        newFeaturePoint.set("ROTATION", ((from_deg + to_deg) / 2)-90)
        newFeaturePoint.set("NUMSECTOR", i)
        newFeaturePoint.set("NUMRING", len(fields)+1)
        newFeaturePoint.set("GEOMETRY", pointLocation)
        pointStore.insert(newFeaturePoint)
        
    if labelOnlyFirstSector:
      labelIdSector = False
    idx_side +=1
    
    
  lineShape.commit()
  pointShape.commit()
  ringShape.commit()
  pointShape.setName("PointLabel")
  lineShape.setName("LineRing")
  ringShape.setName("RingMap")

  try:
    vil = VectorialIntervalLegend(POLYGON)
    vil.setStartColor(Color.white)
    vil.setEndColor(Color.red)
    vil.setIntervalType(1)
    ii = vil.calculateIntervals(ringShape.getFeatureStore(), "VALUE", 8, POLYGON)
    
    vil.setIntervals(ii)
    vil.setClassifyingFieldTypes([7])
    ringShape.setLegend(vil)
  except:
    pass
  gvsig.currentView().addLayer(ringShape)

  leg = SingleSymbolLegend()
  leg.setShapeType(LINE)
  manager = leg.getSymbolManager()
  newline = manager.createSymbol(LINE)
  newline.setColor(Color.black)
  leg.setDefaultSymbol(newline)
  lineShape.setLegend(leg)
  gvsig.currentView().addLayer(lineShape)
  
  leg = SingleSymbolLegend()
  leg.setShapeType(POINT)
  manager = leg.getSymbolManager()
  pointSymbol = manager.createSymbol(POINT)
  pointSymbol.setColor(Color.black)
  leg.setDefaultSymbol(pointSymbol)
  pointSymbol.setSize(0)
  pointShape.setLegend(leg)

  ds = LabelingFactory().createDefaultStrategy(pointShape)
  ds.setTextField("LABEL")
  ds.setRotationField("ROTATION")
  ds.setFixedSize(20)
  pointShape.setLabelingStrategy(ds)
  pointShape.setIsLabeled(True)
  gvsig.currentView().addLayer(pointShape)

def main(*args):
  # Inputs
  idStore = "refman"
  idTable = "refman"
  fields = ["pob_0_14", "pob_15_65", "pob_66_mas"]
  #fields = ["Campo1", "Campo2"] #, "Campo3"]
  #fields = ["Campo1"]
  #layerName = "ejemplo_puntos"
  layerName = "pob_5fs"
  #layerName = "fewlines"
  store = gvsig.currentView().getLayer(layerName).getFeatureStore()
  table = gvsig.currentView().getLayer(layerName).getFeatureStore()
  #store = gvsig.currentLayer().getFeatureStore()
  #table = gvsig.currentLayer().getFeatureStore()
  default_segs = 15
  gaps = 1
  half_step = 90
  internalRadius = 0
  radiusInterval = 0
  centerTopSector = True
  iLabel = True
  labelOnlyFirstSector = False
  createSectorLabel = True
  createRingMap(store, table, idStore, idTable, fields, default_segs, gaps, half_step, internalRadius, radiusInterval, centerTopSector,iLabel, labelOnlyFirstSector, createSectorLabel)







  