### BASIC PROGRAM THAT LOOKS FOR OVERLAP BETWEEN QCOMPONENTS 
from numpy import *
import geopandas as gpd
import pandas as pd 


class QDesign_Check():   # ()design
    """QDesign_Check tests for overlap/collisions between qcomponents.
    """
    
    def overlap_tester(design):    # () self

        for unique_int in design._components:
                print(" ") 
                print("Component ID:")
                print(unique_int)
                comp = unique_int

                # Get the GeoSeries tables separately for polys and paths, then combine. 
                poly = design._components[unique_int].qgeometry_table('poly')
                path = design._components[unique_int].qgeometry_table('path')
                combined = gpd.GeoDataFrame(pd.concat([poly, path], ignore_index=True))
                poly_geo = poly["geometry"]
                path_geo = path["geometry"]
                combined_geo = combined["geometry"]

                # loop within a loop to calculate distance between components  
                for unique_int in design._components:

                    main_counter = 0.0 

                    # don't calculate distance between a component and itself 
                    if unique_int == comp:
                        #print("Don't check for collisions between component and itself.")
                        pass
                    else:
                        poly_inner = design._components[unique_int].qgeometry_table('poly')
                        path_inner = design._components[unique_int].qgeometry_table('path')
                        combined_inner = gpd.GeoDataFrame(pd.concat([poly_inner, path_inner], ignore_index=True))
                        poly_geo_inner = poly_inner["geometry"]
                        path_geo_inner = path_inner["geometry"]
                        combined_geo_inner = combined_inner["geometry"]

                        collision_counter_outer = 0.0 

                        n = int(size(combined_geo_inner))
                        for i in range(0,n): 

                            #print("inner element:", i)
                            a=combined_geo.crosses(combined_geo_inner[i])

                            m = int(size(a))
                            collision_counter = 0.0 
                            for j in range(0,m):
                                if a[j]==1:
                                    collision_counter = collision_counter + 1.0 
                                else:
                                    pass
                            if collision_counter > 0.0:
                                collision_counter_outer = collision_counter_outer + 1.0 
                                pass 
                            else:
                                pass

                        if collision_counter_outer > 0.0:
                            main_counter = main_counter + 1.0 
                        else:
                            pass

                    if main_counter > 0.0:
                        print("Has a collision with the following QComponent:", unique_int)
                    else:
                        pass 
