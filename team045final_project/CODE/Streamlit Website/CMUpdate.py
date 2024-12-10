import streamlit as st
import pandas as pd
import numpy as np
import datetime
import time
import re
import pydeck as pdk

if "counter" not in st.session_state:
    st.session_state.counter = 0

st.session_state.counter += 1

st.set_page_config(page_title='Test_DVA_App',
                   page_icon='chart_with_upwards_trend',
                   layout='wide'
                   )

#Classes:

class Airline():
    def __init__(self,name,tiers,move,thresholds,selection_notes,airports=None):
        self.name = name #string: airline name
        self.tiers = tiers # list : strings of tier names
        self.move = move #string: what is the unit: IE dollar, point,mile
        self.thresholds = np.array(thresholds) #bounds for different tiers of status, np.array
        self.selection_notes = selection_notes
        #list of airports where the airline flies:
        self.airports = airports if airports is not None else "Optional"


#Add the airlines:
airlines    =   dict()

#Add a generic for no airline selected:
airlines['--Select an Airline--'] = Airline(name='--Select an Airline--',
                                            tiers=['No airline selected'],
                                            move = 'Level',
                                            thresholds=None,
                                            selection_notes='Please select an airline'
                                            )

airlines['Delta'] = Airline(name='Delta',
                            tiers=['None','Silver','Gold','Platinum','Diamond'],
                            move = 'MQD',
                            thresholds=[0,5000,10000,15000,28000],
                            selection_notes =   "Basic Economy tickets are not eligible for earning miles in the SkyMiles Program or earning credit toward Medallion and Million Miler Status",
                            
                            airports=[  'Atlanta, GA',         'Boston, MA',          'Chicago, IL',         'Cincinnati, OH',      'Dallas, TX',          
                                        'Denver, CO',          'Detroit, MI',         'Honolulu, HI',        'Houston, TX',         'Indianapolis, IN',    
                                        'Los Angeles, CA',     'Las Vegas, NV',       'Miami, FL',           'Minneapolis, MN',     'New York, NY',        
                                        'Orlando, FL',         'Philadelphia, PA',    'Phoenix, AZ',         'Portland, OR',        'Salt Lake City, UT',  
                                        'San Diego, CA',       'San Francisco, CA',   'Seattle, WA',         'Tampa, FL',           'Washington, D.C.'])

###################################################
#SIDEBAR
###################################################

#AIRLINE SELECTION:

st.sidebar.write('# Airline:')
airline_selection = st.sidebar.selectbox('',airlines,label_visibility='collapsed')
#add notes below airline selection for each airline:
st.sidebar.write(f"**Notes:** *{airlines[airline_selection].selection_notes}*")


#Do the following once an airline is selected:
if airline_selection != '--Select an Airline--':

    #AIRLINE STATUS INFO:

    #Current numerical value, used to determine how far to next level:
    st.sidebar.write(f'# Current {airlines[airline_selection].move}:')
    move_value = st.sidebar.number_input(f'',min_value = 0.00,format='%.2f',label_visibility='collapsed')

    #needed for each tier:
    need = {k:v for k,v in\
            zip(airlines[airline_selection].tiers,((airlines[airline_selection].thresholds)-(move_value)))\
                if (v>0)}

    #radio buttons for tiers:
    tier_choices = [f"{each} : Need {need[each]:,.2f}" for each in need]
    

    if tier_choices:
        st.sidebar.write('# Select Desired Tier:')
        tier_choice_radio = st.sidebar.radio('',options=tier_choices,label_visibility='collapsed')
        for tier in need:
            if tier in tier_choice_radio:
                tier_choice_radio = tier
                #define the spend dollar amount:
                spend = need[tier_choice_radio]


        st.sidebar.write('# Choose Flight Class:')

        st.sidebar.selectbox('',options=['Business'],label_visibility='collapsed')

        
        st.sidebar.write('# Choose Origin:')
        origin = st.sidebar.selectbox('',options = airlines[airline_selection].airports,label_visibility='collapsed')
        #destination list: display all but origin:
        dest_options = [each for each in airlines[airline_selection].airports if each != origin]
        st.sidebar.write('# Choose Destination:')
        destination = st.sidebar.selectbox('',options = dest_options,label_visibility='collapsed')


    else:
        tier_choice_radio = None
        st.sidebar.write('*(Maximum Tier Level Acheived)*')
    #change the tier_choice_radio to JUST the tier name
    #by looping over tiers:
        
