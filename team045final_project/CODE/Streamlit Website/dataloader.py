#this python file contains all the functions associated with loading
#and manipulating data (for now, we can always change the structure if needed)

#also put dictionaries, lists, and other stuff containing information that will
#allow us to efficiently access data.

import pandas as pd
import time
import requests
import mileagerun_finder_oop as mrf
from datetime import timedelta

esi = pd.read_csv('data/entity_sky_id.csv')

airport_data = pd.read_csv('data/airport_data.csv')

#a dictionary containing the iata codes of the supported aiports

#the failure rate of the API is too high to do all of these: so we had to limit it to the top 15 cities

#airports    =   {
#                "BWI"	:	"Baltimore"       ,	"BOS"	:	"Boston"          ,	"BUF"	:	"Buffalo"         ,
#				"CHS"	:	"Charleston"      ,	"CVG"	:	"Cincinnati"      ,	"CLE"	:	"Cleveland"       ,	"CMH"	:	"Columbus"        , "DTW"	:	"Detroit"         ,	
#				"JAX"	:	"Jacksonville"    ,	"LAS"	:	"Las Vegas"       ,	"LAX"	:	"Los Angeles"     ,	"MEM"	:	"Memphis"         ,	"MIA"	:	"Miami"           ,
#				"MKE"	:	"Milwaukee"       ,	"MSP"	:	"Minneapolis"     ,	"BNA"	:	"Nashville"       ,	"MSY"	:	"New Orleans"     ,	"JFK"	:	"New York"        ,
#				"LGA"	:	"New York"        ,	"ORF"	:	"Norfolk"         ,	"OAK"	:	"Oakland"         ,	"OKC"	:	"Oklahoma City"   ,	"OMA"	:	"Omaha"           ,
#				"MCO"	:	"Orlando"         ,	"PHL"	:	"Philadelphia"    ,	"PHX"	:	"Phoenix"         ,	"PIT"	:	"Pittsburgh"      ,
#				"PDX"	:	"Portland"        ,	"RDU"	:	"Raleigh"         ,	"RIC"	:	"Richmond"        ,	"SMF"	:	"Sacramento"      ,	"SLC"	:	"Salt Lake City"  ,
#				"SAT"	:	"San Antonio"     ,	"SAN"	:	"San Diego"       ,	"SFO"	:	"San Francisco"   ,	"SJC"	:	"San Jose"        ,	"SNA"	:	"Santa Ana"       ,
#				"SEA"	:	"Seattle"         ,	"STL"	:	"St. Louis"       ,	"TPA"	:	"Tampa"           ,	"DCA"	:	"Washington, D.C.",	"IAD"	:	"Washington, D.C.",
#				"PBI"	:	"West Palm Beach" }

airports    =   {	"ATL" : "Atlanta"           , 
                    # "DFW" : "Dallas/Fort Worth" , 
                    # "DEN" : "Denver"           ,
	                # "ORD" : "Chicago O'Hare"    , 
                    "LAX" : "Los Angeles"       , 
                    # "CLT" : "Charlotte"        ,
	                "LAS" : "Las Vegas"         , 
                    "PHX" : "Phoenix"           , 
                    "MCO" : "Orlando"          ,
	                "SEA" : "Seattle"           , 
                    "MIA" : "Miami"             , 
                    # "IAH" : "Houston"          ,
	                "JFK" : "New York"          , 
                    # "EWR" : "Newark"            , 
                    "SFO" : "San Francisco"    ,
                    # "MDW" : "Chicago Midway"    , 
                    #"HOU" : "Houston"   
                    }


#reverse the key value pairs in case you need them for anything

airports_reversed = {v:k for (k,v) in airports.items()}



#geographic data for aiports: generated by doing an inner join from the aiports dictionary:
#this is nice, so if we reduce our scope later, all we have to do is change the 'airports' dictionary and the 
#geographic data will adjust accordingly:

airports_geo = pd   .DataFrame  (   
                                airports.keys(),columns=['IATA']
                                )\
                    .merge      (
                                right=airport_data,
                                how='inner',
                                left_on='IATA',
                                right_on='IATA'
                                )

def get_airport_coordinates(IATA,data=airports_geo):
    lat,lon = airports_geo[airports_geo['IATA']==IATA][['Latitude','Longitude']].values[0]
    return lat,lon





