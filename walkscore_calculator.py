from osgeo import ogr
from osgeo import gdal
from road_info import RoadInfo
from poi_point import Poipoint 
from make_start_points import Make_Start_Points_Road, Make_Start_Points_Region
from compute_walkscore import Compute_Walkscore_Road, Compute_Walkscore_Region
from networkx_readshp import read_shp_to_graph
from scipy import spatial
import numpy as np

import os
import time
import shelve
import csv


'''防止编码出现问题'''
gdal.SetConfigOption('GDAL_FILENAME_IS_UTF8', 'YES')
gdal.SetConfigOption('SHAPE_ENCODING', 'UTF-8')
class WalkscoreCalculator:
    all_road_info = []
    all_start_point_info = []
    def __init__(self, city):
        self.road_linedata = ''
        self.poi_pointdata = {}
        self.all_road_info.clear()
        self.all_start_point_info.clear()
        self.MultiType_poi_points = {}
        self.weight_table = {}  
        self.city = city
        self.kdtrees = {}
        self.road_points = {}
#后面再加种类 

        
    def Set_Weights(self, filepath):
        with open(filepath, 'r') as file:
            reader = csv.reader(file)
            lines = list(reader)
            del lines[0]
            for line in lines:
                poi_code = line[0]
                poi_code = del_last_letter(poi_code)
                poi_type = line[1]
                poi_weights = line[2].split('+')
                self.weight_table[poi_code] = [[float(poi_weight) for poi_weight in poi_weights], poi_type]

        ss = 0
        for weight_poi_type in self.weight_table.values():
            s = 0
            for w in weight_poi_type[0]:
                s += w
            ss += s
            print(weight_poi_type[1], s)
        print(ss)
    #    print(self.weight_table)
    def Set_Road_Linedata(self, filename:str):
        self.road_linedata = filename
        if os.path.exists(self.road_linedata):
            print('道路数据路径设置完毕...')
        else:
            print('道路数据路径设置失败...')
    
    def Set_New_Road_Linedata(self, filename):
        self.new_road_linedata = filename
        
    def Set_POI_Pointdata(self, filepath:str):
        MultiType_poi_points = {}
        kdtrees = {}
        with open(filepath, 'r') as file:
            reader = csv.reader(file)
            lines = list(reader)
            del lines[0]
            for poi_code, weights_types in self.weight_table.items(): 
                SingleType_poi_points = []
                for line in lines:
                    if float(line[15]) > 3000 or len(line) != 16:
                        continue
                    current_code = str(line[2])
                    current_code = del_last_letter(current_code)
                    #为什么种类代码的后面有个A呢，是因为excel总是把字符串当成数字，然后把第一个0删了，有个A可以强制为字符串
                    if is_included(current_code, poi_code):
                        coord = (float(line[5]), float(line[6]))
                        SingleType_poi_points.append(coord)
                        road_point = to_tuple(line[12])
                        pre_point = to_tuple(line[13])
                        next_point = to_tuple(line[14])
                        dist = float(line[15])
                        self.road_points[coord] = [road_point, pre_point, next_point, dist]
                kdtree = spatial.KDTree(np.array(SingleType_poi_points))
                kdtrees[weights_types[1]] = kdtree
                MultiType_poi_points[weights_types[1]] = SingleType_poi_points
        self.kdtrees = kdtrees
        self.MultiType_poi_points = MultiType_poi_points
        
        #print(self.MultiType_poi_points)
        '''
        with open('test.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            for k, v in MultiType_poi_points.items():   
                for i in v:
                    x = i[0]
                    y = i[1]
                    writer.writerows([[k, x, y]])
        '''
        print('\n所有POI的数据准备完成...')

    
    def Compute_Road_Walkscore(self, seg_length):
        '''准备道路的数据以及计算步行指数'''
        #Multi_roads_geos = read_shp_to_geo(self.road_linedata)
        G = read_shp_to_graph(self.road_linedata, simplify=False).to_undirected()
        
        #temp_road_info = []      
        #准备路网的数据，temp_road_info是所有道路的数据，temp_roadInfo是一条道路的数据  
        '''读取shp文件'''
        dr = ogr.GetDriverByName('ESRI Shapefile')
        if dr is None:
            print('注册道路的驱动失败...')
            return False
        print('注册道路的驱动成功...')
        ds = dr.Open(self.road_linedata, 0)
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
        
        print('正在统计一共有多少个点')
        road_count, point_count, spatial_reference, fDefns = Counting(layer, seg_length)
        field_count = len(fDefns)
        for fDefn_index in range(len(fDefns)):
            fName = fDefns[fDefn_index].GetName()
            if 'name' in fName.lower():
                name_index = fDefn_index+1
        print('一共有%d条路，%d个点' % (road_count, point_count))
        
        flag = input("是否写入？1为写入，2为不写入，其他字符为退出\n")
        #flag = '2'
        if flag == '1': 
            new_ds = dr.CreateDataSource(self.new_road_linedata)
            new_layer = new_ds.CreateLayer('city', spatial_reference, ogr.wkbLineString)
            '''
            Field_real_id = ogr.FieldDefn('real_id', ogr.OFTInteger)
            Field_id = ogr.FieldDefn('id', ogr.OFTString)
            Field_center = ogr.FieldDefn('center', ogr.OFTString)
            Field_citycode = ogr.FieldDefn('citycode', ogr.OFTString)
            Field_name = ogr.FieldDefn('name', ogr.OFTString)
            Field_road_type = ogr.FieldDefn('road_type', ogr.OFTString)
            Field_width = ogr.FieldDefn('width', ogr.OFTReal) 
            '''
            fDefn_real_id = ogr.FieldDefn('real_id', ogr.OFTInteger)
            fDefn_walkscore = ogr.FieldDefn("walkscore", ogr.OFTReal)
            fDefns.insert(0, fDefn_real_id)
            fDefns.append(fDefn_walkscore)
            for fDefn in fDefns:
                new_layer.CreateField(fDefn)
            for weights_types in self.weight_table.values():
                poi_type = weights_types[1]
                fDefn = ogr.FieldDefn(poi_type, ogr.OFTReal)
                new_layer.CreateField(fDefn)
            Defn = new_layer.GetLayerDefn()
        elif flag == '2':
            print('不写入\n')
        else:
            return False        
        '''
        print('正在生成POI点和对应最近道路点的字典')
        road_points = GenerateRoadPoints(self.MultiType_poi_points, layer, seg_length)  
        with shelve.open('../Road_Points/'+self.city, 'c') as file:
            print('正在将POI点和对应最近道路点的字典写入文件')
            file['road_points'] = road_points 
        '''
        print('kdtree, seg_length=' + str(seg_length))     
        print('\n开始计算步行指数')

        layer.ResetReading()
        temp_road = layer.GetNextFeature()
        temp_count = 0
        start = time.time()
        counting_up_to_now = 0
        while temp_road:
            
            temp_count += 1
            start_point_info = {}
            temp_geo = temp_road.GetGeometryRef().Clone()    #temp_geo可能是MultiLinestring
            real_id = temp_count
            fields = [real_id]
            fields.extend(GetFields(temp_road, field_count))  
            '''
            if temp_id != '025I50F048039268':#025H50F0020382788':#025H50F00203948:
                temp_road = layer.GetNextFeature()
                continue     
            '''
            '''
            if temp_count <= 44761:
                temp_road = layer.GetNextFeature()
                continue
            '''    
            if '高速' in fields[name_index]:
                temp_road = layer.GetNextFeature()
                continue
            
            start_time = time.time()
            '''
            if temp_geo.GetGeometryName() == 'MULTILINESTRING':
                roads_count = temp_geo.GetGeometryCount()
                for index in range(roads_count):
                    temp_road_geo = temp_geo.GetGeometryRef(index)
                    Make_Start_Points_Road(temp_road_geo, start_point_info, seg_length, temp_id)#每隔seg_length创建一个出发点
            elif temp_geo.GetGeometryName() == 'LINESTRING':
            '''
            Make_Start_Points_Road(temp_geo, start_point_info, seg_length)

            counting = len(start_point_info)
            counting_up_to_now += counting
            print('第%d/%d条：名称为%s，%d个点' % (temp_count, road_count, fields[name_index], counting ))
            
            ws = Compute_Walkscore_Road(start_point_info, 
                                        self.weight_table, 
                                        self.MultiType_poi_points, 
                                        self.road_points,
                                        G,
                                        self.kdtrees)                                         
            walkscore = ws['main']

            if flag == '1':  
                feature = ogr.Feature(Defn)
                feature.SetGeometry(temp_geo)
                fields.append(walkscore)
                for weights_types in self.weight_table.values():
                    poi_type = weights_types[1]
                    poi_type_ws = ws[poi_type]
                    fields.append(poi_type_ws)                         
                for i in range(len(fields)):
                    feature.SetField(i, fields[i])
      
                new_layer.CreateFeature(feature)     
                new_ds.SyncToDisk()
                
            print('步行指数为 %f   ' % walkscore, end='')            
            end_time = time.time()  
            time_left = (end_time-start) / counting_up_to_now * (point_count - counting_up_to_now)
            print('步行指数计算%f秒，共%f秒, 预计还剩%.1f分钟' % ((end_time-start_time), (end_time-start), time_left/60))

            '''
            temp_roadInfo = RoadInfo(temp_name, temp_id, temp_geo, 0)
            temp_road_info.append(temp_roadInfo)
            '''
            temp_road = layer.GetNextFeature()
            #if temp_count > 10:
            #break
        '''
        self.all_road_info = temp_road_info
        self.all_start_point_info = start_point_info
        '''

        return True
        
    def Compute_Region_Walkscore(self, first_point_coord, last_point_coord, density, filepath):
        start_points_info = Make_Start_Points_Region(first_point_coord, last_point_coord, density)
        Compute_Walkscore_Region(start_points_info, self.weight_table, self.MultiType_poi_points_geo)
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
    

        
    
