# -*- coding: utf-8 -*-
"""
Created on Tue May 12 10:52:34 2020

@author: 张径舟
shp文件的读写比较麻烦，所以自己写了一个读写shp文件的模块，模仿csv模块
"""
import ogr
import gdal
import os


gdal.SetConfigOption('SHAPE_ENCODING', 'UTF-8')
class shp_writer():
    
    def __init__(self, filename):
        self._filename = filename        
        self.dr = ogr.GetDriverByName('ESRI Shapefile')
        if os.path.exists(self._filename) and os.path.getsize(self._filename) == 100:
            basename = os.path.basename(self._filename)
            temp_dir = os.path.dirname(self._filename)
            for file in os.listdir(temp_dir):
                if os.path.splitext(file)[0] == os.path.splitext(basename)[0]:
                    os.remove(temp_dir + '\\' + file)
        if not os.path.exists(self._filename):
            self.ds = self.dr.CreateDataSource(self._filename)   
        else:
            self.ds = self.dr.Open(self._filename, 0)    
        self.layer = None
        self._lDefn = None
            
    def writerows(self, head, rows):
        _temp_row = rows[0]
        for row in rows:
            if all(row):
                _temp_row = row
                break
        srs = _temp_row[-1].GetSpatialReference()
        _geo_type = _temp_row[-1].GetGeometryType()
        layer = self.ds.CreateLayer("layer", srs, _geo_type)
        if head is None:
            _fDefn = ogr.FieldDefn('name', ogr.OFTString)
            layer.CreateField(_fDefn)
        elif type(head) is list:
            for i in range(len(head)):
                if type(_temp_row[i]) is int:
                    _OFT = ogr.OFTInteger
                elif type(_temp_row[i]) is float:
                    _OFT = ogr.OFTReal
                elif type(_temp_row[i]) is str:
                    _OFT = ogr.OFTString
                else:
                    _OFT = ogr.OFTString
                _field_name = head[i]
                _fDefn = ogr.FieldDefn(_field_name, _OFT)
                layer.CreateField(_fDefn)
        elif type(head) is dict:
            for _field_name, _OFT in head.items():
                _fDefn = ogr.FieldDefn(_field_name, _OFT)
                layer.CreateField(_fDefn)
        else:
            raise Exception("head must be a dict or a list")                
            
        _lDefn = layer.GetLayerDefn()
        for row in rows:
            _feature = ogr.Feature(_lDefn)
            fields = row[:-1]
            for i in range(len(fields)):
                if fields[i] is not None:
                    _feature.SetField(i, fields[i])
                else:
                    _feature.SetFieldNull(i)
            _feature.SetGeometry(row[-1])
            layer.CreateFeature(_feature)
            self.ds.SyncToDisk()
    
    def createlayer(self, srs, geo_type):
        layer = self.ds.CreateLayer('layer', srs, geo_type)
        self.layer = layer
            
    def writehead(self, head):
        if self.layer is None:
            raise Exception('Layer is None. Try writer.createlayer() ?')
        for _field_name, _OFT in head.items():
            _fDefn = ogr.FieldDefn(_field_name, _OFT)
            self.layer.CreateField(_fDefn)             
            
    def appendrows(self, rows):
        if self.layer is None:
            raise Exception('Layer is None. Try writer.createlayer() ?')
        if self._lDefn is None:
            self._lDefn = self.layer.GetLayerDefn()
        for row in rows:
            feature = ogr.Feature(self._lDefn)
            for i in range(len(row)-1):
                if row[i] is not None:
                    feature.SetField(i, row[i])
                else:
                    feature.SetFieldNull(i)
            feature.SetGeometry(row[-1])
            self.layer.CreateFeature(feature) 
            self.ds.SyncToDisk()
        
class shp_reader():
    
    def __init__(self, filename):
        self._filename = filename
        self.dr = ogr.GetDriverByName('ESRI Shapefile')
        self.ds, self.layer = self.__read()
        self._method_dict = {ogr.OFTBinary: 'feature.GetFieldAsBinary(i)', 
                              ogr.OFTDate: 'feature.GetFieldAsDateTime(i)',
                              ogr.OFTInteger: 'feature.GetFieldAsInteger(i)',                
                              ogr.OFTInteger64: 'feature.GetFieldAsInteger64(i)',              
                              ogr.OFTInteger64List: 'feature.GetFieldAsInteger64List(i)',
                              ogr.OFTIntegerList: 'feature.GetFieldAsIntegerList(i)',       
                              ogr.OFTReal: 'feature.GetFieldAsDouble(i)',
                              ogr.OFTRealList: 'feature.GetFieldAsDoubleList(i)',
                              ogr.OFTString: 'feature.GetFieldAsString(i)',
                              ogr.OFTStringList: 'feature.GetFieldAsStringList(i)'}
        
    def readSRS(self):
        layer = self.layer
        srs = layer.GetSpatialRef()
        return srs
        
    def readhead(self, head_type=dict):
        layer = self.layer
        head = {}
        feature = layer.GetNextFeature()
        FIELD_COUNT = feature.GetFieldCount()
        for i in range(FIELD_COUNT):
            fDefn = feature.GetFieldDefnRef(i)
            head[fDefn.GetName()] = fDefn.GetType()
        if head_type is list: 
            return list(head.keys())
        return head
    
    def readrows(self, generator=True):
        if generator:
            return self.__readrows()
        else:
            rows = []
            for row in self.__readrows():
                rows.append(row)
            return rows
        
    def close_datasource(self):
        self.ds.Destroy()

    def __readrows(self):
        layer = self.layer
        layer.ResetReading()
        feature = layer.GetNextFeature()
        FIELD_COUNT = feature.GetFieldCount()
        while feature:
            row = []
            row.extend(self.__getFields(feature, FIELD_COUNT))
            geomRef = feature.GetGeometryRef()
            if geomRef:
                geom = geomRef.Clone()
            else:
                geom = None
            row.append(geom)
            yield row
            feature = layer.GetNextFeature()
    
        
    def __read(self):
        if os.path.exists(self._filename): 
            ds = self.dr.Open(self._filename, 0)
        else:
            raise FileNotFoundError("[Errno 2] No such file or directory: '%s'" % (self._filename))
        layer = ds.GetLayerByIndex(0)
        layer.ResetReading()
        return ds, layer 
    
    def __getFields(self, feature, field_count):
        fields = []
        for i in range(field_count):
            isNull = feature.IsFieldNull(i)
            fDefn = feature.GetFieldDefnRef(i)
            method = self._method_dict.get(fDefn.GetType()) 
            if isNull:
                fields.append(None)
            elif method is not None:
                fields.append(eval(method))
            else:
                fields.append('')
        return fields
        
        
    
        
