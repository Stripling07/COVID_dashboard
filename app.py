#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 31 12:47:45 2020

@author: davidr.mckenna
"""

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import pandas as pd
import requests
from utils import *

from plotly.subplots import make_subplots



#%%  Load the data from covidtracking API

url = 'https://covidtracking.com/api/v1/states/daily.json'

r = requests.get(url)

json_data = r.json()

df = pd.json_normalize(json_data)

### Add calculate various relations of the data and add them as columns

df['DperP'] = df['death']/df['positive']  # Add columns Deaths per Positive case (DperP), Positive per Test (PosPerTest),  

df['PosPerTest']= df['positiveIncrease']/df['totalTestResultsIncrease']*100  # Positives per test in percentage

df['date'] = pd.to_datetime(df['date'], format = '%Y%m%d') #convert date to datetime object and set as index
df.set_index('date')

df = df[df['date'] >= '2020-03-01']
# Drop all unused columns. 

drop = ['pending',
        'hospitalizedCurrently', 'hospitalizedCumulative', 'onVentilatorCurrently',
        'onVentilatorCumulative','recovered', 'dataQualityGrade', 'lastUpdateEt',
        'dateModified','checkTimeEt', 'dateChecked','totalTestsViral', 'positiveTestsViral',
        'negativeTestsViral','positiveCasesViral', 'fips','posNeg','hash', 'commercialScore',
        'negativeRegularScore', 'negativeScore', 'positiveScore', 'score','grade']

df.drop(columns=drop, inplace=True)

    
# clean up bad data point, I found the actual number from NJ.gov website (was 1877)
df.loc[(df['date']=='2020-06-25') & (df['state']=='NJ'),'deathIncrease']=23

#list columns that shouldn't have negative values
greater_than_zero = ['positive', 'negative', 'inIcuCurrently',
       'inIcuCumulative', 'death', 'hospitalized', 'deathConfirmed',
       'deathProbable', 'positiveIncrease', 'negativeIncrease', 'total',
       'totalTestResults', 'totalTestResultsIncrease', 'deathIncrease',
       'hospitalizedIncrease', 'DperP', 'PosPerTest']

# Replace negative value with 0
for item in greater_than_zero :
    df[item].clip(lower=0,inplace=True)


df['yadda'] = df['inIcuCumulative'].shift(-1)

# iterate through the rows to calculate daily increase in ICU cases
for row in df.iterrows() :
    df['icuIncrease'] = df['inIcuCumulative'] - df['yadda']

df= States_Won(df)
df_election = State_Pop(df)

States = Make_State_Dict()



#%%
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
#application=app.server
server = app.server
colors = {
    'background': 'gray',
    'background2': 'lightgray',
    'text': 'DodgerBlue',
    'text_sec': 'FireBrick',
    'plot': 'gray'
    
}



    

#%%

app.layout = html.Div([ 
   
    html.H1(
        children='COVID Tracking',
        style={
            'textAlign': 'center',
            'color': colors['text'],
            'backgroundColor':colors['background2']
            }
        ),
    
    
    html.A('By: David R McKenna',href = 'http://www.linkedin.com/in/david-r-mckenna',
             style={
                 'textAlign': 'center',
                 'color': colors['text']
                 }
             ),
    
        html.H2('National Outlook:',style={
        'textAlign': 'left',
        'width' : '49%',
        'color': colors['text_sec']}
            ),
        
    html.Div([
        html.Div([
            html.H3('National Cases'),
            dcc.Graph(id='NatCase', figure= Make_National_Cases(df))
        ], className="six columns"
    ),

        html.Div([
            html.H3('National Deaths'),
            dcc.Graph(id='NatDeath', figure= Make_National_Deaths(df))
            ], className="six columns"),
            ], className="row"
        
    ),

    html.Div([
        html.Div([
            #html.H3('Red v Blue States Cases per 1M Population'),
            dcc.Graph(id='R_B_Case', figure= Make_R_B_National_Scaled_c(df_election))
        ], className="six columns"
    ),

        html.Div([
            #html.H3('Red v Blue States Deaths per 1M Population'),
            dcc.Graph(id='R_B_Death', figure= Make_R_B_National_Scaled_d(df_election))
            ], className="six columns"),
            ], className="row"
        
    ),

        html.H2('State Outlook:',style={
        'textAlign': 'left',
        'width' : '49%',
        'color': colors['text_sec']}
    ),

        
    html.H3('Please Select State',style={
        'textAlign': 'left',
        'width' : '49%'}        
        ),
    
    
    dcc.Dropdown(
        id='States Dropdown',
        options = States,
        value = 'UT',
        clearable =False,
        style={'width': '49%', 'padding': '0px 20px 20px 20px'}
       ),
    html.Div([
        html.Div([
            html.H3('Statewide New Cases'),
            dcc.Graph(id='StCase', figure= Make_State_Cases(df,'UT'))
        ], className="six columns"
            ),

        html.Div([
            html.H3('Statewide New Deaths'),
            dcc.Graph(id='StDeath', figure= Make_State_Deaths(df,'UT'))
            ], className="six columns"),
          ], className="row"
        ),
    
    html.Div([
        dcc.Graph(id='Test_Plot', figure = Make_Test_Plot(df,'UT'))
        ],
        style={

            'height': 500,
            'width': 900,
            "display": "block",
            "margin-left": "auto",
            "margin-right": "auto",
            'margin-bottom':'auto'
            }
        ),
    
    
    
    html.Div([
        html.Br(),
        html.A('Data from covid tracking project',href='https://covidtracking.com/')
            ],
             style={'text-align':'right',
                    'margin-top':200}
        
        ),
 
    html.Div([
        html.A('Source Code',href='https://github.com/Stripling07/COVID_dashboard')
            ],
             style={'text-align':'right'}
        
        )
])



@app.callback([
    dash.dependencies.Output('Test_Plot','figure'),
    dash.dependencies.Output('StCase','figure'), 
    dash.dependencies.Output('StDeath','figure')
        ],
    [dash.dependencies.Input('States Dropdown', 'value')]
    )

def Update_State_Plots(value):
    state_of_choice = value
    return (
        Make_Test_Plot(df,state_of_choice),
        
   
        Make_State_Cases(df,state_of_choice),
    
        Make_State_Deaths(df,state_of_choice)
        )
 




if __name__ == '__main__':
    app.run_server(debug=True,port=8020)
    
    
    
    
    