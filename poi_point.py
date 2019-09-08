from osgeo import ogr
class Poipoint:
    def __init__(self, point_name, point_id, point_type:str, point_geo:ogr.Geometry, weight:float, dis_to_start:float):
        self.point_name = point_name
        self.point_id = point_id
        self.point_type = point_type
        self.point_geo = point_geo
        self.weight = 0
        self.dis_to_start = 0
    '''下面这两个函数没用上'''    
    def Update_Weight(self, weight:float):

        if self.dis_to_start <= 400:
            atten_index = 1
        elif self.dis_to_start > 400 and self.dis_to_start <= 800:
            atten_index = 0.9
        elif self.dis_to_start > 800 and self.dis_to_start <= 1200:
            atten_index = 0.55
        elif self.dis_to_start > 1200 and self.dis_to_start <= 1600:
            atten_index = 0.25
        elif self.dis_to_start > 2000 and self.dis_to_start <= 2400:
            atten_index = 0.08
        else:
            atten_index = 0
        self.weight = weight*atten_index        
    def Update_Dis(self, dis:float):
        self.dis_to_start = dis