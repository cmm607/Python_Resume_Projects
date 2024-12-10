import pydeck as pdk
import streamlit as st
import pandas as pd
import numpy as np
import dataloader

def create_layer(data,radius=4):
    '''
    Create a pydeck scatterplot layer for a dataframe:

    inputs:

        data        :   a pandas dataframe with columns
                        'City', 'IATA', 'Latitude', and 'Longitude'
    
        layer_name  :   a string: name for the layer:
                        ideally this will just be origin and destination
    returns

        pdk.Layer   :   A configured layer for Pydeck scatterplot          
    '''

    return pdk.Layer    (
                        'ScatterplotLayer',
                        data=data,
                        get_position = ['Longitude','Latitude'],
                        get_radius = 'PointSize',
                        stroked=True,
                        line_width_min_pixels=3,
                        get_fill_color = 'Color',
                        pickable = True,
                        tooltip = True
                        )





def plot_map(df):
    '''
    Plot a map: separate layers/ coloring for origin and destinations.
    If origin_coordinates is None or empty, display a blank map of the US.


    the dataframe should have the 'Stops' and 'Weighted Score' columns
    '''

    # Initialize separate layers for nodes and edges:

    nodes = []
    edges = []

    min_score,max_score = df['Weighted Score'].min(),df['Weighted Score'].max()

    #set the interval: even though it seems unlikely in this situation,
    #avoid division by zero

    score_range = (max_score - min_score)

    #define a lambda function to set the thickness based on 'thickness_range' input:
    

    #track unique nodes:

    unique_nodes = set()

    for _,row in df.iterrows():
        #break up the stops:
        stops = list(row['Itinerary'])
        weighted_score  =   row['Weighted Score']
        
        
        #check code in a little bit 
        coordinates = [dataloader.get_airport_coordinates(code) for code in stops]

        #add nodes:

        if coordinates:
            origin = coordinates[0]
            if (origin[0],origin[1]) not in unique_nodes:
                #set points identified as origin in ORANGE:
                nodes.append({'Latitude': origin[0], 'Longitude': origin[1],"Color": [255, 120, 0],"Weighted Score" : 0})
                unique_nodes.add((origin[0] , origin[1]))


            #others should be BLUE:
            for coord in coordinates[1:-1]:
                stop = (coord[0] , coord[1])
                if stop not in unique_nodes:
                    nodes.append({'Latitude': coord[0] , 'Longitude':coord[1],"Color": [0, 120, 255],"Weighted Score":weighted_score})
                    unique_nodes.add(stop)

            #orange: last leg is the same as first in our current format:
            last_stop = coordinates[-1]

            if (last_stop[0],last_stop[1]) not in unique_nodes:
                nodes.append({'Latitude':last_stop[0],'Longitude':last_stop[1],'Color':[255, 120, 0],"Weighted Score":weighted_score})
                unique_nodes.add((last_stop[0] , last_stop[1]))

        #add edges:
        #for i in range(len(coordinates)-1):
        #    edges.append({'path' : [coordinates[i],coordinates[i+1]], 'thickness' : thickness_scale(weighted_score)})
        
 
    
    
            
    

    # Create a DataFrame for all coordinates:
    all_coordinates = pd.DataFrame(nodes)

    # Add PointSize column based on ranking:
    point_sizes = [150000,120000,90000,60000]
    all_coordinates.sort_values(by='Weighted Score', ascending=False, inplace=True)
    all_coordinates.reset_index(drop=True, inplace=True)
    all_coordinates['PointSize'] = all_coordinates.index.map(lambda idx: point_sizes[idx] if idx < len(point_sizes) else 40000)



    # Create a layer for the origin and destination nodes:
    origin_dest_layer = create_layer(all_coordinates, 'Nodes')

 




    lat_min , lat_max   =   all_coordinates['Latitude'].min() , all_coordinates['Latitude'].max()
    lon_min , lon_max   =   all_coordinates['Longitude'].min() , all_coordinates['Longitude'].max()

    center_lat , center_lon =   (lat_min + lat_max) / 2 , (lon_min + lon_max)/2

    view_state  =   pdk.ViewState(latitude= center_lat , longitude=center_lon,zoom=4,pitch=0)

    #render

    st.pydeck_chart (
                    pdk.Deck(
                        map_style="mapbox://styles/mapbox/light-v10",
                        initial_view_state=view_state,
                        layers=(origin_dest_layer)
                    ))
    