def is_included(current_code:str, weight_table_poi_code:str):
    #current_code是爬到的，weight_table_poi_code是自己写的权重表里的  
    #poi_code: 050000/050101|050119A "/"后面是要排除掉的id 表示050000类的都会被提取，但是除了属于050101和050119的
    needed_poi_codes = weight_table_poi_code.split('/')[0] #要包含的id
    if '/' in weight_table_poi_code:
        excepted_poi_codes = weight_table_poi_code.split('/')[1] #腰排除掉的id
    else:
        excepted_poi_codes = ''
    poi_codes = [del_zeros(temp_code) for temp_code in needed_poi_codes.split('|')] #[05]
    full_current_codes = [temp_code for temp_code in current_code.split('|')] #[050101, 050105]
    excepted_poi_codes = [temp_code for temp_code in excepted_poi_codes.split('|')] #[050101, 050119]

    #先判断在不在需要排除掉的里面
    for full_current_code in full_current_codes:
        if full_current_code in excepted_poi_codes:
            return False
            
    for poi_code in poi_codes:
        for full_current_code in full_current_codes:
            if full_current_code[:len(poi_code)] == poi_code:
                return True            
    return False

def del_zeros(code):
    code = list(code)
    while code and code[-1] == '0' and code[-2] == '0':
        del code[-1]
        del code[-1]
    return ''.join(code)

