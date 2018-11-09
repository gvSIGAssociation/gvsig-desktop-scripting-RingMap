# encoding: utf-8

import gvsig
import pdb
from gvsig import geom
from gvsig import commonsdialog
from gvsig.libs.toolbox import ToolboxProcess, NUMERICAL_VALUE_DOUBLE,SHAPE_TYPE_POLYGON,NUMERICAL_VALUE_INTEGER,SHAPE_TYPE_POLYGON, SHAPE_TYPE_POINT
from es.unex.sextante.gui import core
from es.unex.sextante.gui.core import NameAndIcon

from es.unex.sextante.gui.core import SextanteGUI
from org.gvsig.geoprocess.lib.api import GeoProcessLocator
from addons.RingMap.ringCreation import createRingMap
from org.gvsig.andami import PluginsLocator
import os
from java.io import File
from org.gvsig.tools import ToolsLocator

class RingMapGeoprocess(ToolboxProcess):
  def getHelpFile(self):
    name = "ringmap"
    extension = ".xml"
    locale = PluginsLocator.getLocaleManager().getCurrentLocale()
    tag = locale.getLanguage()
    #extension = ".properties"

    helpPath = gvsig.getResource(__file__, "help", name + "_" + tag + extension)
    if os.path.exists(helpPath):
        return File(helpPath)
    #Alternatives
    alternatives = PluginsLocator.getLocaleManager().getLocaleAlternatives(locale)
    for alt in alternatives:
        helpPath = gvsig.getResource(__file__, "help", name + "_" + alt.toLanguageTag() + extension )
        if os.path.exists(helpPath):
            return File(helpPath)
    # More Alternatives
    helpPath = gvsig.getResource(__file__, "help", name + extension)
    if os.path.exists(helpPath):
        return File(helpPath)
    return None
  def defineCharacteristics(self):
      i18nManager = ToolsLocator.getI18nManager()
      self.setName(i18nManager.getTranslation("_Ring_map"))
      self.setGroup(i18nManager.getTranslation("_Criminology_group"))
      self.setUserCanDefineAnalysisExtent(False)
      params = self.getParameters()
      
      params.addInputVectorLayer("LAYER",i18nManager.getTranslation("_Input_layer"), SHAPE_TYPE_POLYGON, True)
      params.addTableField("FLAYER", i18nManager.getTranslation("_Field_table"), "LAYER", True)
      params.addInputTable("TABLE", i18nManager.getTranslation("_Table_data"), True)
      params.addTableField("FTABLE", i18nManager.getTranslation("_Field_table"), "TABLE", True)
      params.addString("FIELDS", i18nManager.getTranslation("_Fields_separated_by_comma"))
      
      params.addNumericalValue("DEFAULTSEGS", i18nManager.getTranslation("_Number_of_segments"),10, NUMERICAL_VALUE_INTEGER)
      params.addNumericalValue("GAPS", i18nManager.getTranslation("_Gaps_between_sectors"),0, NUMERICAL_VALUE_INTEGER)
      params.addNumericalValue("HALFSTEP", i18nManager.getTranslation("_Half_step"),90, NUMERICAL_VALUE_DOUBLE)
      params.addNumericalValue("INTERNALRADIUS", i18nManager.getTranslation("_Internal_radius"),0, NUMERICAL_VALUE_DOUBLE)
      params.addNumericalValue("RADIUSINTERVAL", i18nManager.getTranslation("_Radius_interval"),0, NUMERICAL_VALUE_DOUBLE)
      params.addBoolean("CENTERTOPSECTOR", i18nManager.getTranslation("_Center_top_sector"),True)
      params.addBoolean("LABELIDSECTOR", i18nManager.getTranslation("_Label_id_sector"),True)
      params.addBoolean("LABELONLYFIRSTSECTOR", i18nManager.getTranslation("_Label_only_first_sector"),True)
      params.addBoolean("CREATESECTORLABEL", i18nManager.getTranslation("_Create_Sector_Label"),True)

  def processAlgorithm(self):
    features=None
    params = self.getParameters()

    store = params.getParameterValueAsVectorLayer("LAYER").getFeatureStore()
    positionIdStore = params.getParameterValueAsInt("FLAYER")
    idStore = store.getDefaultFeatureType().getAttributeDescriptor(positionIdStore).getName()
    table = params.getParameterValueAsTable("TABLE").getFeatureStore()
    positionIdTable = params.getParameterValueAsInt("FTABLE")
    idTable = table.getDefaultFeatureType().getAttributeDescriptor(positionIdTable).getName()
    stringFields = params.getParameterValueAsString("FIELDS")
    fields = [x.strip() for x in stringFields.split(',')]
    default_segs = params.getParameterValueAsInt("DEFAULTSEGS")
    gaps = params.getParameterValueAsInt("GAPS")
    half_step = params.getParameterValueAsDouble("HALFSTEP")
    internalRadius = params.getParameterValueAsDouble("INTERNALRADIUS")
    radiusInterval = params.getParameterValueAsDouble("RADIUSINTERVAL")
    centerTopSector = params.getParameterValueAsBoolean("CENTERTOPSECTOR")
    labelOnlyFirstSector = params.getParameterValueAsBoolean("LABELONLYFIRSTSECTOR")
    labelIdSector = params.getParameterValueAsBoolean("LABELIDSECTOR")
    createSectorLabel = params.getParameterValueAsBoolean("CREATESECTORLABEL")
    createRingMap(store, table, idStore, idTable, fields, default_segs, gaps, half_step, internalRadius, radiusInterval, centerTopSector, labelOnlyFirstSector, labelIdSector, createSectorLabel)

    return True
        
def main(*args):
        process = RingMapGeoprocess()
        process.selfregister("Scripting")
        process.updateToolbox()