###################################################
#END SIDEBAR
###################################################





st.write('# Potential Trips:')

# Define the origin (Atlanta, GA)
origin = {
    "city": "Atlanta",
    "iata_code": "ATL",
    "coordinates": [33.7490, -84.3880]
}

# Define other destinations (New York, Miami, Chicago)
destinations = [
    {"city": "New York", "iata_code": "JFK", "coordinates": [40.7128, -74.0060]},
    {"city": "Miami", "iata_code": "MIA", "coordinates": [25.7617, -80.1918]},
    {"city": "Chicago", "iata_code": "ORD", "coordinates": [41.8781, -87.6298]},
]

# Combine origin and destinations into a DataFrame for plotting points
locations = [
    {"name": f"Origin: {origin['city']} ({origin['iata_code']})", "lat": origin["coordinates"][0], "lon": origin["coordinates"][1]},
]

# Add destination points with labels
for dest in destinations:
    locations.append({
        "name": f"Potential Trip: {dest['city']} ({dest['iata_code']})",
        "lat": dest["coordinates"][0],
        "lon": dest["coordinates"][1]
    })

# Convert list to DataFrame for pydeck
location_df = pd.DataFrame(locations)

# Define the flight paths (lines) between Atlanta and each destination
flight_paths = [
    {
        "source": origin["coordinates"],
        "target": dest["coordinates"]
    }
    for dest in destinations
]

# Create a Pydeck Layer for the points (Atlanta and destinations)
scatter_layer = pdk.Layer(
    "ScatterplotLayer",
    data=location_df,
    get_position=["lon", "lat"],
    get_radius=100000,  # Adjust point size
    get_fill_color=[255, 140, 0],  # Orange color for the points
    pickable=True,
    tooltip=True,
)


# Create a Pydeck Layer for the flight paths
path_layer = pdk.Layer(
    "ArcLayer",
    data=flight_paths,
    get_source_position="source",
    get_target_position="target",
    get_source_color=[0, 128, 255],  # Blue color for flight path
    get_target_color=[255, 0, 0],    # Red color for destination
    stroke_width=3,
    auto_highlight=True,
)



# Set the initial view of the map
view_state = pdk.ViewState(
    latitude=origin["coordinates"][0],
    longitude=origin["coordinates"][1],
    zoom=4,
    pitch=0,
)

# Define the map with the layers
r = pdk.Deck(
    map_style="mapbox://styles/mapbox/light-v10",
    initial_view_state=view_state,
    layers=[scatter_layer, path_layer],
    tooltip={"text": "{name}"},  # Display tooltips with the point names
)

# Display the map in Streamlit
st.pydeck_chart(r)




#display and style data:


df = pd.DataFrame({'first column':[1,2,3],'second column':[4,5,6],})

@st.cache_data
def gen_test_df():
    return pd.DataFrame( np.random.randn(10,20),
                        columns = [f'Col {i}'  for i in range(20)])
test_df = gen_test_df()


st.write('## Selected Origin : ATL')


c1,c2 = st.columns(2)

