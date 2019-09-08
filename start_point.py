from osgeo import ogr
class Startpoint:
    def __init__(self, point_id, road_id, point_geo, walkscore=0):
        self.point_id = point_id
        self.road_id = road_id
        self.point_geo = point_geo
        self.walkscore = walkscore
    def Update_Walkscore(self, walkscore):
        self.walkscore = walkscore