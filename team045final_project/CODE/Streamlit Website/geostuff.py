import streamlit as st
import pandas as pd
import pydeck as pdk    
import dataloader
from geopy.distance import geodesic

def get_origin_coordinates(IATA , airports_geo = dataloader.airports_geo,coordinates_only = False):
    ''' 
    inputs:

        IATA            :   The IATA airport code
        airports_geo    :   The pandas dataframe containing the geo information
                            (currently stored in the dataloader py file)
    
    returns:

        a dictionary    :   {
                            'City'      :   city name from the dataloader,
                            'IATA'      :   the IATA code supplied,
                            'Latitude'  :   Latitude coordinate,
                            'Longitude' :   Longitude coordinate    
                            }
    '''
    cols =   ['City','IATA','Latitude','Longitude']

    criteria = airports_geo['IATA']==IATA

    if airports_geo[criteria].empty:
        output = None
        return output
    else:
        output = airports_geo.query("IATA == @IATA")[cols].iloc[0,:].to_dict()
        if coordinates_only:
            return [output['Latitude'] , output['Longitude']]
        else:
            return output

def filter_airports_within_radius(origin_coords , radius , airports_geo=dataloader.airports_geo):
    ''' 
    inputs
        origin_coords       :   a list: [latitude,longitude]
        radius              :   float/int : radius in
        airports_geo        :   The pandas dataframe containing the geo information
                                (currently stored in the dataloader py file)
    
    outputs
        pandas dataframe with desired results
    '''

    def calculate_distance(row):
        return geodesic(origin_coords,(row['Latitude'],row['Longitude'])).miles
    
    distances = airports_geo.apply(calculate_distance,axis=1)

    return list(airports_geo[distances<=radius]['IATA'].unique())
    




