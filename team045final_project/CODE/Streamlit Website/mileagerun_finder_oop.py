import pandas as pd
import numpy as np
from datetime import timedelta, datetime
import time
import streamlit as st
import json
import map_functions

class FlightData:
    """Class to load and preprocess flight data"""
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = None
        #to make the columns in the input file
        #match what was coded:
        self.column_mapping = {
                                'origin': 'Origin',
                                'destination': 'Destination',
                                'departure': 'Departs',
                                'arrival': 'Arrives',
                                'price': 'Price'}
        

    def load_data(self):
        self.data = pd.read_csv(self.file_path)
        self.data = self.data[self.data['CarrierName']=='Delta']
        #preprocess dates AFTER renaming the columns
        self.preprocess_dates()


    def filter_airports(self, airports):
        self.data = self.data[self.data['Origin'].isin(airports) & self.data['Destination'].isin(airports)]

    def preprocess_dates(self):
        self.data['Departs'] = pd.to_datetime(self.data['Departs'])
        self.data['Arrives'] = pd.to_datetime(self.data['Arrives'])

    def filter_dates(self, start_date, end_date):
        start_date = datetime.combine(start_date, datetime.min.time())
        end_date = datetime.combine(end_date, datetime.max.time())
        self.data = self.data[(self.data['Departs'] >= start_date) & (self.data['Departs'] <= end_date)]
    
class RouteFinder:
    """Class to find all possible routes from a given origin airport and target miles"""
    def __init__(self, flight_data, origin, target_miles, min_layover, max_stops):
        self.flight_data = flight_data
        self.origin = origin
        self.target_miles = target_miles
        self.min_layover = min_layover
        self.max_stops = max_stops

    def build_route(self, current_route, remaining_flights):
        """Build all possible qualifying routes from flight legs"""
        last_flight = current_route[-1]
        valid_routes = []

        valid_connections = remaining_flights[
            (remaining_flights['Origin'] == last_flight['Destination']) &
            (remaining_flights['Departs'] >= last_flight['Arrives'] + self.min_layover)
        ]

        for _, next_flight in valid_connections.iterrows():
            new_route = current_route + [next_flight]
            total_price = sum(f['Price'] for f in new_route)

            if total_price >= self.target_miles and new_route[-1]['Destination'] == self.origin and len(new_route) > 1:
                valid_routes.append(new_route)
            elif len(new_route) <= self.max_stops + 1 and new_route[-1]['Destination'] != self.origin:
                valid_routes.extend(self.build_route(new_route, remaining_flights))
                
        return valid_routes

    def find_routes(self):
        """Find all possible routes from the origin airport"""
        initial_routes = []
        for _, flight in self.flight_data[self.flight_data['Origin'] == self.origin].iterrows():
            initial_routes.extend(self.build_route([flight], self.flight_data))
        return initial_routes 