def del_last_letter(code):
    code = list(code)
    code = code[:-1]
    return ''.join(code)

def to_tuple(s):
    coord = s.split(', ')
    x = float(coord[0][1:])
    y = float(coord[1][:-1])
    return (x, y)

    
def Counting(layer, seg_length):
    '''统计有多少条路多少个点'''
    layer.ResetReading()
    temp_road = layer.GetNextFeature()
    field_count = temp_road.GetFieldCount()
    fDefns = []
    for i in range(field_count):
        fDefn = temp_road.GetFieldDefnRef(i)
        fDefns.append(fDefn)
            
    road_count = 0
    point_count = 0
    while temp_road:
        temp_geo = temp_road.GetGeometryRef().Clone()
        start_point_info = {}
        if temp_geo.GetGeometryName() == 'MULTILINESTRING':
            roads_count = temp_geo.GetGeometryCount()
            for index in range(roads_count):
                temp_road_geo = temp_geo.GetGeometryRef(index)
                Make_Start_Points_Road(temp_road_geo, start_point_info, seg_length)
        elif temp_geo.GetGeometryName() == 'LINESTRING':
            Make_Start_Points_Road(temp_geo, start_point_info, seg_length)
        road_count += 1
        point_count += len(start_point_info)
        temp_road = layer.GetNextFeature()
    srs = temp_geo.GetSpatialReference()
    return road_count, point_count, srs, fDefns

def GetFields(feature, field_count):
    fields = []
    for i in range(field_count):
        fDefn = feature.GetFieldDefnRef(i)
        if fDefn.GetType() == ogr.OFTInteger:
            field = feature.GetFieldAsInteger(i)
            
        elif fDefn.GetType() == ogr.OFTReal:
            field = feature.GetFieldAsDouble(i)
            
        elif fDefn.GetType() == ogr.OFTString:
            field = feature.GetFieldAsString(i)  
        fields.append(field)
    return fields
'''            
walkscore_calculator = WalkscoreCalculator()
types = walkscore_calculator.poi_types
walkscore_calculator.Set_Road_Linedata('C:\\Users\\DELL\\Desktop\\first_trial\\road\\roads_cgcs2000.shp')
walkscore_calculator.Set_POI_Pointdata('C:\\Users\\DELL\\Desktop\\first_trial\\')
walkscore_calculator.Prepare_Roadinfo()
walkscore_calculator.Prepare_POIinfo()
walkscore_calculator.Compute_Walkscore(types)
'''
#print(is_included('050300', '050000/050101|050119A'))