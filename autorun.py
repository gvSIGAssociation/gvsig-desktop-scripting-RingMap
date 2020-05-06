# encoding: utf-8
import gvsig
from gvsig import getResource
from java.io import File
from org.gvsig.tools import ToolsLocator

try:
  from addons.RingMap.ringMapGeoprocess import RingMapGeoprocess
except:
  import sys
  ex = sys.exc_info()[1]
  gvsig.logger("Can't load module 'RingMapGeoprocess'. " + str(ex), gvsig.LOGGER_WARN)#, ex)
  RingMapGeoprocess = None


def i18nRegister():
  i18nManager = ToolsLocator.getI18nManager()
  i18nManager.addResourceFamily("text",File(getResource(__file__,"i18n")))
  
def main(*args):
  if RingMapGeoprocess== None:
    return
  i18nRegister()
  process = RingMapGeoprocess()
  process.selfregister("Scripting")
  process.updateToolbox()