class RouteRanker:
    """Class rank routes based on multi-objective optimization (MOO) weights or user-defined weights, input routes is from RouteFinder"""
    def __init__(self, routes, weight_time, connection_weight=0):
        self.routes = routes
        self.weight_time = weight_time
        self.weight_cost = 1 - weight_time
        self.connection_weight = connection_weight
        self.all_route_durations = [(route[-1]['Arrives'] - route[0]['Departs']).total_seconds() for route in routes]
        self.all_prices = [sum(f['Price'] for f in route) for route in routes]
        self.all_connections = [len(route) - 1 for route in routes]

    def normalize_data(self, data):
        normalized_data = {}
        for key, values in data.items():
            max_value = max(values)
            min_value = min(values)
            normalized_data[key] = [(value - min_value) / (max_value - min_value) if max_value > min_value else 0 for value in values]
        return normalized_data
        

    def calculate_weighted_score(self, normalized_data, weights):
        weighted_scores = []
        for i in range(len(self.routes)):
            weighted_score = sum(normalized_data[key][i] * weight for key, weight in weights.items())
            weighted_scores.append(weighted_score)
        return weighted_scores

    def rank_initial_routes(self):
        """Rank routes based on MOO weights computed from information entropy. Return a DataFrame of ranked routes and the MOO weight dictionary"""
        data = {
            "Total Route Duration": self.all_route_durations,
            "Total Price": self.all_prices,
            "Connections": self.all_connections
        }
        normalized_data = self.normalize_data(data)

        entropy = []
        for key in normalized_data:
            p = np.array(normalized_data[key]) / sum(normalized_data[key])
            entropy_j = -(1 / np.log(len(self.routes))) * np.nansum(p * np.log(p + 1e-9))
            entropy.append(entropy_j)

        entropy = np.array(entropy)
        weights = (1 - entropy) / (1 - entropy).sum()

        weights_dict = {
            "Total Route Duration": round(weights[0], 2),
            "Total Price": round(weights[1], 2),
            "Connections": round(weights[2], 2)
        }

        weighted_scores = self.calculate_weighted_score(normalized_data, weights_dict)

        ranked = []
        top_stops = set()

        for i, route in enumerate(self.routes):
            total_route_duration = self.all_route_durations[i]
            total_price = self.all_prices[i]
            weighted_score = weighted_scores[i]

            route_stops = set(f['Origin'] for f in route) | set(f['Destination'] for f in route)
            common_stops = len(route_stops & top_stops)
            diversity_score = 1 / (1 + common_stops)

            final_score = weighted_score * diversity_score

            flights = [{
                'Origin': flight['Origin'],
                'Destination': flight['Destination'],
                'Departs': flight['Departs'].strftime('%m/%d/%Y %H:%M'),
                'Arrives': flight['Arrives'].strftime('%m/%d/%Y %H:%M'),
                'Price': flight['Price'],
                'Duration': round(flight['Duration'] / 60, 2)#(flight['Arrives'] - flight['Departs']).total_seconds() / 60
            } for flight in route]

            all_stops = [flight['Origin'] for flight in route] + [route[-1]['Destination']]

            ranked.append({
                'Departure Time': route[0]['Departs'].strftime('%m/%d/%Y %H:%M'),
                'Arrival Time': route[-1]['Arrives'].strftime('%m/%d/%Y %H:%M'),
                'Total In-flight Duration': sum(flight['Duration'] for flight in flights),
                'Total Route Duration': round(total_route_duration / 3600, 2),
                'Total Price': total_price,
                'Weighted Score': 1 - final_score,
                'Itinerary': tuple(all_stops),
                'Flights': flights
            })

            top_stops.update(route_stops)

        return pd.DataFrame(ranked).sort_values('Weighted Score', ascending=False), weights_dict
    
    def rerank_routes(self):
        """Rank routes based on user-defined weights. Return a DataFrame of ranked routes"""
        data = {
            "Total Route Duration": self.all_route_durations,
            "Total Price": self.all_prices,
            "Connections": self.all_connections
        }
        normalized_data = self.normalize_data(data)
        weights = {
            "Total Route Duration": self.weight_time,
            "Total Price": self.weight_cost,
            "Connections": self.connection_weight  # Assuming no weight for connections in rerank_routes
        }
        weighted_scores = self.calculate_weighted_score(normalized_data, weights)

        ranked = []
        top_stops = set()

        for i, route in enumerate(self.routes):
            total_route_duration = self.all_route_durations[i]
            total_price = self.all_prices[i]
            weighted_score = weighted_scores[i]

            route_stops = set(f['Origin'] for f in route) | set(f['Destination'] for f in route)
            common_stops = len(route_stops & top_stops)
            diversity_score = 1 / (1 + common_stops)

            final_score = weighted_score * diversity_score

            flights = [{
                'Origin': flight['Origin'],
                'Destination': flight['Destination'],
                'Departs': flight['Departs'].strftime('%m/%d/%Y %H:%M'),
                'Arrives': flight['Arrives'].strftime('%m/%d/%Y %H:%M'),
                'Price': flight['Price'],
                'Duration': round(flight['Duration'] / 60, 2)#(flight['Arrives'] - flight['Departs']).total_seconds() / 60
            } for flight in route]

            all_stops = [flight['Origin'] for flight in route] + [route[-1]['Destination']]

            ranked.append({
                'Departure Time:': route[0]['Departs'].strftime('%m/%d/%Y %H:%M'),
                'Arrival Time:': route[-1]['Arrives'].strftime('%m/%d/%Y %H:%M'),
                'Total In-flight Duration': sum(flight['Duration'] for flight in flights),
                'Total Route Duration': round(total_route_duration / 3600, 2),
                'Total Price': total_price,
                'Weighted Score': 1 - final_score,
                'Itinerary': tuple(all_stops),
                'Flights': flights
            })

            top_stops.update(route_stops)

        return pd.DataFrame(ranked).sort_values('Weighted Score', ascending=False)


##################################################
#BYPASSING THE MAIN FUNCTION FOR NOW,
#Extracting features stepwise as needed....
##################################################

