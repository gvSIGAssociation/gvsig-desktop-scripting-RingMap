# encoding: utf-8

import gvsig
from org.gvsig.symbology.fmap.mapcontext.rendering.legend.styling import LabelingFactory
def main(*args):

  layer = gvsig.currentLayer()
  ls = layer.getLabelingStrategy()
  print ls
  print ls.getFont()
  print ls.getTextField()
  print ls.getRotationField()
  ds = LabelingFactory().createDefaultStrategy(layer)
  print ds
  ds.setTextField("LABEL")
  ds.setRotationField("ROTATION")