
# Mileage Run Finder

## Description

The **The Mileage Run Finder** is a Python application, an interactive tool tailored for frequent flyers who want to achieve their airline's frequent flyer status efficiently. By leveraging multi-objective optimization (MOO), the tool allows users to find and rank flight routes that align with their specific goals, such as maximizing miles, minimizing travel time, or limiting connections. Users can adjust weights and preferences to rerank routes interactively.
The tool bridges the gap in existing flight search platforms by addressing the specific needs of frequent flyers, empowering them to achieve their status goals while balancing time, cost, and convenience.

Key Features:
- Tailored for frequent flyers seeking to optimize routes for airline status goals.
- Incorporates multi-objective optimization for ranking routes based on user-defined priorities.
- Interactive and intuitive, enabling users to explore and analyze flight options comprehensively.

Data:
The CSV data used for this demo is a reduced dataset for demonstrating the app’s functionality. The original data source is an API (see instructions below for accessing it).

To access the API, follow these steps:
   - Visit https://www.goflightlabs.com/.
   - Sign up for an account and obtain an API key (requires a credit card).
   - Final data was gotten from this end point after preprocssing and cleaning -https://www.goflightlabs.com/flight-prices

## Installation
Download the Zip File:
Extract the downloaded zip file (team45final.zip) to access the project files.
### Prerequisites
- Ensure you have Python 3.8+ installed.

### Steps to Run the Code
- Extracted Zipped folder can be loaded into an IDE,preferably VSCode.

- Install project dependencies(streamlit==1.39.0 pandas==2.1.1 numpy==1.26.0 pydeck==0.9.1 scipy==1.14.1 geopy==2.4.1 requests==2.32.3).
 The code below run in the terminal will install all required Libraries.

    ```pip install -r requirements.txt```
## Execution

### Running the Application
- Navigate to the "Streamlit Website" path, where Main.py is located, and launch the website.
    ```
    cd CODE/"Streamlit Website"
    streamlit run Main.py
    ```

### Demo

App Features 

Left pane-
1.Airline - To select the desired airline( project scope limited to Delta)
2.Current MQD - Indicating the current status and the MQD.
3. Select Desire Tier - Where the desired class is selected
4. Choose Dates - Preferred Travel Date
5. Choose Origin - Preferred Destination
6. Maximum Layovers - Preferred Layovers
7. Sliders for customized route seacrh - Time weight to adjust for time, Cost weight to set cost as priority if its higher. 

Canvas
Top Route Results  - Shows the top route 
Map - Displays the graphic for the top three destinations(In blue) and the Origin(In Orange)




