### BASIC PROGRAM THAT LOOKS FOR OVERLAP BETWEEN QCOMPONENTS
from numpy import size
import geopandas as gpd
import pandas as pd


class QDesignCheck():
    """QDesign_Check contains various design checks, such as
    testing designs in qiskit metal for unintended overlap
    between components and/or connections between components.
    """

    def __init__(self, design: 'QDesign'):
        self.design = design

    def update_design(self, design: 'QDesign'):
        self.design = design

    def overlap_tester(self):
        design = self
        """This particular function tests for overlap amongst qcomponents
        and CPWs. It will catch qubit/qubit overlap, qubit, CPW overlap
        and CPW/CPW overlap.
        """

        for unique_int in self.design._components:
            print(" ")
            print("Component ID:")
            print(unique_int)
            comp = unique_int

            # Get the GeoSeries tables separately for polys and paths, then combine.
            poly = self.design._components[unique_int].qgeometry_table('poly')
            path = self.design._components[unique_int].qgeometry_table('path')
            combined = gpd.GeoDataFrame(
                pd.concat([poly, path], ignore_index=True))
            combined_geo = combined["geometry"]

            # loop within a loop to calculate distance between components
            for unique_int in self.design._components:

                main_counter = 0.0

                # don't calculate distance between a component and itself
                if unique_int == comp:
                    #print("Don't check for collisions between component and itself.")
                    pass
                else:
                    poly_inner = self.design._components[
                        unique_int].qgeometry_table('poly')
                    path_inner = self.design._components[
                        unique_int].qgeometry_table('path')
                    combined_inner = gpd.GeoDataFrame(
                        pd.concat([poly_inner, path_inner], ignore_index=True))
                    combined_geo_inner = combined_inner["geometry"]

                    collision_counter_outer = 0.0

                    n = int(size(combined_geo_inner))
                    for i in range(0, n):

                        #print("inner element:", i)
                        el_inner = combined_geo.crosses(combined_geo_inner[i])

                        m = int(size(el_inner))
                        collision_counter = 0.0
                        for j in range(0, m):
                            if el_inner[j] == 1:
                                collision_counter = collision_counter + 1.0
                            else:
                                pass
                        if collision_counter > 0.0:
                            collision_counter_outer = collision_counter_outer + 1.0
                        else:
                            pass

                    if collision_counter_outer > 0.0:
                        main_counter = main_counter + 1.0
                    else:
                        pass

                if main_counter > 0.0:
                    print("Has a collision with the following QComponent:",
                          unique_int)
                else:
                    pass
