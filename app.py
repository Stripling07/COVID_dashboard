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
import datetime as dt
import requests
import json
from utils import *
from dash.dependencies import Input, Output

from plotly.subplots import make_subplots


States = Make_State_Dict()

df = Get_Data()

#%%
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.config['suppress_callback_exceptions'] = True
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
    dcc.Interval(id='get_data_interval',
                 interval = 1 * 30000,
                 n_intervals=0),
   
    html.H1(
        children='COVID Tracking',
        style={
            'textAlign': 'center',
            'color': colors['text'],
            'backgroundColor':colors['background2']
            }
        ),
    

   html.Div([
           html.H2('By: David R McKenna',
                  style={
                      'textAlign': 'left',
                      'color': colors['text'],
                      'fontSize':26
                
                 },
                  ),
           ]),
    html.Div(children = Make_Update(),
           id= 'update',
             style={
                 'textAlign': 'left',
                 'color': colors['background']
                 }
             ),          

   html.Div([  
           html.H5('Open to Opportunities',
                   style={
                       'textAlign': 'left',
                       'color': 'Green'}),
           html.A('Please ',
                       style={
                           'textAlign': 'left',
                           'color': 'Black'}),           
                
            html.A('Email ',href = 'mailto:david.r.mckenna.55@gmail.com',
                           style={
                               'textAlign': 'left',
                               'color': 'DodgerBlue',
                             }),
            html.A('or ',
                       style={
                           'textAlign': 'left',
                           'color': 'Black',
                           }),        
           html.A('LinkedIn',href = 'http://www.linkedin.com/in/david-r-mckenna',
                   style={
                       'textAlign': 'left',
                       'color': 'DodgerBlue'})        
           ]),
    


    
    html.H2('National Outlook:',style={
        'textAlign': 'left',
        'width' : '49%',
        'color': colors['text_sec']}
            ),
        
    html.Div([
        dcc.Graph(id='Nat', figure = Make_National(df))
        ],
        style={

            'height': 500,
            'width': 1200,
            "display": "block",
            "margin-left": "auto",
            "margin-right": "auto",
            'margin-bottom':'auto'
            }
        ),


    html.Div([
        dcc.Graph(id='R_B', figure = Make_R_B_National(df))
        ],
        style={

            'height': 500,
            'width': 1200,
            "display": "block",
            "margin-left": "auto",
            "margin-right": "auto",
            'margin-bottom':'auto'
            }
        ),

    
    html.Div([
        dcc.Graph(id='R_B_Sum', figure = Make_R_B_Sum(df))
        ],
        style={

            'height': 500,
            'width': 1200,
            "display": "block",
            "margin-left": "auto",
            "margin-right": "auto",
            'margin-bottom':'auto'
            }
        ),
    
        html.Div(id='Update_df', style={'display': 'none'}),
        
        
        html.H2('State Outlook:',style={
        'textAlign': 'left',
        'width' : '49%',
        'color': colors['text_sec']}
            ),

        
    html.H3('Please Select State',style={
        'textAlign': 'left',
        'width' : '49%',
        'color':colors['text']}        
        ),
    
    
    dcc.Dropdown(
        id='States Dropdown',
        options = States,
        value = 'UT',
        clearable =False,
        style={'width': '49%', 'padding': '0px 20px 20px 20px'}
       ),
    
    html.Div([
        dcc.Graph(id='State', figure = Make_State(df,'UT'))
        ],
        style={

            'height': 500,
            'width': 1200,
            "display": "block",
            "margin-left": "auto",
            "margin-right": "auto",
            'margin-bottom':'auto'
            }
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



@app.callback(
    Output('Update_df', 'children'),
    [Input('get_data_interval', 'n_intervals')])
def Update_Data(n):
     # an expensive query step
     updated_df = Get_Data()



     return updated_df.to_json(date_format='iso', orient='split')

@app.callback([
    Output('Nat','figure'),
    Output('R_B','figure'),
    Output('R_B_Sum','figure'),
    Output('update','children')],
    [Input('Update_df', 'children')])
def update_Nat(json_updated_df):
    dataset = json.loads(json_updated_df)
    dff = pd.read_json(json_updated_df, orient='split')
    
    return (
       
        Make_National(dff),
        
        Make_R_B_National(dff),
        
        Make_R_B_Sum(dff),
    
        Make_Update()
        )




@app.callback([
    Output('Test_Plot','figure'),
    Output('State','figure'), 
        ],
    [Input('States Dropdown', 'value'),
     Input('Update_df','children')]
    )


def Update_State_Plots(value,jsonified_cleaned_data):
    state_of_choice = value
    
    dataset = json.loads(jsonified_cleaned_data)
    dff = pd.read_json(jsonified_cleaned_data, orient='split')

    return (
       
        Make_Test_Plot(dff,state_of_choice),
        
        Make_State(dff,state_of_choice),
    
        )
 



if __name__ == '__main__':
    app.run_server(debug=True,port=8020)
    




    
    
    