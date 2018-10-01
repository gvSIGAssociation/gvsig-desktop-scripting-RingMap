# encoding: utf-8
import gvsig
from gvsig import getResource
from java.io import File
from org.gvsig.tools import ToolsLocator
from addons.RingMap.ringMapGeoprocess import RingMapGeoprocess

# Icon made by [author link] from www.flaticon.com

def i18nRegister():
  i18nManager = ToolsLocator.getI18nManager()
  i18nManager.addResourceFamily("text",File(getResource(__file__,"i18n")))
  
def main(*args):
  process = RingMapGeoprocess()
  process.selfregister("Scripting")
  process.updateToolbox()
  i18nRegister()