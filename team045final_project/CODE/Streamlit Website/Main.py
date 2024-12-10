import streamlit as st
import pandas as pd
import numpy as np
import datetime
import time
import re
import pydeck as pdk
import dataloader
import geostuff
import map_functions

#change to false if you want to connect to the API
#you will need to enter your API key on the sidebar
#of the streamlit page:

testing_mode = True

#otherwise, you will be connected to the CSV for demo purposes
#limited scope, limited dates and airports


if "counter" not in st.session_state:
    st.session_state.counter = 0

st.session_state.counter += 1

st.set_page_config(page_title='Mileage Run Finder DVA Team45',
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
                            
                            airports=[ # subset for demo purpose
                                    'Atlanta',
                                    #   'Dallas/Fort Worth',
                                    #   'Denver',
                                    #   "Chicago O'Hare",
                                    'Los Angeles',
                                    # 'Charlotte',
                                    'Las Vegas',
                                    'Phoenix',
                                    'Orlando',
                                    'Seattle',
                                    'Miami',
                                    # 'Houston',
                                    'New York',
                                    # 'Newark',
                                    'San Francisco',
                                    # 'Chicago Midway',
                                    # 'Houston'
                                    ])

###################################################
#SIDEBAR
###################################################
#AIRLINE SELECTION:

if not testing_mode:
    st.sidebar.write('# API Key:')
    api_key_inputbox = st.sidebar.text_input(label='',value='API_KEY')

st.sidebar.write('# Airline:')
airline_selection = st.sidebar.selectbox('',airlines,label_visibility='collapsed')
#add notes below airline selection for each airline:
st.sidebar.write(f"**Notes:** *{airlines[airline_selection].selection_notes}*")

need = None

#Do the following once an airline is selected:
if airline_selection != '--Select an Airline--':

    #AIRLINE STATUS INFO:

    #Current numerical value, used to determine how far to next level:
    st.sidebar.write(f'# Current {airlines[airline_selection].move}:')
    move_value = st.sidebar.number_input(f'',format='%.2f',value=4000.00,label_visibility='collapsed',step=100.00)

    #needed for each tier:
    need = {k:v for k,v in\
            zip(airlines[airline_selection].tiers,((airlines[airline_selection].thresholds)-(move_value)))\
                if (v>0)}

    #radio buttons for tiers:
    tier_choices = [f"{each} : Need {need[each]:,.2f}" for each in need]
    
    start_date_range = datetime.date(2024, 11, 14)
    end_date_range = datetime.date(2024, 11, 20)

    if tier_choices:
        st.sidebar.write('# Select Desired Tier:')
        tier_choice_radio = st.sidebar.radio('',options=tier_choices,label_visibility='collapsed')
        for tier in need:
            if tier in tier_choice_radio:
                tier_choice_radio = tier
                #define the spend dollar amount:
                spend = need[tier_choice_radio]
    
        st.sidebar.write('# Choose Dates:')
        date_range = st.sidebar.date_input(
            "Select your vacation dates",
            (start_date_range, start_date_range + datetime.timedelta(days=5)),
            min_value=start_date_range,
            max_value=end_date_range,
            format="MM.DD.YYYY",
        )
        start_date, end_date = date_range

        ##################################################        
        #ORIGIN SELECTION
        ##################################################        
        st.sidebar.write('# Choose Origin:')

        #Select from a dropdown:
        origin = st.sidebar.selectbox('',options = airlines[airline_selection].airports,label_visibility='collapsed',key='origin')
        
        #identify other airports within radius 'origin_radius', display as a multiselect
        origin_iata = dataloader.airports_reversed[origin]
        origin_coords = geostuff.get_origin_coordinates(IATA = origin_iata,coordinates_only=True)

        #convert back to simply IATA once the selection is made
        origin_options = [dataloader.airports_reversed[origin]]

        #Set destination options NOW based on these:
        destination_options = [each for each in airlines[airline_selection].airports if dataloader.airports_reversed[each] not in origin_options]
        
        #Maximum number of stops 
        st.sidebar.write('# Maximum Layovers:')
        max_stops = st.sidebar.selectbox(label = 'maxstops',
                                         options=[i for i in range(0,5)],
                                         placeholder='Select',
                                         label_visibility='hidden')
        
        #convert back to simply IATA once the selection is made
        destination_options = [each[1:4] for each in destination_options]
        
        #Now into DF form for plotting later:
        destination_options = pd.DataFrame([geostuff.get_origin_coordinates(each) for each in destination_options] )

    else:
        tier_choice_radio = None
        st.sidebar.write('*(Maximum Tier Level Acheived)*')
    #change the tier_choice_radio to JUST the tier name
    #by looping over tiers:
                    
###################################################
#END SIDEBAR
###################################################

st.write('# Potential Mileage Runs:')

##################################################
#GENERATING THE MAP
##################################################

c1, c3 = st.columns([0.35,0.65],vertical_alignment='center')

with c1:
    st.write('## Top Route Results:')
# with c2:
#     build = st.button('Build Route')
with c3:
    recalculate = st.button('Recalculate with My Customizations')

build = True if ((airline_selection != '--Select an Airline--')) else False

if build:
    #once the "CALCULATE" button is pressed,
    #wrap all user inputs together by using dataloader.mrf.user_inputs
    #recall that this was initialized as 'False' in dataloader.mrf

    dataloader.mrf.user_route_inputs  =  {
                                        'origin'            :   origin_options[0],
                                        'target_miles'      :   need[tier_choice_radio],
                                        'min_layover'       :   dataloader.timedelta(hours = 1),
                                        'max_stops'         :   max_stops,
                                        'start_date'        :   start_date,
                                        'end_date'          :   end_date,
                                        'cost_weight'       :   0.5,
                                        'time_weight'       :   0.5
                                        }
    

    if dataloader.mrf.user_route_inputs:
        #st.write('START ALGORITHM HERE!:')
        try:
            dataloader.mrf.main_build()
        except ValueError:
            st.error("""No qualifying routes found, please try: 
                        1. increase maximum layovers
                        2. loosen your search criteria
                        3. change origin airports.""")
    #Sliderbars for the weights
    st.sidebar.write('# Customize Route Search:')
    if 'time_weight' not in st.session_state:
        st.session_state.time_weight = 0.5
    if 'cost_weight' not in st.session_state:
        st.session_state.cost_weight = 0.5

    def update_cost_weight():
        st.session_state.cost_weight = 1.0 - st.session_state.time_weight

    def update_time_weight():
        st.session_state.time_weight = 1.0 - st.session_state.cost_weight

    # Create the sliders with callbacks
    st.sidebar.slider('Time Weight', min_value=0.0, max_value=1.0, value=st.session_state.time_weight, step=0.01, key='time_weight', on_change=update_cost_weight)
    st.sidebar.slider('Cost Weight', min_value=0.0, max_value=1.0, value=st.session_state.cost_weight, step=0.01, key='cost_weight', on_change=update_time_weight)

if recalculate:
    dataloader.mrf.user_preference_inputs = {
                                        'cost_weight'       :   st.session_state.cost_weight,
                                        'time_weight'       :   st.session_state.time_weight,
                                        'max_stops'         :   max_stops
                                        }
    if dataloader.mrf.user_preference_inputs:
        try:
            dataloader.mrf.main_rerank()
        except ValueError:
            st.error("""No qualifying routes found, please try: 
                        1. increase maximum layovers
                        2. loosen your search criteria
                        3. change origin airports.""")