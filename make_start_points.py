from osgeo import ogr
from start_point import Startpoint
import math

def Make_Start_Points_Road(road_geo:ogr.Geometry, 
                           start_points:list, 
                           seg_length:float, 
                           temp_point_id, 
                           temp_road_id, 
                           flag=True):
    '''在road_geo上每隔seg_length取一个出发点'''
    temp_point_id += 1    
    count = road_geo.GetPointCount()
    total_length = road_geo.Length()
    
    '''如果是在递归中seg_length比路的全长还要长，那就把路的最后一个点作为出发点'''
    if seg_length >= total_length:
        start_point_coord = road_geo.GetPoint(count-1)        
        start_point_geo = ogr.Geometry(ogr.wkbPoint)
        start_point_geo.AddPoint(start_point_coord[0], start_point_coord[1])
        start_point = Startpoint(temp_point_id, temp_road_id, start_point_geo)
        start_points.append(start_point)
        return 
    
    first_to_current_length = 0
    temp_length = 0
    temp_x1 = 0
    temp_y1 = 0
    temp_x2 = 0
    temp_y2 = 0
    
    '''计算当前线段的长度和累计长度'''
    for index in range(count):
        temp_x1 = road_geo.GetX(index)              
        temp_y1 = road_geo.GetY(index)  
        temp_x2 = road_geo.GetX(index+1)
        temp_y2 = road_geo.GetY(index+1)
        temp_length = math.sqrt( (temp_x1-temp_x2)**2 + (temp_y1-temp_y2)**2 )
        first_to_current_length = first_to_current_length + temp_length
        if seg_length < first_to_current_length:
            break
    '''这时从第零个点到第index+1个点的距离大于seg_length了'''

    '''算出发点的坐标'''
    len1 = seg_length - (first_to_current_length - temp_length)
    start_point_x = (len1 / temp_length) * (temp_x2 - temp_x1) + temp_x1
    start_point_y = (len1 / temp_length) * (temp_y2 - temp_y1) + temp_y1
    
    '''给出发点做一个点的几何体'''
    start_point_geo = ogr.Geometry(ogr.wkbPoint)
    start_point_geo.AddPoint(start_point_x, start_point_y)
    start_point = Startpoint(temp_point_id, temp_road_id, start_point_geo)
    start_points.append(start_point)
    
    '''给出发点后面的点做一个线的几何体，用来进行下一个递归'''
    temp_road_geo = ogr.Geometry(ogr.wkbLineString)
    temp_road_geo.AddPoint(start_point_x, start_point_y)
    for i in range(index+1, count):
        temp_x = road_geo.GetX(i)                   
        temp_y = road_geo.GetY(i)        
        temp_road_geo.AddPoint(temp_x, temp_y)
    if flag:    
        Make_Start_Points_Road(temp_road_geo, start_points, seg_length, temp_point_id, temp_road_id)
    
'''    
line = ogr.Geometry(ogr.wkbLineString)
line.AddPoint(0, 0)
line.AddPoint(2, 0)
line.AddPoint(2, 1)
line.AddPoint(4, 1)
start = []
Make_Start_Points(line, start, 1.5)
print(start[3].point_geo)
'''
    
def Make_Start_Points_Region(first_point_coord, last_point_coord, density):
    first_point_x = first_point_coord[0]
    first_point_y = first_point_coord[1]
    last_point_x = last_point_coord[0]
    last_point_y = last_point_coord[1]
    pointnumber_in_x = int((last_point_x-first_point_x) / density) + 2
    pointnumber_in_y = int((first_point_y-last_point_y) / density) + 2

    temp_point_y = first_point_y
    start_points_info = []
    temp_id = 1
    for i in range(pointnumber_in_y):
        temp_point_x = first_point_x
        for j in range(pointnumber_in_x):
            temp_point_geo = ogr.Geometry(ogr.wkbPoint)
            temp_point_geo.AddPoint(temp_point_x, temp_point_y)
            temp_start_point = Startpoint(temp_id, 0, temp_point_geo)
            start_points_info.append(temp_start_point)
            temp_point_x += density
            temp_id += 1
        temp_point_y = temp_point_y - density 
    return start_points_info
        
    