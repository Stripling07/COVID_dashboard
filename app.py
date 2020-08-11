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
#import warnings

from plotly.subplots import make_subplots


#warnings.filterwarnings('ignore')

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



States = [{'label': 'Alaska', 'value': 'AK'}, {'label': 'Alabama', 'value': 'AL'}, {'label': 'Arkansas', 'value': 'AR'}, {'label': 'American Samoa', 'value': 'AS'}, {'label': 'Arizona', 'value': 'AZ'}, {'label': 'California', 'value': 'CA'}, {'label': 'Colorado', 'value': 'CO'}, {'label': 'Connecticut', 'value': 'CT'}, {'label': 'District of Columbia', 'value': 'DC'}, {'label': 'Delaware', 'value': 'DE'}, {'label': 'Florida', 'value': 'FL'}, {'label': 'Georgia', 'value': 'GA'}, {'label': 'Guam', 'value': 'GU'}, {'label': 'Hawaii', 'value': 'HI'}, {'label': 'Iowa', 'value': 'IA'}, {'label': 'Idaho', 'value': 'ID'}, {'label': 'Illinois', 'value': 'IL'}, {'label': 'Indiana', 'value': 'IN'}, {'label': 'Kansas', 'value': 'KS'}, {'label': 'Kentucky', 'value': 'KY'}, {'label': 'Louisiana', 'value': 'LA'}, {'label': 'Massachusetts', 'value': 'MA'}, {'label': 'Maryland', 'value': 'MD'}, {'label': 'Maine', 'value': 'ME'}, {'label': 'Michigan', 'value': 'MI'}, {'label': 'Minnesota', 'value': 'MN'}, {'label': 'Missouri', 'value': 'MO'}, {'label': 'Northern Mariana Islands', 'value': 'MP'}, {'label': 'Mississippi', 'value': 'MS'}, {'label': 'Montana', 'value': 'MT'}, {'label': 'National', 'value': 'NA'}, {'label': 'North Carolina', 'value': 'NC'}, {'label': 'North Dakota', 'value': 'ND'}, {'label': 'Nebraska', 'value': 'NE'}, {'label': 'New Hampshire', 'value': 'NH'}, {'label': 'New Jersey', 'value': 'NJ'}, {'label': 'New Mexico', 'value': 'NM'}, {'label': 'Nevada', 'value': 'NV'}, {'label': 'New York', 'value': 'NY'}, {'label': 'Ohio', 'value': 'OH'}, {'label': 'Oklahoma', 'value': 'OK'}, {'label': 'Oregon', 'value': 'OR'}, {'label': 'Pennsylvania', 'value': 'PA'}, {'label': 'Puerto Rico', 'value': 'PR'}, {'label': 'Rhode Island', 'value': 'RI'}, {'label': 'South Carolina', 'value': 'SC'}, {'label': 'South Dakota', 'value': 'SD'}, {'label': 'Tennessee', 'value': 'TN'}, {'label': 'Texas', 'value': 'TX'}, {'label': 'Utah', 'value': 'UT'}, {'label': 'Virginia', 'value': 'VA'}, {'label': 'Virgin Islands', 'value': 'VI'}, {'label': 'Vermont', 'value': 'VT'}, {'label': 'Washington', 'value': 'WA'}, {'label': 'Wisconsin', 'value': 'WI'}, {'label': 'West Virginia', 'value': 'WV'}, {'label': 'Wyoming', 'value': 'WY'}]

#%%

def Roll_Avg(df, col, interval,shift = True) :
    """Calculate the rolling averages of interval duration of columns in df"""
    length = len(interval)
    
    for n in range(length) :
        # make new col called roll_col_interval
        new_col = 'roll_' + str(col) + '_'+ str(interval[n])
        if shift == False :
            df[new_col] = df.loc[:,col].rolling(interval[n]).mean()
        
        else :
            df[new_col] = df.loc[:,col].rolling(interval[n]).mean().shift(periods= - interval[n])


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

def Make_National_Cases():
    national_cases = df.groupby('date')['positiveIncrease'].sum().reset_index()
    
    national_cases['date'] = national_cases.date.dt.strftime('%Y-%m-%d')
    Roll_Avg(national_cases, 'positiveIncrease', [7],shift=False)
    
    # print(national_cases['date'], national_cases['positiveIncrease'])
    
    fig = go.Figure()
    
    fig.add_trace(
        go.Bar(x=national_cases['date'],
                y=national_cases['positiveIncrease'],
                marker=dict(color='slategray'),
                name='National Daily Case Increase'
                )
    )
    
    
    fig.add_trace(
        go.Line(x=national_cases['date'],
                y=national_cases['roll_positiveIncrease_7'],
                marker=dict(color='DodgerBlue'),
                line=dict(width=4),
                name='7-Day Average'
                )
        
    )
    
    
    fig.update_layout(title='National New Cases per Day',
                      title_x=0.5,
                      xaxis_title='Date',
                      yaxis_title='New Cases',
                      legend=dict(
                              yanchor="top",
                              y=0.99,
                              xanchor="left",
                              x=0.01)
    )     
    return fig

