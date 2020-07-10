# -*- coding: utf-8 -*-
"""
Created on Tue May 12 10:52:34 2020

@author: 张径舟
路径：D:\Python\Lib\shp.py
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
            

        
'''
def __transform(self, geom, transform):
    target_srs = None
    src_srs = _temp_row[geom_index].GetSpatialReference()
    if type(target_spatial_reference) is int:
        epsg = target_spatial_reference
        target_srs = osr.SpatialReference()
        target_srs.ImportFromEPSG(epsg)
    elif type(target_spatial_reference) is str:
        epsg = None
        if target_spatial_reference.isdigit():
            epsg = int(target_spatial_reference)
        target_srs = osr.SpatialReference()
        if epsg:
            target_srs.ImportFromEPSG(epsg)
    elif type(target_spatial_reference) == type(osr.SpatialReference()):
        target_srs = target_spatial_reference
    
    if target_srs != src_srs:
        ct = osr.CoordinateTransformation(src_srs, target_srs)
    else:
        ct = None
'''   
        
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

#gdal.SetConfigOption('SHAPE_ENCODING', 'GBK')
#'C:\Users\DELL\Desktop\银川.shp'
#'D:\all_cities\OSM路网_投影\南京.shp'
if __name__ == '__main__':
    '''
    reader1 = shp_reader('C:\\Users\\DELL\\Desktop\\test\\000.shp')
    rows1 = list(reader1.readrows())
    '''
    '''
    reader = shp_reader('D:\\黄土\\result1_Update.shp')
    head = reader.readhead()
    srs = reader.readSRS()
    rows = reader.readrows()
    new_rows = []
    yuan = ogr.Geometry(ogr.wkbMultiPolygon)
    yuan.AssignSpatialReference(srs)
    for row in rows:
        if row[27] == 0:
            geom = row[-1]
            yuan.AddGeometry(geom)
    new_rows.append([yuan])
    print(yuan.Area())
    #writer = shp_writer('C:\\Users\\DELL\\Desktop\\test\\only_yuan_multipoly.shp')
    #writer.writerows(head, new_rows)
    '''
    '''
    reader = shp_reader('D:\\黄土\\result1_Update.shp')
    head = reader.readhead()
    srs = reader.readSRS()
    rows = reader.readrows()
    new_rows = []
    for row in rows:
        if row[27] == 0:
            new_rows.append(row)  
    writer = shp_writer('C:\\Users\\DELL\\Desktop\\test\\only_yuan.shp')
    writer.writerows(head, new_rows)
    '''
    
    '''
    reader = shp_reader('C:\\Users\\DELL\\Desktop\\test\\001.shp')
    rows = reader.readrows()
    a = 0
    for row in rows:
        geom = row[-1]
        a += geom.Area()
        area = row[-2]
        print(area, geom.Area())
    print(a)
    '''
    '''
    r = shp_reader('C:\\Users\\DELL\\Desktop\\test\\yuan.shp')
    w = shp_writer('C:\\Users\\DELL\\Desktop\\test\\yuan1.shp')
    h = r.readhead()
    nr = []
    h['area_ogr'] = ogr.OFTReal
    for row in r.readrows():
        geom = row[-1]
        area = geom.Area()
        new_row = row
        new_row.insert(-1, area)
        nr.append(new_row)
    w.writerows(h, nr)    
    '''
    """
    r = shp_reader('C:\\Users\\DELL\\Desktop\\test\\yuan.shp')
    w = shp_writer('C:\\Users\\DELL\\Desktop\\test\\yuan_dis_ogr.shp')
    srs = r.readSRS()
    yuan = ogr.Geometry(ogr.wkbMultiPolygon)
    yuan.AssignSpatialReference(srs)
    for row in r.readrows():
        geom = row[-1]
        yuan.AddGeometryDirectly(geom)
    h = []
    nr = [[yuan]]
    #w.writerows(h, nr)
    r1 = shp_reader('C:\\Users\\DELL\\Desktop\\test\\yuan_dis_ogr.shp')    
    for row in r1.readrows():
        yuan1 = row[-1]
    a = []
    for i in range(yuan.GetGeometryCount()):
        a.append(yuan.GetGeometryRef(i).Area())
    a1 = []
    for i in range(yuan1.GetGeometryCount()):
        a1.append(yuan1.GetGeometryRef(i).Area())
    print(len(a1))
    """
    '''
    yuan_wkt = yuan.ExportToIsoWkt()
    yuan1_wkt = yuan1.ExportToIsoWkt()
    with open('C:\\Users\\DELL\\Desktop\\test\\111.txt', 'w') as file:
        file.write(yuan_wkt)
        file.write('\n')
        file.write(yuan1_wkt)  
    '''
    #print(yuan.GetGeometryRef(2).Equals(yuan1.GetGeometryRef(2)))
    #print(yuan.GetGeometryRef(200))
    #print(yuan1.GetGeometryRef(200))
    '''
    r1 = shp_reader('C:\\Users\\DELL\\Desktop\\test\\only_yuan_multipoly.shp')
    r2 = shp_reader('C:\\Users\\DELL\\Desktop\\test\\only_yuan.shp')
    r3 = shp_reader('C:\\Users\\DELL\\Desktop\\test\\only_yuan_dissolve.shp')
    w1 = shp_writer('C:\\Users\\DELL\\Desktop\\test\\only_yuan_multipoly1.shp')
    w2 = shp_writer('C:\\Users\\DELL\\Desktop\\test\\only_yuan1.shp')
    w3 = shp_writer('C:\\Users\\DELL\\Desktop\\test\\only_yuan_dissolve1.shp')
    h1 = r1.readhead()
    h1['area_ogr'] = ogr.OFTReal
    h2 = r2.readhead()
    h2['area_ogr'] = ogr.OFTReal
    h3 = r3.readhead()
    h3['area_ogr'] = ogr.OFTReal
    nr1 = []
    nr2 = []
    nr3 = []
    
    for row in r1.readrows():
        geom = row[-1]
        area = geom.Area()
        new_row = row
        new_row.insert(-1, area)
        nr1.append(new_row)
    w1.writerows(h1, nr1)
    
    for row in r2.readrows():
        geom = row[-1]
        area = geom.Area()
        new_row = row
        new_row.insert(-1, area)
        nr2.append(new_row)
    w2.writerows(h2, nr2)
    
    for row in r3.readrows():
        geom = row[-1]
        area = geom.Area()
        new_row = row
        new_row.insert(-1, area)
        nr3.append(new_row)
    w3.writerows(h3, nr3)
    '''

        
        
    
        