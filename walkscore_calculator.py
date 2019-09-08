from osgeo import ogr
from osgeo import gdal
from road_info import RoadInfo
from poi_point import Poipoint 
from make_start_points import *
from compute_walkscore import *
import os
import time

class WalkscoreCalculator:
    all_road_info = []
    all_start_point_info = []
    def __init__(self):
#        self.poi_path = 'C:\\Users\\DELL\\Desktop\\first_trial\\'
        self.road_linedata = ''
        self.poi_pointdata = {}
        self.all_road_info.clear()
        self.all_start_point_info.clear()
        self.MultiType_poi_points_geo = {}
        self.weight_tables = {'grocery_stores': [3], 
                          'restaurants_and_bars': [0.75,0.45,0.25,0.25,0.225,0.225,0.225,0.225,0.2,0.2], 
                          'shops': [0.5,0.45,0.4,0.35,0.3], 
                          'cafes': [1.25,0.75], 
                          'banks': [1], 
                          'parks': [1], 
                          'schools': [1], 
                          'bookstores': [1], 
                          'entertain': [1]}   
#后面再加种类     
        self.poi_types = ['grocery_stores', 
                          'restaurants_and_bars', 
                          'shops', 
                          'cafes', 
                          'banks', 
                          'parks', 
                          'schools', 
                          'bookstores', 
                          'entertain']
#后面再加种类 
        '''防止编码出现问题'''
        gdal.SetConfigOption('GDAL_FILENAME_IS_UTF8', 'YES')
        gdal.SetConfigOption('SHAPE_ENCODING', 'GBK')
        
    def Set_Road_Linedata(self, filename:str):
        self.road_linedata = filename
        if os.path.exists(self.road_linedata):
            print('道路数据路径设置完毕...')
            return True
        else:
            print('道路数据路径设置失败...')
            return False
        

    def Set_POI_Pointdata(self, filepath:str):
        for poi_type in self.poi_types:
            self.poi_pointdata[poi_type] = filepath + poi_type + '\\' + poi_type + '_cgcs2000.shp'   
            if not os.path.exists(self.poi_pointdata[poi_type]):
                print('POI数据路径设置失败...')
                return False
        print('POI数据路径设置成功...\n')
        return True
    
    def Prepare_POIinfo(self):
        MultiType_poi_points_geo = {}
        for poi_type, path in self.poi_pointdata.items():  
            print('\n当前处理 %s 类POI...' % poi_type)
            
            '''读取shp文件'''
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
        temp_road_info = []
        temp_point_id = 0        
        #准备路网的数据，temp_road_info是所有道路的数据，temp_roadInfo是一条道路的数据  
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
        layer.ResetReading()   
        flag = input("是否写入？1为写入，其他字符为不写入\n")
        if flag == '1':            
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
            
        temp_road = layer.GetNextFeature()
        print('\n开始计算步行指数，一共有6419条道路')

        i = 0
        counting = 0
        start = time.time()
        while temp_road:
            i += 1
            temp_point_info = []
            temp_geo = temp_road.GetGeometryRef().Clone() 
            temp_name = temp_road.GetFieldAsString('name')
            temp_id = temp_road.GetFieldAsString('id')
            if temp_name == '':
                temp_name = 'Road No.'+str(temp_id) 
            temp_point_id = 0
            Make_Start_Points_Road(temp_geo, temp_point_info, seg_length, temp_point_id, temp_id) #每隔seg_length创建一个出发点
            counting += len(temp_point_info)
            print('第%d条：id为%s' % (i, temp_id))
            
            start_time = time.time()
            ws = Compute_Walkscore_Road(temp_point_info, self.weight_tables, self.MultiType_poi_points_geo, temp_geo)   
            walkscore = ws['main']
            print('步行指数为 %f   ' % walkscore, end='')            
            end_time = time.time()             
            print('步行指数计算%f秒，共%f秒' % ((end_time-start_time), (end_time-start)))
            
            if flag == '1':           
                temp_road.SetField("walkscore", walkscore)
                for poi_type in self.poi_types:
                    temp_ws = ws[poi_type]
                    if poi_type == 'grocery_stores':
                        poi_type = 'grocery'
                    elif poi_type == 'restaurants_and_bars':
                        poi_type = 'r_b'
                    temp_road.SetField(poi_type, temp_ws)
                layer.SetFeature(temp_road)        
            
            temp_roadInfo = RoadInfo(temp_name, temp_id, temp_geo, 0)
            temp_road_info.append(temp_roadInfo)
            temp_road = layer.GetNextFeature()
#            break
        self.all_road_info = temp_road_info
        self.all_start_point_info = temp_point_info
        print(counting)
        return True
         
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
    
    
    
    
         
'''            
walkscore_calculator = WalkscoreCalculator()
types = walkscore_calculator.poi_types
walkscore_calculator.Set_Road_Linedata('C:\\Users\\DELL\\Desktop\\first_trial\\road\\roads_cgcs2000.shp')
walkscore_calculator.Set_POI_Pointdata('C:\\Users\\DELL\\Desktop\\first_trial\\')
walkscore_calculator.Prepare_Roadinfo()
walkscore_calculator.Prepare_POIinfo()
walkscore_calculator.Compute_Walkscore(types)
'''


                
            