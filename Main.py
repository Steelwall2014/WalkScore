from walkscore_calculator import WalkscoreCalculator
import time

def main():
    WS_cal = WalkscoreCalculator()
    WS_cal.Set_Road_Linedata('D:\\WalkScore\\jiangdu\\roads\\roads_cgcs2000_special.shp')
    WS_cal.Set_POI_Pointdata('D:\\WalkScore\\jiangdu\\')
    WS_cal.Prepare_POIinfo()    
    first_point_coord = [20733766, 3620680] 
    last_point_coord =  [20767706, 3582231] 
    seg_length = 200
    density = 500
    region_walkscore_filepath = 'D:\\WalkScore\\jiangdu\\Region\\points_'+str(density)+'m.shp'
    flag = input('按1开始计算街道的步行指数，按2开始计算面域步行指数\n')
    if flag == '1':
        start_time = time.time()
        WS_cal.Compute_Road_Walkscore(seg_length)
        end_time = time.time()
        print('完成! 一共用时：%f秒' % (end_time-start_time))        
    elif flag == '2':
        start_time = time.time()
        WS_cal.Compute_Region_Walkscore(first_point_coord, last_point_coord, density, region_walkscore_filepath)
        end_time = time.time()
        print('完成! 一共用时：%f秒' % (end_time-start_time))
if __name__ == "__main__":
    main()