# encoding: utf-8

import gvsig
from gvsig.geom import *
import math
from java.awt import Color
from org.gvsig.symbology.fmap.mapcontext.rendering.legend.impl import VectorialIntervalLegend, SingleSymbolLegend

# math.radians(x)
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
def create_ring_cell(centroid, from_deg, to_deg, from_radius, to_radius, default_segs, gaps):
  step = abs(to_deg - from_deg) / default_segs
  radian = 0.0
  outer_ring = []
  # first interior
  first = True
  
  for index in xrange(default_segs+1-gaps):
    radian = to_radian(from_deg - (index * step))
    outer_ring.append(create_point(centroid, radian, from_radius))
    if first==True:
      point1 = create_point(centroid, radian, from_radius)
      first = False
  
  # second outer
  for index in xrange(default_segs-gaps,-1,-1):
    radian = to_radian(from_deg-(index * step))
    outer_ring.append(create_point(centroid, radian, to_radius))

  outer_ring.append(point1)
  polygon = createPolygon(D2, [outer_ring])
  g = createGeometry(POLYGON, D2)
  for i in outer_ring:
    g.addVertex(i)
  return g
    
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

def getRingCentroid(ring, centroid, r, rk,from_deg, to_deg, default_segs, gaps):
  d = (from_deg + (default_segs * gaps) + to_deg)/2
  radius = r + (rk/4)
  radian = to_radian(d)
  point = create_point(centroid, radian, radius)
  return point


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
        centerTopSector):
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
    
  # Prepare envelope
  envelope = envelopeSelection #store.getEnvelope()
  centroid = envelope.getGeometry().centroid()
  if internalRadius > 0:
    radius = internalRadius
  else: 
    minx = envelope.getLowerCorner().getX()
    miny = envelope.getLowerCorner().getY()
    maxx = envelope.getUpperCorner().getX()
    maxy = envelope.getUpperCorner().getY()
    radius = (((maxx - minx)**2 + (maxy - miny)**2) **0.5) / 2.0
  if radiusInterval > 0:
      radius_interval = radiusInterval
  else:
      radius_interval = radius / ring_num

  # Prepare schema
  newSchema = gvsig.createFeatureType() #table.getDefaultFeatureType())
  #rm = newSchema.getEditableAttributeDescriptor("GEOMETRY")
  #if rm!=None:
  #  newSchema.remove(rm)
  #newSchema.append("GEOMETRY", "GEOMETRY")
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
  
  # Vars
  ringStore = ringShape.getFeatureStore()
  ringShape.edit()
  iLabel = True
  step_angle = 360.0 / feature_count

  if centerTopSector:
    half_step = half_step + (step_angle/2)-((default_segs*gaps)/2)
  #step_angle / 2.0
  idx_side = 0
  for i in xrange(0, feature_count):
    from_deg = half_step - (idx_side * step_angle)
    to_deg = half_step - ((idx_side + 1) * step_angle)
    to_deg = to_deg - (default_segs* gaps)
    print from_deg, to_deg
    # Get closest
    rin = radius+(radius_interval*(1))
    rout = radius
    prering = create_ring_cell(centroid, from_deg, to_deg, rin, rout, default_segs, gaps).centroid()
    feature = getClosest(featureList, prering)
    if iLabel == True:
        pass
    for iring in xrange(0, len(fields)):
      featureIdValues = table.findFirst(idTable+"="+feature.get(idStore))
      new = ringStore.createNewFeature()
      rin = radius+(radius_interval*(iring+1))
      rout = radius+(radius_interval*iring)
      ring = create_ring_cell(centroid, from_deg, to_deg, rin, rout,  default_segs, gaps)
      new.set("LABEL", fields[iring])
      new.set("VALUE", feature.get(fields[iring]))
      new.set("ROTATION", ((from_deg + to_deg) / 2)-90)
      new.set("NUMSECTOR", i)
      new.set("NUMRING", iring)
      new.set("GEOMETRY", ring)
      ringStore.insert(new)
      if iring==0:
          featureGeometryCentroid  = getInsidePoint(feature.getDefaultGeometry(), ring)
          centroidRing = getRingCentroid(ring,centroid, radius,radius_interval, from_deg, to_deg,default_segs, gaps)
          line = createLine(D2, [centroidRing,centroid]) #featureGeometryCentroid])
          newFeatureLine = lineShape.getFeatureStore().createNewFeature(featureIdValues)
          newFeatureLine.set("GEOMETRY", line)
          lineShape.getFeatureStore().insert(newFeatureLine)
    iLabel = False
    idx_side +=1
    
    
  lineShape.commit()
  ringShape.commit()
  lineShape.setName("LineRing")
  ringShape.setName("RingMap")


  vil = VectorialIntervalLegend(POLYGON)
  vil.setStartColor(Color.red)
  vil.setEndColor(Color.blue)
  vil.setIntervalType(1)
  ii = vil.calculateIntervals(ringShape.getFeatureStore(), "VALUE", 5, POLYGON)
  vil.setIntervals(ii)
  ringShape.setLegend(vil)
  gvsig.currentView().addLayer(ringShape)


  leg = SingleSymbolLegend()
  leg.setShapeType(LINE)
  manager = leg.getSymbolManager()
  newline = manager.createSymbol(LINE)
  newline.setColor(Color.black)
  leg.setDefaultSymbol(newline)
  lineShape.setLegend(leg)
  gvsig.currentView().addLayer(lineShape)