with c1:

    #sample flight data:

    c1_data = {
    "month": [
        "2024-01", "2024-01", "2024-01",
        "2024-02", "2024-02", "2024-02",
        "2024-03", "2024-03", "2024-03",
        "2024-04", "2024-04", "2024-04",
        "2024-05", "2024-05", "2024-05",
        "2024-06", "2024-06", "2024-06",
        "2024-07", "2024-07", "2024-07",
        "2024-08", "2024-08", "2024-08",
        "2024-09", "2024-09", "2024-09",
        "2024-10", "2024-10", "2024-10",
        "2024-11", "2024-11", "2024-11",
        "2024-12", "2024-12", "2024-12"
    ],
    "destination": [
        "ORD", "MIA", "JFK",
        "ORD", "MIA", "JFK",
        "ORD", "MIA", "JFK",
        "ORD", "MIA", "JFK",
        "ORD", "MIA", "JFK",
        "ORD", "MIA", "JFK",
        "ORD", "MIA", "JFK",
        "ORD", "MIA", "JFK",
        "ORD", "MIA", "JFK",
        "ORD", "MIA", "JFK",
        "ORD", "MIA", "JFK",
        "ORD", "MIA", "JFK"
    ],
    "average_price": [
        250, 180, 300,  # January
        230, 170, 290,  # February
        260, 190, 310,  # March
        270, 200, 320,  # April
        240, 185, 305,  # May
        245, 195, 315,  # June
        255, 205, 325,  # July
        260, 210, 330,  # August
        265, 215, 335,  # September
        275, 220, 340,  # October
        285, 225, 350,  # November
        290, 230, 360   # December
    ]
    }




    st.write('### Price Trends\n')
    c1_df = pd.DataFrame(c1_data)
    st.line_chart(data = c1_df , x= 'month' ,
                                 y = 'average_price',
                                 color = 'destination')

with c2:
    st.write('### Flight Details')
    c2_data = {
    "destination": ["ORD", "MIA", "JFK", "ORD", "MIA", "JFK", "ORD"],
    "departure": [
        "2024-10-01 08:30:00", "2024-10-02 09:00:00", "2024-10-03 12:45:00",
        "2024-10-04 06:15:00", "2024-10-05 14:30:00", "2024-10-06 17:00:00",
        "2024-10-07 10:25:00"
    ],
    "arrival": [
        "2024-10-01 10:45:00", "2024-10-02 11:30:00", "2024-10-03 15:05:00",
        "2024-10-04 08:35:00", "2024-10-05 17:10:00", "2024-10-06 19:40:00",
        "2024-10-07 13:00:00"
    ],
    "cost": [320, 275, 180, 350, 295, 210, 315],
    "number_of_layovers": [1, 0, 0, 2, 1, 0, 1]
        }
    
    c2_df = pd.DataFrame(c2_data)

    # Convert 'departure' and 'arrival' to datetime format
    c2_df['departure'] = pd.to_datetime(c2_data['departure'])
    c2_df['arrival'] = pd.to_datetime(c2_data['arrival'])

    st.write(c2_df)


from itertools import permutations

target_miles = 5000  # Example target for the frequent flyer program
max_time = 15

# Define a function for calculating the route with maximum price (mileage run)
def calculate_optimal_route(destinations, prices, origin):
    # Generate all possible routes
    routes = permutations(destinations)
    
    # Initialize variables to track the best route
    max_price = 0
    best_route = None
    
    # Loop through all routes to find the route with the maximum price
    for route in routes:
        route_price = sum(prices[dest] for dest in route)
        if route_price > max_price:
            max_price = route_price
            best_route = route
            
    # Add origin at the start and end for a round trip
    best_route = [origin] + list(best_route) + [origin]
    
    return best_route, max_price

# Sample data for destinations and prices (replace with actual values)
destinations = ["JFK", "MIA", "ORD"]
prices = {"JFK": 300, "MIA": 180, "ORD": 250}
origin = "ATL"

# Calculate the optimal route and max price
optimal_route, max_price = calculate_optimal_route(destinations, prices, origin)

# Display the optimal route and max price
st.write(f"Optimal Route: {' -> '.join(optimal_route)}")
st.write(f"Total Mileage Run Value: ${max_price:,.2f}")

# Plot the optimal route on Pydeck map
route_path = [
    {
        "source": [origin["coordinates"]],
        "target": [dest[stop]] if stop in dest else origin["coordinates"]
    }
    for stop in optimal_route[1:]
]

# Update Pydeck with the new route layer
route_layer = pdk.Layer(
    "LineLayer",
    data=route_path,
    get_source_position="source",
    get_target_position="target",
    get_color=[255, 0, 0],
    width_scale=3,
)

# Re-render the map with the optimal route
r = pdk.Deck(
    map_style="mapbox://styles/mapbox/light-v10",
    initial_view_state=view_state,
    layers=[scatter_layer, route_layer],  # Add route layer to display optimal route
    tooltip={"text": "{name}"},
)

st.pydeck_chart(r)





