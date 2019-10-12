from osgeo import ogr
from osgeo import gdal
from make_start_points import *
from compute_walkscore_1 import *
from networkx_readshp import *
import os
import time


class WalkscoreCalculator:

    def __init__(self, poi_types, weight_tables):
        self.road_linedata = ''
        self.poi_pointdata = {}
        self.poi_types = poi_types
        self.weight_tables = weight_tables
        self.MultiType_poi_points_geo = {}

        '''防止编码出现问题'''
        gdal.SetConfigOption('GDAL_FILENAME_IS_UTF8', 'YES')
        gdal.SetConfigOption('SHAPE_ENCODING', 'GBK')
        
    '''设置道路数据的路径'''    
    def Set_Road_Linedata(self, filename:str):
        self.road_linedata = filename
        if os.path.exists(self.road_linedata):
            print('道路数据路径设置完毕...')
            return True
        else:
            print('道路数据路径设置失败...')
            return False
        
    '''设置POI数据的路径'''
    def Set_POI_Pointdata(self, filepath:str):
        for poi_type in self.poi_types:
            self.poi_pointdata[poi_type] = filepath + poi_type + '\\' + poi_type + '_cgcs2000.shp'   
            if not os.path.exists(self.poi_pointdata[poi_type]):
                print('POI数据路径设置失败...')
                return False
        print('POI数据路径设置成功...\n')
        return True
    
    '''准备POI数据'''
    def Prepare_POIinfo(self):
        MultiType_poi_points_geo = {}
        for poi_type, path in self.poi_pointdata.items():  
            print('\n当前处理 %s 类POI...' % poi_type)
            
            '''读取shapfile'''
            dr = ogr.GetDriverByName('ESRI Shapefile')
            if dr is None:
                print('注册 %s 的驱动失败...' % poi_type)
                return False
            print('注册 %s 的驱动成功...' % poi_type)
            ds = dr.Open(path, 0)
            if ds is None:
                print('打开 %s 的shp文件失败...' % poi_type)
                return False
            print('打开 %s 的shp文件成功...' % poi_type)
            '''读取图层'''
            layer = ds.GetLayerByIndex(0)
            if layer is None:
                print('获取 %s 的图层失败...' % poi_type)
                return False
            print('获取 %s 的图层成功...' % poi_type)  
            layer.ResetReading()
        
            SingleType_poi_points_geo = ogr.Geometry(ogr.wkbMultiPoint)
            temp_poi = layer.GetNextFeature()
            while temp_poi:
                temp_geo = temp_poi.GetGeometryRef().Clone()
                SingleType_poi_points_geo.AddGeometry(temp_geo)
                temp_poi = layer.GetNextFeature()
            MultiType_poi_points_geo[poi_type] = SingleType_poi_points_geo
        self.MultiType_poi_points_geo = MultiType_poi_points_geo
        print('\n所有POI的数据准备完成...')
        return True
    
    def Compute_Road_Walkscore(self, seg_length):
        '''准备道路的数据以及计算步行指数'''
        Multi_roads_geos = read_shp_to_geo(self.road_linedata)
        G = read_shp_to_graph(self.road_linedata, simplify=False).to_undirected()
        
        temp_point_id = 0        
        '''读取shp文件'''
        dr = ogr.GetDriverByName('ESRI Shapefile')
        if dr is None:
            print('注册道路的驱动失败...')
            return False
        print('注册道路的驱动成功...')
        ds = dr.Open(self.road_linedata, 1)
        if ds is None:
            print('打开道路的shp文件失败...')
            return False
        print('打开道路的shp文件成功...')
        '''读取图层'''
        layer = ds.GetLayerByIndex(0)
        if layer is None:
            print('获取道路的图层失败...')
            return False
        print('获取道路的图层成功...') 
        flag = int(input("是否写入？1为写入，其他字符为不写入\n"))
        
        '''准备写入，只有flag == 1的时候才写入'''
        if flag == 1:   
            print('写入\n')
            oFieldID = ogr.FieldDefn("walkscore", ogr.OFTReal)
            layer.CreateField(oFieldID, 1)
            for poi_type in self.poi_types:
                if poi_type == 'grocery_stores':
                    poi_type = 'grocery'
                elif poi_type == 'restaurants_and_bars':
                    poi_type = 'r_b'
                oFieldID = ogr.FieldDefn(poi_type, ogr.OFTReal)
                layer.CreateField(oFieldID, 1)
        else:
            print('不写入\n')
        print('\n开始计算步行指数')

        i = 0
        
        start = time.time()        
        layer.ResetReading()   
        temp_road = layer.GetNextFeature()
        while temp_road:
            start_time = time.time()            
            temp_road_geo = temp_road.GetGeometryRef().Clone() 
            temp_name = temp_road.GetFieldAsString('name')
            temp_id = temp_road.GetFieldAsString('id')
            if temp_name == '':
                temp_name = 'Road No.'+str(temp_id) 
            i += 1
            print('第%d条：id为%s' % (i, temp_id))     
            '''
            #下面三行是测试时用的
            if temp_id != '55':     
                temp_road = layer.GetNextFeature()
                continue
            '''
            start_points = []
            Make_Start_Points_Road(temp_road_geo, start_points, seg_length, temp_id) #每隔seg_length创建一个出发点
            G_copy = G.copy()
            ws = Compute_Walkscore_Road(start_points, 
                                        self.weight_tables, 
                                        self.MultiType_poi_points_geo, 
                                        temp_road_geo, 
                                        Multi_roads_geos,
                                        G_copy)   
            walkscore = ws#['main']
            print('步行指数为 %f   ' % walkscore, end='')            
            end_time = time.time()             
            print('步行指数计算%f秒，共%f秒' % ((end_time-start_time), (end_time-start)))
            
            '''写入，只有flag=1的时候才写入'''
            if flag == 1:           
                temp_road.SetField("walkscore", walkscore)
                for poi_type in self.poi_types:
                    temp_ws = ws[poi_type]
                    if poi_type == 'grocery_stores':
                        poi_type = 'grocery'
                    elif poi_type == 'restaurants_and_bars':
                        poi_type = 'r_b'
                    temp_road.SetField(poi_type, temp_ws)
                layer.SetFeature(temp_road)        
            
            temp_road = layer.GetNextFeature()
#            break
        return True

    '''下面这是计算面域步行指数的，暂时没用'''         
    def Compute_Region_Walkscore(self, first_point_coord, last_point_coord, density, filepath):
        start_points_info = Make_Start_Points_Region(first_point_coord, last_point_coord, density)
        Compute_Walkscore_Region(start_points_info, self.weight_tables, self.MultiType_poi_points_geo)
        dr = ogr.GetDriverByName('ESRI Shapefile')
        if dr is None:
            return False
        ds = dr.CreateDataSource(filepath)
        if ds is None:
            return False
        layer = ds.CreateLayer('Points', None, ogr.wkbPoint)
    
        FieldID = ogr.FieldDefn('ID', ogr.OFTInteger)
        layer.CreateField(FieldID, 1)
    
        FieldWalkscore = ogr.FieldDefn('Walkscore', ogr.OFTReal)
        layer.CreateField(FieldWalkscore, 1)
    
        oDefn = layer.GetLayerDefn()
        print('开始写入面域步行指数')
        for start_point_info in start_points_info:
            start_point_feature = ogr.Feature(oDefn)
            start_point_feature.SetField(0, start_point_info.point_id)
            start_point_feature.SetField(1, start_point_info.walkscore)
            start_point_feature.SetGeometry(start_point_info.point_geo)
            layer.CreateFeature(start_point_feature)
        ds.Destroy()
        return True
              
            