def main(*args):
  # Inputs
  idStore = "refman"
  idTable = "refman"
  fields = ["pob_0_14", "pob_15_65", "pob_66_mas"]
  layerName = "pob_5fs"
  store = gvsig.currentView().getLayer(layerName).getFeatureStore()
  table = gvsig.currentView().getLayer(layerName).getFeatureStore()
  #store = gvsig.currentLayer().getFeatureStore()
  #table = gvsig.currentLayer().getFeatureStore()
  default_segs = 15
  gaps = 3
  half_step = 90
  internalRadius = 0
  radiusInterval = 8
  centerTopSector = True
  createRingMap(store, table, idStore, idTable, fields, default_segs, gaps, half_step, internalRadius, radiusInterval, centerTopSector)

"""

def main(*args):
  # Inputs
  idStore = "refman"
  idTable = "refman"
  fields = ["pob_0_14", "pob_15_65", "pob_66_mas"]
  layerName = "pob_5fs"
  store = gvsig.currentView().getLayer(layerName).getFeatureStore()
  table = gvsig.currentView().getLayer(layerName).getFeatureStore()

  # Pre vars
  ring_num = len(fields) # number fileds
  
  # Prepare envelope
  envelope = store.getEnvelope()
  centroid = envelope.getGeometry().centroid()
  minx = envelope.getLowerCorner().getX()
  miny = envelope.getLowerCorner().getY()
  maxx = envelope.getUpperCorner().getX()
  maxy = envelope.getUpperCorner().getY()
  radius = (((maxx - minx)**2 + (maxy - miny)**2) **0.5) / 2.0
  radius_interval = radius / ring_num
  
  # Prepare schema: from the table
  newSchema = gvsig.createFeatureType() #table.getDefaultFeatureType())
  #rm = newSchema.getEditableAttributeDescriptor("GEOMETRY")
  #if rm!=None:
  #  newSchema.remove(rm)
  #newSchema.append("GEOMETRY", "GEOMETRY")
  newSchema.append("LABEL", "STRING", 20)
  newSchema.append("VALUE", "DOUBLE", 20,5)
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
  
  # Vars
  ringStore = ringShape.getFeatureStore()
  ringShape.edit()
  featureSet = store.getFeatureSet()
  feature_count = featureSet.getSize()

  step_angle = 360.0 / feature_count
  half_step = step_angle / 2.0
  idx_side = 0
  for feature in featureSet:
    from_deg = half_step + (idx_side * step_angle)
    to_deg = half_step + ((idx_side + 1) * step_angle)
    for iring in xrange(0, len(fields)):
      featureIdValues = table.findFirst(idTable+"="+feature.get(idStore))
      new = ringStore.createNewFeature() #featureIdValues)
      rin = radius+(radius_interval*(iring+1))
      rout = radius+(radius_interval*iring)
      ring = create_ring_cell(centroid, from_deg, to_deg, rin, rout)
      new.set("LABEL", fields[iring])
      new.set("VALUE", feature.get(fields[iring]))
      new.set("ROTATION", ((from_deg + to_deg) / 2)-90)
      new.set("GEOMETRY", ring)
      ringStore.insert(new)
      if iring==0:
          featureGeometryCentroid  = getInsidePoint(feature.getDefaultGeometry())
          line = createLine(D2, [ring.centroid(),featureGeometryCentroid])
          newFeatureLine = lineShape.getFeatureStore().createNewFeature()
          newFeatureLine.set("GEOMETRY", line)
          lineShape.getFeatureStore().insert(newFeatureLine)
    idx_side +=1
  lineShape.commit()
  ringShape.commit()
  lineShape.setName("LineRing")
  ringShape.setName("RingMap")
  gvsig.currentView().addLayer(ringShape)
  gvsig.currentView().addLayer(lineShape)

  
def main1_createOneRing(*args):
  ring_num = 5 # number fileds
  store = gvsig.currentLayer().getFeatureStore()
  envelope = store.getEnvelope()
  centroid = envelope.getGeometry().centroid()
  minx = envelope.getLowerCorner().getX()
  miny = envelope.getLowerCorner().getY()
  maxx = envelope.getUpperCorner().getX()
  maxy = envelope.getUpperCorner().getY()
  
  radius = (((maxx - minx)**2 + (maxy - miny)**2) **0.5) / 2.0
  radius_interval = radius / ring_num
  print radius, radius_interval
  schema = gvsig.createFeatureType()
  schema.append("GEOMETRY", "GEOMETRY")
  schema.get("GEOMETRY").setGeometryType(POLYGON, D2)
  shape = gvsig.createShape(schema)
  store = shape.getFeatureStore()
  shape.edit()
  new = store.createNewFeature()
  ring = create_ring_cell(centroid, 0, 100, radius+radius_interval, radius)
  #print create_point(ring.centroid(), 0, 2)
  new.set("GEOMETRY", ring)
  store.insert(new)
  shape.commit()
  gvsig.currentView().addLayer(shape)
"""











  