def Make_National_Deaths() :
    
    national_deaths = df.groupby('date')['deathIncrease'].sum().reset_index()
    
    national_deaths['date'] = national_deaths.date.dt.strftime('%Y-%m-%d')
    Roll_Avg(national_deaths, 'deathIncrease', [7],shift=False)
    
    # print(national_cases['date'], national_cases['positiveIncrease'])
    
    fig = go.Figure()
    
    fig.add_trace(
        go.Bar(x=national_deaths['date'],
                y=national_deaths['deathIncrease'],
                marker=dict(color='slategray'),
                name='National Daily Case Increase'
                )
    )
    
    
    fig.add_trace(
        go.Line(x=national_deaths['date'],
                y=national_deaths['roll_deathIncrease_7'],
                marker=dict(color='FireBrick'),
                line=dict(width=4),
                name='7-Day Average'
                )
        
    )
    
    
    fig.update_layout(title='National Deaths per Day',
                      title_x=0.5,
                      xaxis_title='Date',
                      yaxis_title='New Deaths',
                      legend=dict(
                              yanchor="top",
                              y=0.99,
                              xanchor="left",
                              x=0.01)
    )
    return fig
#%% Subset df with the state of choice


# Define function to do the subsetting of the data of selected state
def State_Subset(state_abbrev) :
    new_df = state_abbrev
    new_df = df[df['state']== state_abbrev]

    
    return new_df

#%%

def Make_State_Cases(state_of_choice):
    
    new_df = State_Subset(state_of_choice)
    interval = [7,20]#sets the intervals for the rolling averages
    state_cases = new_df.groupby('date')['positiveIncrease'].sum().reset_index()
    
    state_cases['date'] = state_cases.date.dt.strftime('%Y-%m-%d')
    Roll_Avg(state_cases, 'positiveIncrease', interval,shift=False)
    
    # print(national_cases['date'], national_cases['positiveIncrease'])
    
    fig = go.Figure()
    
    fig.add_trace(
        go.Bar(x=state_cases['date'],
                y=state_cases['positiveIncrease'],
                marker=dict(color='slategray'),
                name= str(state_of_choice) + ' Daily Case Increase'
                )
    )
    
    
    fig.add_trace(
        go.Line(x=state_cases['date'],
                y=state_cases['roll_positiveIncrease_7'],
                marker=dict(color='FireBrick'),
                line=dict(width=4),
                name='7-Day Average'
                )
        
    )
    
    fig.add_trace(
        go.Line(x=state_cases['date'],
                y=state_cases['roll_positiveIncrease_20'],
                marker=dict(color='DodgerBlue'),
                line=dict(width=4),
                name='20-Day Average'
                )
        
    )
    
    
    fig.update_layout(title=str(state_of_choice)+ ' New Cases per Day',
                      title_x=0.5,
                      xaxis_title='Date',
                      yaxis_title='New Cases',
                      legend=dict(
                              yanchor="top",
                              y=0.99,
                              xanchor="right",
                              x=0.5)
    )     
    return fig

def Make_State_Deaths(state_of_choice) :
    
    new_df = State_Subset(state_of_choice)
    interval = [7,20]#sets the intervals for the rolling averages
    state_deaths = new_df.groupby('date')['deathIncrease'].sum().reset_index()
    
    
    state_deaths['date'] = state_deaths.date.dt.strftime('%Y-%m-%d')
    Roll_Avg(state_deaths, 'deathIncrease', interval,shift=False)
    
    # print(national_cases['date'], national_cases['positiveIncrease'])
    
    fig = go.Figure()
    
    fig.add_trace(
        go.Bar(x=state_deaths['date'],
                y=state_deaths['deathIncrease'],
                marker=dict(color='slategray'),
                name= str(state_of_choice)+' Daily Case Increase'
                )
    )
    
    
    fig.add_trace(
        go.Line(x=state_deaths['date'],
                y=state_deaths['roll_deathIncrease_7'],
                marker=dict(color='FireBrick'),
                line=dict(width=4),
                name='7-Day Average'
                )
        
    )
    fig.add_trace(
        go.Line(x=state_deaths['date'],
                y=state_deaths['roll_deathIncrease_20'],
                marker=dict(color='DodgerBlue'),
                line=dict(width=4),
                name='20-Day Average'
                )
        
    )
    
    
    fig.update_layout(title=str(state_of_choice)+' Deaths per Day',
                      title_x=0.5,
                      xaxis_title='Date',
                      yaxis_title='New Deaths',
                      legend=dict(
                              yanchor="top",
                              y=0.99,
                              xanchor="right",
                              x=0.5)
    )
    return fig




