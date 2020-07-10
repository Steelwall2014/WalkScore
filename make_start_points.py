from osgeo import ogr
import math

#创建出发点
def Make_Start_Points_Road(road_geo:ogr.Geometry, 
                           start_points:dict, 
                           seg_length:float):
    '''在road_geo上每隔seg_length取一个出发点'''

     
    count = road_geo.GetPointCount()
    total_length = road_geo.Length()

    '''如果是在递归中seg_length比路的全长还要长，那就把路的最后一个点作为出发点'''
    if seg_length >= total_length:
        start_point = road_geo.GetPoint_2D(count-1)        
        start_points[start_point] = [road_geo.GetPoint_2D(count-2), road_geo.GetPoint_2D(count-1)] 
        #start_points = {出发点: [前驱点, 后继点]}
        return 
    
    first_to_current_length = 0
    temp_length = 0
    temp_x1 = 0
    temp_y1 = 0
    temp_x2 = 0
    temp_y2 = 0
    
    '''计算当前线段的长度和累计长度'''
    for index in range(count-1):
        temp_x1 = road_geo.GetX(index)              
        temp_y1 = road_geo.GetY(index)  
        temp_x2 = road_geo.GetX(index+1)
        temp_y2 = road_geo.GetY(index+1)
        temp_length = math.sqrt( (temp_x1-temp_x2)**2 + (temp_y1-temp_y2)**2 )
        first_to_current_length = first_to_current_length + temp_length
        if seg_length < first_to_current_length:
            pre_point = (temp_x1, temp_y1)
            nex_point = (temp_x2, temp_y2)
            break
    '''这时从第零个点到第index+1个点的距离大于seg_length了'''

    '''算出发点的坐标'''
    len1 = seg_length - (first_to_current_length - temp_length)
    start_point_x = (len1 / temp_length) * (temp_x2 - temp_x1) + temp_x1
    start_point_y = (len1 / temp_length) * (temp_y2 - temp_y1) + temp_y1
    start_points[(start_point_x, start_point_y)] = [pre_point, nex_point]
    
    '''给出发点后面的点做一个线的几何体，用来进行下一个递归'''
    temp_road_geo = ogr.Geometry(ogr.wkbLineString)
    temp_road_geo.AddPoint(start_point_x, start_point_y)
    for i in range(index+1, count):
        temp_x = road_geo.GetX(i)                   
        temp_y = road_geo.GetY(i)        
        temp_road_geo.AddPoint(temp_x, temp_y)
      
    Make_Start_Points_Road(temp_road_geo, start_points, seg_length)
    
if __name__ == '__main__':     
    line = ogr.Geometry(ogr.wkbLineString)
    line.AddPoint(0, 0)
    line.AddPoint(2, 0)
    line.AddPoint(2, 1)
    line.AddPoint(3.9, 1)
    line.AddPoint(4, 1)
    start = {}
    Make_Start_Points_Road(line, start, 1.5, '0')
    print(start)