def get_flights(api_key , iata_origin, iata_destination, date):

    '''
    -----------------------------------------------------------------------------
    DOES:
    -----------------------------------------------------------------------------
    Gets all delta flights for a specific day using the arguments:

    api_key             :   your api key from flightlabs

    iata_origin         :   three-character airport code.  Remember, to limit
                            the scope of the project, it must be one of the ones
                            listed in the "airports" dictionary.

    iata_destination    :   three-character airport code. Same rules as above

    date                :   in YYYY-MM-DD format
    -----------------------------------------------------------------------------
    RETURNS:
    -----------------------------------------------------------------------------

    pandas dataframe with columns   :   'id'            'CarrierName'   'Origin' 
                                        'Destination'   'Departs'       'Arrives' 
                                        'Duration'      'Price'

    status_comp                     :   A boolean, if True is returned, then the
                                        API call returned a status of complete.
                                        
    NOTES REGARDING INCOMPLETE STATUS (from FlightLabs):
    
    If you receive incomplete results, please wait a moment and try your request
    again for the full information. Sometimes heavy queries may take longer to process.
    Please be aware that incomplete API calls will still be counted towards your API usage.
    '''
    ##################################################
    #Query the API:
    ##################################################     

    BASE_URL = "https://www.goflightlabs.com/retrieveFlights"

    params  =   {   
                #API Key:
                'access_key'    :   api_key,
                #ORIGIN:
                #skyid: 3 char code:
                'originSkyId'   :   iata_origin,
                #Entity ID:
                'originEntityId':   esi[esi['SkyId']==iata_origin]['EntityId'].to_string(index=False),
                #DESTINATION
                #skyid: 3 char code:
                'destinationSkyId'  :   iata_destination,
                #EntityID
                'destinationEntityId' : esi[esi['SkyId']==iata_destination]['EntityId'].to_string(index=False),
                #date
                'date' : date,
                #Cabin class premium economy: basic economy fares don't contribute to MQD on Delta!
                'cabinClass' : 'premium_economy'
                }

    response = requests.get(BASE_URL , params=params)

    ##################################################
    #Pre-Data Frame Organizing Stuff:
    ##################################################     

    #list output that will be turned into dataframe
    output  =   []


    #the structure of this loop is dictated by the json/api call
    #please review FlightLabs documentation if you need a refresher
    #on how a json arrives once you call:
    
    for each in response.json()['itineraries']:
        for leg in each['legs']:
            row =   {
                    'id'            :       leg['id'],
                    'CarrierName'   :       leg['carriers']['marketing'][0]['name'],
                    'Origin'        :       leg['origin']['id'],
                    'Destination'   :       leg['destination']['id'],
                    'Departs'       :       leg['departure'],
                    'Arrives'       :       leg['arrival'],
                    'Duration'      :       leg['durationInMinutes'],
                    'Price'         :       each['price']['raw']
                    }
            carrier_id  =   leg['carriers']['marketing'][0]['id']

            #-32385 is the identifier for delta.  Append to output
            #if and only if delta flight
            if carrier_id   ==  -32385:
                output.append(row)

    ##################################################
    #Create the output DataFrame:
    ##################################################     
    output_df = pd.DataFrame(output)
    
    if output:
        #convert to pandas datetime objects:
        output_df['Departs'] = pd.to_datetime(output_df['Departs'])
        output_df['Arrives'] = pd.to_datetime(output_df['Arrives'])
    
    status_comp = response.json()['context']['status']=='complete'
    return output_df , status_comp

def gather_flights(api_key, dates, codes, max_iter=1):
    """
    Loops through each combination of dates and airport codes to gather Delta flights data.
    Appends each successful result to a list of DataFrames.

    INPUT : LIST of DATES (must be a list, list of 1 is fine) YYYY-MM-DD
            LIST of AIRPORT CODES (IATA)
    
    Returns:
    --------
    List of DataFrames with gathered Delta flights data.
    """
    
    assert type(dates)==list, 'dates argument must be a list'
    assert type(codes)==list, 'codes argument must be a list'

    # List to store each DataFrame
    flights_dataframes = [] 

    #total combinations:
    combinations = [(a,b,c) for a in codes for b in codes for c in dates if a!=b]
    counter = 0

    for (x,y,z) in combinations:
        if counter > max_iter:
            break
        output,status = get_flights(api_key=api_key,
                                    iata_origin=x,
                                    iata_destination=y,
                                    date=z)
        
        flights_dataframes.append(output)

        counter +=1
        time.sleep(5)
    
    return pd.concat(flights_dataframes)