#%%

def Make_Test_Plot(state_of_choice) :


    
    #subset the state of interest
    new_df = State_Subset(state_of_choice)
    interval = [7,20]#sets the intervals for the rolling averages
    
    ## Calculate the ROlling averages of features of interest
    Roll_Avg(new_df,'positiveIncrease',interval)
    Roll_Avg(new_df,'deathIncrease',interval)
    Roll_Avg(new_df,'PosPerTest',interval)
    Roll_Avg(new_df,'totalTestResultsIncrease',interval)
    
    #Create Plotly figure objects
    fig = go.Figure()
    fig = make_subplots(specs=[[{"secondary_y": True}]])#secondary y scale for infection rate
    
    # Add barplot of total tests per day
    fig.add_trace(
        go.Bar(x=new_df['date'],
               y=new_df['totalTestResultsIncrease'],
               marker=dict(color='slategray'),
               name='Total Tests',
               offsetgroup=0
               ),
        secondary_y=False
               
    )
    
    # Add barplotof positive tests per day
    fig.add_trace(
        go.Bar(x=new_df['date'],
               y=new_df['positiveIncrease'],
               marker=dict(color='Red'),
               name='Positive Tests',
               offsetgroup=0
               ),
        secondary_y=False
               
    )
    
    #Rolling average trace of testing 
    fig.add_trace(
        go.Line(x=new_df['date'],
                y=new_df['roll_totalTestResultsIncrease_7'],
                marker=dict(color='Black'),
                line=dict(width=2),
                name='7-Day Average'
                ),
        secondary_y=False
                
        
    )
    
    # Rolling average line of positive tests
    fig.add_trace(
        go.Line(x=new_df['date'],
                y=new_df['roll_positiveIncrease_7'],
                marker=dict(color='FireBrick'),
                line=dict(width=2),
                name='7-Day Average'
                ),
        secondary_y=False
                
        
    )
    
    # Scatter of d=Infection Rate
    fig.add_trace(
        go.Scatter(x=new_df['date'],
                y=new_df['PosPerTest'],
                mode='markers',
                marker=dict(color='Green',size=7),
                name='Infection Rate',
                ),
        secondary_y=True           
                
        
    )
    
    # Rolling average of Infection Rate
    fig.add_trace(
        go.Line(x=new_df['date'],
                y=new_df['roll_PosPerTest_7'],
                marker=dict(color='forestgreen'),
                line=dict(width=3),
                name='7-Day Average Infection Rate'
                ),
        secondary_y=True
    )
    
    # Setup the layout of legend and title 
    fig.update_layout(title= str(state_of_choice) + ' Tests and Infection Rate',
                      title_x=0.5, 
                      legend=dict(
                               yanchor="top",
                               y=0.99,
                               xanchor="left",
                               x=0.01,),
                      yaxis2_showgrid=False
                             
    )
    # Update Axis labels and range
    fig.update_yaxes(title_text="Tests", secondary_y=False)
    fig.update_yaxes(title_text="Infection Rate (%)",secondary_y=True, range=[0,50])   
    return fig


#%% Create  New Hospitalizations and ICU Cases with Infection Rate Overlay


        

    

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
            dcc.Graph(id='NatCase', figure= Make_National_Cases())
        ], className="six columns"
            ),

        html.Div([
            html.H3('National Deaths'),
            dcc.Graph(id='NatDeath', figure= Make_National_Deaths())
        ], className="six columns"),
    ], className="row"),
    
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
            dcc.Graph(id='StCase', figure= Make_State_Cases('UT'))
        ], className="six columns"
            ),

        html.Div([
            html.H3('Statewide New Deaths'),
            dcc.Graph(id='StDeath', figure= Make_State_Deaths('UT'))
            ], className="six columns"),
          ], className="row"
        ),
    
    html.Div([
        dcc.Graph(id='Test_Plot', figure = Make_Test_Plot('UT'))
    ]),
    
    html.Div([
        html.A('data from covid tracking project',href='https://covidtracking.com/')
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
        Make_Test_Plot(state_of_choice),
        
   
        Make_State_Cases(state_of_choice),
    
        Make_State_Deaths(state_of_choice)
        )
 




if __name__ == '__main__':
    app.run_server(debug=True,port=8020)
    
    
    
    
    