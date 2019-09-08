from osgeo import ogr

class RoadInfo:
    def __init__(self, road_name, road_id, road_geo, road_walkscore):
        self.road_name = road_name
        self.road_id = road_id
        if self.road_name == '':
            self.road_name = 'Road No.'+str(road_id)
        self.road_geometry = road_geo
        self.road_walkscore = road_walkscore
#temp_roadInfo.Get_Startpoints()
#    def Get_Startpoints(self):
        