#load the data
flight_data = FlightData('data/cached_flights_1.csv')
flight_data.load_data()
flight_data.filter_airports(['ATL','LAX','JFK','SFO'])


#PARAMETERS FROM UI:
#will be updated from the Main.py file (streamlit)
#by way of the dataloader upon user input
#example: dataloader.mrf.parameter = (...) 
user_route_inputs = False

#if all user inputs have been completed, the
#Main.py file will change the above from 'False'
#to a dictionary of arguments

def main_build():
    '''
    This function should only be called if a user_inputs
    dictionary is available
    '''
    origin = user_route_inputs['origin']
    target_miles = user_route_inputs['target_miles']
    min_layover = timedelta(hours=1)
    max_stops = user_route_inputs['max_stops']
    weight_time = user_route_inputs['time_weight']
    connection_weight = 0
    cost_weight =   user_route_inputs['cost_weight']

    #START FILTERING:
    # Filter to only include qualifying flights

    flight_data.filter_dates(user_route_inputs['start_date'], user_route_inputs['end_date'])    
    route_finder = RouteFinder(flight_data.data, origin, target_miles, min_layover, max_stops)
    all_routes = route_finder.find_routes()
    st.write(f'{len(all_routes)} possible routes found.')
    st.session_state.all_routes = all_routes

    ranker = RouteRanker(all_routes, weight_time, connection_weight)
    initial_ranked_routes_df, moo_weights = ranker.rank_initial_routes()
    initial_ranked_routes_df['Flights'] = initial_ranked_routes_df['Flights'].apply(lambda x: json.dumps(x))
    initial_ranked_routes_df = initial_ranked_routes_df[:20]
    initial_ranked_routes_df['See Itinerary Details'] = False
    initial_df_with_flights = initial_ranked_routes_df.copy()
    initial_ranked_routes_df = initial_ranked_routes_df.drop(columns=['Flights'])
    edited_df = st.data_editor(initial_ranked_routes_df.drop(['Total In-flight Duration'],axis=1), use_container_width=True,hide_index=True)
    #insert the map here?:
    #st.write('## Insert the map here?')
    plot_data = initial_ranked_routes_df[['Itinerary','Weighted Score']]
    map_functions.plot_map(df = plot_data)

    for index, row in edited_df.iterrows():
        if row['See Itinerary Details']:
            with st.expander(f"Details for Route {index} (${row['Total Price']:.2f})"):
                flights = json.loads(initial_df_with_flights.loc[index, 'Flights'])
                for flight in flights:
                    st.markdown(f"**{flight['Origin']}** ({flight['Departs']}) -> **{flight['Destination']}** ({flight['Arrives']}), Duration: {flight['Duration']} Hours")

    st.write(f"MOO Weights: {moo_weights}")
    

user_preference_inputs = False

def main_rerank():
    '''This function should only be called if all_routes is available in session state'''
    if 'all_routes' not in st.session_state:
        st.write("Please build routes first.")
        return
    all_routes = st.session_state.all_routes
    weight_time = user_preference_inputs['time_weight']
    connection_weight = 0
    cost_weight =   user_preference_inputs['cost_weight']
    ranker = RouteRanker(all_routes, weight_time, connection_weight)
    reranked_routes_df = ranker.rerank_routes()
    reranked_routes_df = reranked_routes_df[:20]
    reranked_routes_df['See Itinerary Details'] = False
    st.write("## Top Re-ranked Routes Based on User Preferences")
    st.write(f"Reranked routes based on user preferences: Time weight={weight_time:.2f}, Cost weight={cost_weight:.2f}")

    reranked_routes_df['Flights'] = reranked_routes_df['Flights'].apply(lambda x: json.dumps(x))
    reranked_df_with_flights = reranked_routes_df.copy()
    reranked_routes_df = reranked_routes_df.drop(columns=['Flights'])
    edited_reranked_df = st.data_editor(reranked_routes_df.drop(['Total In-flight Duration'],axis=1), use_container_width=True,hide_index=True)
    for index, row in edited_reranked_df.iterrows():
        if row['See Itinerary Details']:
            with st.expander(f"Details for Route {index} (${row['Total Price']:.2f})"):
                flights = json.loads(reranked_df_with_flights.loc[index, 'Flights'])
                for flight in flights:
                    st.markdown(f"**{flight['Origin']}** ({flight['Departs']}) -> **{flight['Destination']}** ({flight['Arrives']}), Duration: {flight['Duration']} minutes")


    if not all_routes:
        #the print statements don't make it to the front
        #end unless I wrap the string in st.write()
        st.write("No valid routes found.")