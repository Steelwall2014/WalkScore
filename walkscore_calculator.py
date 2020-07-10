from osgeo import ogr
from osgeo import gdal
from road_info import RoadInfo
from poi_point import Poipoint 
from make_start_points import Make_Start_Points_Road, Make_Start_Points_Region
from compute_walkscore import Compute_Walkscore_Road, Compute_Walkscore_Region
from networkx_readshp import read_shp_to_graph
from scipy import spatial
import numpy as np
import catch_road
import shp

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
        self.road_points = {}
        self.shelve_path = './Shelve/'
        self.flag = '3'
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
        print('权重表如下：')
        for weight_poi_type in self.weight_table.values():
            s = 0
            for w in weight_poi_type[0]:
                s += w
            ss += s
            print(weight_poi_type[1], s)
        self.weight_sum = ss
        print('权重和为：%f' % ss)
    #    print(self.weight_table)
    def Set_Road_Linedata(self, filename:str):
        self.road_linedata = filename
        if os.path.exists(self.road_linedata):
            print('道路数据路径设置完毕...')
        else:
            print('道路数据路径设置失败...')
    
    def Set_New_Road_Linedata(self, filename):
        self.new_road_linedata = filename
        
    def Set_POI_Pointdata(self, filepath:str, new_csv_path:str):
        print('##############################')
        print('正在检测POI是否已经过抓路...')
        MultiType_poi_points = {}
        index = new_csv_path.find('.csv')
        new_csv_path_list = list(new_csv_path)
        new_csv_path_list.insert(index, '错误')
        error_path = ''.join(new_csv_path_list)

        lines = []
        catch_lines = []
        with open(filepath, 'r', encoding='utf-8') as file:
            lines = list(csv.reader(file))
        if os.path.exists(new_csv_path):
            with open(new_csv_path, 'r') as file:
                catch_lines = list(csv.reader(file))
        if not os.path.exists(new_csv_path) or len(lines) != len(catch_lines):
            print('POI尚未被抓取到道路上')
            print('开始将POI抓取到道路上.........')
            catch_road.catch(self.city, 
                             filepath,
                             self.road_linedata,
                             new_csv_path, error_path, 50)
        else:
            print('POI已经成功被抓取到道路上')
        del lines
        del catch_lines
        print('正在准备POI的数据...')
        with open(new_csv_path, 'r') as file:
            reader = csv.reader(file)
            lines = list(reader)
            coord_index = lines[0].index('lng')
            code_index = lines[0].index('poi_code')
            del lines[0]
            for poi_code, weights_types in self.weight_table.items(): 
                SingleType_poi_points = []
                for line in lines:
                    if float(line[-1]) > 3000:
                        continue
                    current_code = str(line[code_index])
                    current_code = del_last_letter(current_code)
                    #为什么种类代码的后面有个A呢，是因为excel总是把字符串当成数字，然后把第一个0删了，有个A可以强制为字符串
                    if is_included(current_code, poi_code):
                        coord = (float(line[coord_index]), float(line[coord_index+1]))
                        SingleType_poi_points.append(coord)
                        road_point = to_tuple(line[-4])
                        pre_point = to_tuple(line[-3])
                        next_point = to_tuple(line[-2])
                        dist = float(line[-1])
                        self.road_points[coord] = [road_point, pre_point, next_point, dist]
                MultiType_poi_points[weights_types[1]] = SingleType_poi_points
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
        print('所有POI的数据准备完成')
        print('#################################')

    
    def Compute_Road_Walkscore(self, seg_length, poi_num, part_num):
        '''准备道路的数据以及计算步行指数'''
        #Multi_roads_geos = read_shp_to_geo(self.road_linedata)
        scale = 100.0 / self.weight_sum
        print('正在检测Graph和KDtree是否已经生成过')
        write_G = False
        write_T = False
        if not os.path.exists(self.shelve_path):
            os.makedirs(self.shelve_path)
        if not os.path.exists(self.shelve_path + self.city + '.dat'):
            write_G = True
            write_T = True
        elif os.path.exists(self.shelve_path + self.city + '.dat'):
            s = shelve.open(self.shelve_path + self.city, 'r')
            if s.get('G') is None:
                write_G = True
            if s.get('T') is None:
                write_T = True
            s.close()
        
        print('Graph: 未生成', end='  ') if write_G else print('Graph: 已生成', end='  ')  
        print('KDtree: 未生成') if write_T else print('KDtree: 已生成') 
        
        if write_G:
            print('正在生成Graph...')
            s = shelve.open(self.shelve_path + self.city, 'c')            
            G = read_shp_to_graph(self.road_linedata, simplify=False).to_undirected()
            s['G'] = G
            s.close()
            print('Graph生成完成')
        if write_T:
            print('正在生成KDtree...')
            s = shelve.open(self.shelve_path + self.city, 'c')            
            kdtrees = self.create_kdtree()
            s['T'] = kdtrees
            s.close()
            print('KDtree生成完成')
        with shelve.open(self.shelve_path + self.city, 'r') as s:
            G = s['G']
            kdtrees = s['T']
        #temp_road_info = []      
        #准备路网的数据，temp_road_info是所有道路的数据，temp_roadInfo是一条道路的数据  
        '''读取shp文件'''
        reader = shp.shp_reader(self.road_linedata)
        head = reader.readhead()
        spatial_reference = reader.readSRS()

        for field in head:
            if 'name' == field.lower():
                name_index = list(head.keys()).index(field)
            elif 'id' in field.lower():
                id_index = list(head.keys()).index(field)   
                
        print('正在统计一共有多少个点...')   
        road_count, point_count = Counting(reader.layer, seg_length, name_index)   
        print('一共有%d条路，%d个点' % (road_count, point_count))
        
        parts = [1, road_count // 3, road_count // 3 * 2, road_count]
        flag = self.flag
        #flag = '2'
        if flag == '1': 
            writer = shp.shp_writer(self.new_road_linedata)
            writer.createlayer(spatial_reference, ogr.wkbLineString)
            new_head = {'real_id':ogr.OFTInteger}
            for field, _OFT in head.items():
                new_head[field] = _OFT
            new_head['walkscore'] = ogr.OFTReal
            for weights_types in self.weight_table.values():
                poi_type = weights_types[1]
                new_head[poi_type] = ogr.OFTReal       
            writer.writehead(new_head)
        elif flag == '2':
            print('不写入\n')
        else:
            return False        

        print('kdtree, seg_length=' + str(seg_length))     
        print('\n开始计算步行指数')

        real_id = 0
        start = time.time()
        counting_up_to_now = 0
        for row in reader.readrows():
            
            real_id += 1
            if not parts[part_num-1] < real_id <= parts[part_num]:
                continue
            start_point_info = {}
            temp_geo = row[-1]    #temp_geo可能是MultiLinestring
            #if real_id > 8884: break
            #if real_id != 8884: continue    
            
            start_time = time.time()
            '''
            if temp_geo.GetGeometryName() == 'MULTILINESTRING':
                roads_count = temp_geo.GetGeometryCount()
                for index in range(roads_count):
                    temp_road_geo = temp_geo.GetGeometryRef(index)
                    Make_Start_Points_Road(temp_road_geo, start_point_info, seg_length, temp_id)#每隔seg_length创建一个出发点
            elif temp_geo.GetGeometryName() == 'LINESTRING':
            '''
            if row[name_index] is not None:
                if '高速' in row[name_index]:
                    continue
            Make_Start_Points_Road(temp_geo, start_point_info, seg_length)

            counting = len(start_point_info)
            counting_up_to_now += counting
            print('第%d/%d条：名称为%s，%d个点' % (real_id, road_count, row[name_index], counting ))
            
            ws = Compute_Walkscore_Road(start_point_info, 
                                        self.weight_table, 
                                        self.MultiType_poi_points, 
                                        self.road_points,
                                        G,
                                        kdtrees,
                                        poi_num,
                                        scale)                                         
            walkscore = ws['main']
            if flag == '1':
                new_row = [real_id] + row[:-1] + [walkscore]
                for weights_types in self.weight_table.values():
                    poi_type = weights_types[1]
                    poi_type_ws = ws[poi_type]                
                    new_row.append(poi_type_ws)
                new_row.append(temp_geo)
                writer.appendrows([new_row])                
            print('步行指数为 %f   ' % walkscore, end='')            
            end_time = time.time()  
            time_left = (end_time-start) / counting_up_to_now * (point_count - counting_up_to_now)
            print('步行指数计算%f秒，共%f秒, 预计还剩%.1f分钟' % ((end_time-start_time), (end_time-start), time_left/60))
            #if real_id > 10:
            #break
        if flag == '1':
            writer.ds.Destroy()
        '''
        self.all_road_info = temp_road_info
        self.all_start_point_info = start_point_info
        '''
        print(counting_up_to_now, point_count)
        return True

    def create_kdtree(self):
        kdtrees = {}
        for weights_types in self.weight_table.values():
            SingleType_poi_points = self.MultiType_poi_points[weights_types[1]]
            kdtree = spatial.KDTree(np.array(SingleType_poi_points))
            kdtrees[weights_types[1]] = kdtree   
        return kdtrees
    
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
    #poi_code: 050000/050101|050119 "/"后面是要排除掉的id 表示050000类的都会被提取，但是除了属于050101和050119的
    needed_poi_codes = weight_table_poi_code.split('/')[0] #要包含的id
    if '/' in weight_table_poi_code:
        excepted_poi_codes = weight_table_poi_code.split('/')[1] #要排除掉的id
    else:
        excepted_poi_codes = None
    poi_codes = [del_zeros(temp_code) for temp_code in needed_poi_codes.split('|')] #[05]
    full_current_codes = [temp_code for temp_code in current_code.split('|')] #[050101, 050105]
    if excepted_poi_codes is not None:
        excepted_poi_codes = [del_zeros(temp_code) for temp_code in excepted_poi_codes.split('|')] #[050101, 050119]
    else:
        excepted_poi_codes = []
    #先判断在不在需要排除掉的里面
    for excepted_poi_code in excepted_poi_codes:
        for full_current_code in full_current_codes:
            if full_current_code[:len(excepted_poi_code)] == excepted_poi_code:
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

#18832 19711    
def Counting(layer, seg_length, name_index):
    '''统计有多少条路多少个点'''
    layer.ResetReading()
    temp_road = layer.GetNextFeature()
            
    road_count = 0
    point_count = 0
    
    while temp_road:
        name = temp_road.GetFieldAsString(name_index)
        if '高速' in name:
            temp_road = layer.GetNextFeature()
            continue
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
    return road_count, point_count

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
def TEST_is_included(): 
    print(is_included('060400|050700', '060400|060700'))
    
if __name__ == '__main__':
    TEST_is_included()