#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 14 09:20:28 2020

@author: davidr.mckenna
"""

#%%

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import pandas as pd
import requests
import datetime as dt
from plotly.graph_objs.scatter.marker import Line


from plotly.subplots import make_subplots

color = {
    '7-day': 'Black',
    '20-day': 'Forestgreen',
    'Bar': 'slategray',
    'Bar2': 'Red',
    'Clinton': 'DodgerBlue',
    'Clinton7':'MidnightBlue',
    'Trump': 'Red',
    'Trump7': 'FireBrick'
    
}



#%%

def Make_Update():
    
    return [html.P('Last Updated: ' + str(dt.datetime.now().strftime("%m/%d/%y %H:%M (MT)")))]
#%%  Load the data from covidtracking API


def Get_Data():
    
   
    
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
    
    #clean up bad data point in RI 
    df.loc[(df['date']=='2020-08-08') & (df['state']=='RI'),'positiveIncrease']=0
    df.loc[(df['date']=='2020-08-10') & (df['state']=='RI'),'positiveIncrease']=196
    #Bad Data Point 8-26 in WI
    df.loc[(df['date']=='2020-08-26') & (df['state']=='WI'),'positiveIncrease']=768
    
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
    df= State_Pop(df)

   
    
    return df

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

# Define function to do the subsetting of the data of selected state
def State_Subset(df,state_abbrev, start_date = '2020-03-01') :
    new_df = state_abbrev
    new_df = df[df['state']== state_abbrev]
    new_df = new_df[new_df['date']>= start_date]
    
    return new_df




#%%

def Make_Test_Plot(df,state_of_choice) :
    
    
    #subset the state of interest
    new_df = State_Subset(df,state_of_choice)
    
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
               marker=dict(color=color['Bar']),
               name='Total Tests',
               legendgroup = 'Tests',
               offsetgroup=0
               ),
        secondary_y=False
               
    )
    
    # Add barplotof positive tests per day
    fig.add_trace(
        go.Bar(x=new_df['date'],
               y=new_df['positiveIncrease'],
               marker=dict(color=color['Bar2']),
               name='Positive Tests',
               offsetgroup=0,
               legendgroup = 'Cases'
               ),
        secondary_y=False
               
    )
    
    #Rolling average trace of testing 
    fig.add_trace(
        go.Line(x=new_df['date'],
                y=new_df['roll_totalTestResultsIncrease_7'],
                marker=dict(color='Black'),
                line=dict(width=2),
                name='7-Day Average',
                legendgroup = 'Tests'
                ),
        secondary_y=False
                
        
    )
    
    # Rolling average line of positive tests
    fig.add_trace(
        go.Line(x=new_df['date'],
                y=new_df['roll_positiveIncrease_7'],
                marker=dict(color='FireBrick'),
                line=dict(width=2),
                name='7-Day Average',
                legendgroup = 'Cases'
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
                legendgroup = 'Infection'
                ),
        secondary_y=True           
                
        
    )
    
    # Rolling average of Infection Rate
    fig.add_trace(
        go.Line(x=new_df['date'],
                y=new_df['roll_PosPerTest_7'],
                marker=dict(color='forestgreen'),
                line=dict(width=3),
                name='7-Day Average Infection Rate',
                legendgroup = 'Infection'
                ),
        secondary_y=True
    )
    
    # Setup the layout of legend and title 
    fig.update_layout(height=700, width=1000,title=dict(text= str(state_of_choice) + ' Tests and Infection Rate',
                      x=0.5,
                      font=dict(size=24)),
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
    fig.update_xaxes(title_text="Date")
    return fig

#%%


def Make_State(df,state_of_choice):
    
    
    new_df = State_Subset(df,state_of_choice)
    interval = [7,20]#sets the intervals for the rolling averages
    state_cases = new_df.groupby('date')['positiveIncrease'].sum().reset_index()
    state_deaths = new_df.groupby('date')['deathIncrease'].sum().reset_index()

    state_cases['date'] = state_cases.date.dt.strftime('%Y-%m-%d')
    Roll_Avg(state_cases, 'positiveIncrease', interval,shift=False)
    
    state_deaths['date'] = state_deaths.date.dt.strftime('%Y-%m-%d')
    Roll_Avg(state_deaths, 'deathIncrease', interval,shift=False)
    
    # print(national_cases['date'], national_cases['positiveIncrease'])
    
    fig = make_subplots(rows=1, cols=2,
                        subplot_titles = [str(state_of_choice)+ ' Cases per Day'
                                          , str(state_of_choice)+ ' Deaths per Day'],
                        )
    
    fig.add_trace(
        go.Bar(x=state_cases['date'],
                y=state_cases['positiveIncrease'],
                marker=dict(color=color['Bar']),
                legendgroup='Bars',
                name= str(state_of_choice) + ' Daily Increase'
                ),row=1,col=1
    )
    
    
    fig.add_trace(
        go.Line(x=state_cases['date'],
                y=state_cases['roll_positiveIncrease_7'],
                marker=dict(color=color['7-day']),
                line=dict(width=4),
                legendgroup='7Day',
                name='7-Day Average'
                ),row=1,col=1
        
    )
    
    fig.add_trace(
        go.Line(x=state_cases['date'],
                y=state_cases['roll_positiveIncrease_20'],
                marker=dict(color=color['20-day']),
                line=dict(width=2),
                legendgroup='20Day',
                name='20-Day Average'
                ),row=1,col=1
        
    )
    
    
    fig.update_yaxes(title_text="New Deaths")
 
    fig.update_xaxes(title_text="Date")
    
    fig.add_trace(
        go.Bar(x=state_deaths['date'],
                y=state_deaths['deathIncrease'],
                marker=dict(color=color['Bar']),
                legendgroup='Bars',
                showlegend=False,
                name= str(state_of_choice)+' Daily Deaths Increase'
                ),row=1,col=2
    )
    
    
    fig.add_trace(
        go.Line(x=state_deaths['date'],
                y=state_deaths['roll_deathIncrease_7'],
                marker=dict(color=color['7-day']),
                line=dict(width=2),
                legendgroup='7Day',
                showlegend=False,
                name='7-Day Average'
                ),row=1,col=2
        
    )
    fig.add_trace(
        go.Line(x=state_deaths['date'],
                y=state_deaths['roll_deathIncrease_20'],
                marker=dict(color=color['20-day']),
                line=dict(width=2),
                legendgroup='20Day',
                showlegend=False,
                name='20-Day Average'
                ),row=1,col=2
        
    )
    

    fig.update_layout(
                title=dict(text= str(state_of_choice) + " Cases and Deaths",
                font=dict(size=24),
                x = 0.5),
                xaxis_title='Date',
                yaxis_title='New Cases',                
                legend=dict(
                               yanchor="top",
                               y=0.99,
                               xanchor="left",
                               x=0.01,),
                    )         
    
    return fig
    

#%%

def Make_National(df) :

    national_cases = df.groupby('date')['positiveIncrease'].sum().reset_index()
    
    national_cases['date'] = national_cases.date.dt.strftime('%Y-%m-%d')
    Roll_Avg(national_cases, 'positiveIncrease', [7,20],shift=False)
    
    # print(national_cases['date'], national_cases['positiveIncrease'])
    fig = make_subplots(rows=1, cols=2,
                    subplot_titles = ['National Cases per Day'
                                          , 'National Deaths per Day'],
                        )
    
    fig.add_trace(
        go.Bar(x=national_cases['date'],
                y=national_cases['positiveIncrease'],
                marker=dict(color=color['Bar']),
                legendgroup = 'Bar',
                name='National Daily Case Increase'
                ),row=1,col=1
    )
    
    
    fig.add_trace(
        go.Line(x=national_cases['date'],
                y=national_cases['roll_positiveIncrease_7'],
                marker=dict(color=color['7-day']),
                line=dict(width=4),
                legendgroup = '7Avg',
                name='7-Day Average'
                ),row=1,col=1
        
    )

    fig.add_trace(
        go.Line(x=national_cases['date'],
                y=national_cases['roll_positiveIncrease_20'],
                marker=dict(color=color['20-day']),
                line=dict(width=2),
                legendgroup = '20Avg',
                name='20-Day Average'
                ),row=1,col=1
        
    )

    fig.update_yaxes(title_text="New Deaths")
 
    fig.update_xaxes(title_text="Date")


    national_deaths = df.groupby('date')['deathIncrease'].sum().reset_index()
    
    national_deaths['date'] = national_deaths.date.dt.strftime('%Y-%m-%d')
    Roll_Avg(national_deaths, 'deathIncrease', [7,20],shift=False)
    

    
    fig.add_trace(
        go.Bar(x=national_deaths['date'],
                y=national_deaths['deathIncrease'],
                marker=dict(color=color['Bar']),
                legendgroup = 'Bar',
                showlegend=False,
                
                name='National Daily Case Increase'
                ),row=1, col=2
    )
    
    
    fig.add_trace(
        go.Line(x=national_deaths['date'],
                y=national_deaths['roll_deathIncrease_7'],
                marker=dict(color= color['7-day']),
                showlegend=False,
                legendgroup = '7Avg',
                line=dict(width=4),
                name='7-Day Average'
                ),row=1, col=2
        
    )

    fig.add_trace(
        go.Line(x=national_deaths['date'],
                y=national_deaths['roll_deathIncrease_20'],
                marker=dict(color= color['20-day']),
                showlegend=False,
                legendgroup = '20Avg',
                line=dict(width=2),
                name='20-Day Average'
                ),row=1, col=2
        
    )
        
    fig.update_layout(
                title= dict(text ="National Cases & Deaths",
                font=dict(size=24),
                x = 0.5),
                xaxis_title='Date',
                yaxis_title='New Cases',                
                legend=dict(
                               yanchor="top",
                               y=0.99,
                               xanchor="left",
                               x=0.01,),
                    )

    return fig
    
#%%

def Make_State_Dict():
    
        
    States = [{'label': 'Alaska', 'value': 'AK'}, 
              {'label': 'Alabama', 'value': 'AL'}, 
              {'label': 'Arkansas', 'value': 'AR'},  
              {'label': 'Arizona', 'value': 'AZ'}, 
              {'label': 'California', 'value': 'CA'}, 
              {'label': 'Colorado', 'value': 'CO'}, 
              {'label': 'Connecticut', 'value': 'CT'}, 
              {'label': 'District of Columbia', 'value': 'DC'}, 
              {'label': 'Delaware', 'value': 'DE'}, 
              {'label': 'Florida', 'value': 'FL'}, 
              {'label': 'Georgia', 'value': 'GA'}, 
              {'label': 'Hawaii', 'value': 'HI'},
              {'label': 'Iowa', 'value': 'IA'},
              {'label': 'Idaho', 'value': 'ID'}, 
              {'label': 'Illinois', 'value': 'IL'},
              {'label': 'Indiana', 'value': 'IN'}, 
              {'label': 'Kansas', 'value': 'KS'}, 
              {'label': 'Kentucky', 'value': 'KY'}, 
              {'label': 'Louisiana', 'value': 'LA'}, 
              {'label': 'Massachusetts', 'value': 'MA'}, 
              {'label': 'Maryland', 'value': 'MD'}, 
              {'label': 'Maine', 'value': 'ME'}, 
              {'label': 'Michigan', 'value': 'MI'},
              {'label': 'Minnesota', 'value': 'MN'}, 
              {'label': 'Missouri', 'value': 'MO'}, 
              {'label': 'Mississippi', 'value': 'MS'}, 
              {'label': 'Montana', 'value': 'MT'}, 
              {'label': 'North Carolina', 'value': 'NC'}, 
              {'label': 'North Dakota', 'value': 'ND'}, 
              {'label': 'Nebraska', 'value': 'NE'}, 
              {'label': 'New Hampshire', 'value': 'NH'}, 
              {'label': 'New Jersey', 'value': 'NJ'}, 
              {'label': 'New Mexico', 'value': 'NM'}, 
              {'label': 'Nevada', 'value': 'NV'}, 
              {'label': 'New York', 'value': 'NY'}, 
              {'label': 'Ohio', 'value': 'OH'}, 
              {'label': 'Oklahoma', 'value': 'OK'}, 
              {'label': 'Oregon', 'value': 'OR'}, 
              {'label': 'Pennsylvania', 'value': 'PA'}, 
              {'label': 'Rhode Island', 'value': 'RI'}, 
              {'label': 'South Carolina', 'value': 'SC'}, 
              {'label': 'South Dakota', 'value': 'SD'}, 
              {'label': 'Tennessee', 'value': 'TN'}, 
              {'label': 'Texas', 'value': 'TX'}, 
              {'label': 'Utah', 'value': 'UT'}, 
              {'label': 'Virginia', 'value': 'VA'},
              {'label': 'Vermont', 'value': 'VT'}, 
              {'label': 'Washington', 'value': 'WA'},
              {'label': 'Wisconsin', 'value': 'WI'},
              {'label': 'West Virginia', 'value': 'WV'},
              {'label': 'Wyoming', 'value': 'WY'}]
    
    return States

#%%

def Make_R_B_National(df_election):

    
    df_election['positiveIncreasescale'] = df_election['positiveIncrease']/(df_election['Population']/1000000)
    df_election['deathIncreasescale'] = df_election['deathIncrease']/(df_election['Population']/1000000)
    Cases = df_election.groupby(['date','2016 Won By'])['positiveIncreasescale'].sum().unstack().reset_index()
    Deaths = df_election.groupby(['date','2016 Won By'])['deathIncreasescale'].sum().unstack().reset_index()
    
    Roll_Avg(Cases, 'States Won By Clinton', [7,20],shift=False)
    Roll_Avg(Deaths, 'States Won By Clinton', [7,20],shift=False)
    Roll_Avg(Cases, 'States Won By Trump', [7,20],shift=False)
    Roll_Avg(Deaths, 'States Won By Trump', [7,20],shift=False)

    
    
    fig = make_subplots(rows=1, cols=2,
                    subplot_titles = ['Cases per Day'
                                          , ' Deaths per Day'],
                        )


    fig.add_trace(
        go.Line(x=Cases['date'],
                y=Cases['States Won By Clinton'],
                marker=dict(color=color['Clinton']),
                line=dict(width=2),
                legendgroup = 'solidC',
                name='Won By Clinton'
                ),row=1,col=1
        )
    
    fig.add_trace(
        go.Line(x=Cases['date'],
                y=Cases['States Won By Trump'],
                marker=dict(color= color['Trump']),
                line=dict(width=2),
                legendgroup = 'solidT',
                name='Won By Trump'
                ),row=1,col=1
        )
    
    fig.add_trace(
        go.Line(x=Cases['date'],
                y=Cases['roll_States Won By Clinton_7'],
                marker=dict(color= color['Clinton7']),
                line=dict(width=2, dash ='dash'),
                legendgroup = 'dashC',
                name='Clinton 7-Day Avg.'
                ),row=1,col=1
        )

    fig.add_trace(
        go.Line(x=Cases['date'],
                y=Cases['roll_States Won By Trump_7'],
                marker=dict(color= color['Trump7']),
                line=dict(width=2, dash ='dash'),
                legendgroup = 'dashT',
                name='Trump 7-Day Avg'
                ),row=1,col=1
        )

    fig.update_yaxes(title_text="New Deaths")
 
    fig.update_xaxes(title_text="Date")

    
    fig.add_trace(
        go.Line(x=Deaths['date'],
                y=Deaths['States Won By Clinton'],
                marker=dict(color=color['Clinton']),
                line=dict(width=2),
                showlegend=False,
                legendgroup = 'solidC',
                name='Won By Clinton'
                ),row=1,col=2
        )


    fig.add_trace(
        go.Line(x=Deaths['date'],
                y=Deaths['States Won By Trump'],
                marker=dict(color=color['Trump']),
                line=dict(width=2),
                showlegend=False,
                legendgroup = 'solidT',
                name='Won By Trump'
                ),row=1,col=2
        )

    fig.add_trace(
        go.Line(x=Deaths['date'],
                y=Deaths['roll_States Won By Clinton_7'],
                marker=dict(color=color['Clinton7']),
                line=dict(width=2, dash ='dash'),
                showlegend=False,
                legendgroup = 'dashC',
                name='Clinton 7-Day Avg'
                ),row=1,col=2
        )

    fig.add_trace(
        go.Line(x=Deaths['date'],
                y=Deaths['roll_States Won By Trump_7'],
                marker=dict(color=color['Trump7']),
                line=dict(width=2, dash ='dash'),
                showlegend=False,
                legendgroup = 'dashT',
                name='Trump 7-Day Avg'
                ),row=1,col=2
        )

    fig.update_layout(
                title=dict(text="Red v Blue States Cases & Deaths Per 1M Population",
                font={'size':24},
                x = 0.5),
    
                xaxis_title='Date',
                yaxis_title='New Cases',                
                legend=dict(
                               yanchor="top",
                               y=0.99,
                               xanchor="left",
                               x=0.01,),
                    )
    return fig 


#%% 
def State_Pop(df) :

    State_Pop = {'AK': 731545.0,
     'AL': 4903185.0,
     'AR': 3017804.0,
     'AZ': 7278717.0,
     'CA': 39512223.0,
     'CO': 5758736.0,
     'CT': 3565287.0,
     'DC': 705749.0,
     'DE': 973764.0,
     'FL': 21477737.0,
     'GA': 10617423.0,
     'HI': 1415872.0,
     'IA': 3155070.0,
     'ID': 1787065.0,
     'IL': 12671821.0,
     'IN': 6732219.0,
     'KS': 2913314.0,
     'KY': 4467673.0,
     'LA': 4648794.0,
     'MA': 6892503.0,
     'MD': 6045680.0,
     'ME': 1344212.0,
     'MI': 9986857.0,
     'MN': 5639632.0,
     'MO': 6137428.0,
     'MS': 2976149.0,
     'MT': 1068778.0,
     'NC': 10488084.0,
     'ND': 762062.0,
     'NE': 1934408.0,
     'NH': 1359711.0,
     'NJ': 8882190.0,
     'NM': 2096829.0,
     'NV': 3080156.0,
     'NY': 19453561.0,
     'OH': 11689100.0,
     'OK': 3956971.0,
     'OR': 4217737.0,
     'PA': 12801989.0,
     'RI': 1059361.0,
     'SC': 5148714.0,
     'SD': 884659.0,
     'TN': 6829174.0,
     'TX': 28995881.0,
     'UT': 3205958.0,
     'VA': 8535519.0,
     'VT': 623989.0,
     'WA': 7614893.0,
     'WI': 5822434.0,
     'WV': 1792147.0,
     'WY': 578759.0}
    
    df['Population'] = df['state'].map(State_Pop)
    df_election = df[df['Population'].notna()] # Define df with states with no vote info (US Territories) removed

    return df_election

#%%

def Merge_Pop(df_to_merge):
    #Define names of columns to be used and dropped

    pop = State_Pop
    
    states = {
        'AK': '.Alaska',
        'AL': '.Alabama',
        'AR': '.Arkansas',
        'AS': '.American Samoa',
        'AZ': '.Arizona',
        'CA': '.California',
        'CO': '.Colorado',
        'CT': '.Connecticut',
        'DC': '.District of Columbia',
        'DE': '.Delaware',
        'FL': '.Florida',
        'GA': '.Georgia',
        'GU': '.Guam',
        'HI': '.Hawaii',
        'IA': '.Iowa',
        'ID': '.Idaho',
        'IL': '.Illinois',
        'IN': '.Indiana',
        'KS': '.Kansas',
        'KY': '.Kentucky',
        'LA': '.Louisiana',
        'MA': '.Massachusetts',
        'MD': '.Maryland',
        'ME': '.Maine',
        'MI': '.Michigan',
        'MN': '.Minnesota',
        'MO': '.Missouri',
        'MP': '.Northern Mariana Islands',
        'MS': '.Mississippi',
        'MT': '.Montana',
        'NA': '.National',
        'NC': '.North Carolina',
        'ND': '.North Dakota',
        'NE': '.Nebraska',
        'NH': '.New Hampshire',
        'NJ': '.New Jersey',
        'NM': '.New Mexico',
        'NV': '.Nevada',
        'NY': '.New York',
        'OH': '.Ohio',
        'OK': '.Oklahoma',
        'OR': '.Oregon',
        'PA': '.Pennsylvania',
        'PR': '.Puerto Rico',
        'RI': '.Rhode Island',
        'SC': '.South Carolina',
        'SD': '.South Dakota',
        'TN': '.Tennessee',
        'TX': '.Texas',
        'UT': '.Utah',
        'VA': '.Virginia',
        'VI': '.Virgin Islands',
        'VT': '.Vermont',
        'WA': '.Washington',
        'WI': '.Wisconsin',
        'WV': '.West Virginia',
        'WY': '.Wyoming'
        }

    #Subset the dataset with only the columns of interest, this speeds up the merge:

    # Subset the dataset with only the columns of interest, this speeds up the merge:
    #df_to_merge = df_to_merge[['state','date','positiveIncrease','deathIncrease','totalTestResultsIncrease']].reset_index()
    df_to_merge['full'] = df_to_merge['state'].map(states)

    # Merge datasets
    df_pop = pd.merge(df_to_merge,pop, left_on='full',right_on='State')
    df_pop.drop(columns=['full','State'],inplace=True)

    today = str(df_pop.date.max())
    # sort index by formated date
    df_pop['Date'] = pd.to_datetime(df_pop['date'], format= '%Y%m%d')
    df_pop.rename(columns={'2019': 'Population'},inplace=True)
    
    df_pop.sort_index(inplace=True)
    
    return df_pop

#%%

def States_Won(df):
    """# Adds a categorical column of who won each state in the 2016 election 
    and creates a new df_election without US Territories"""
    
    states_won = {
    'AK': 'Trump',
    'AL': 'Trump',
    'AR': 'Trump',
    'AZ': 'Trump',
    'CA': 'Clinton',
    'CO': 'Clinton',
    'CT': 'Clinton',
    'DC': 'Clinton',
    'DE': 'Clinton',
    'FL': 'Trump',
    'GA': 'Trump',
    'HI': 'Clinton',
    'IA': 'Trump',
    'ID': 'Trump',
    'IL': 'Clinton',
    'IN': 'Trump',
    'KS': 'Trump',
    'KY': 'Trump',
    'LA': 'Trump',
    'MA': 'Clinton',
    'MD': 'Clinton',
    'ME': 'Clinton',
    'MI': 'Trump',
    'MN': 'Clinton',
    'MO': 'Trump',
    'MS': 'Trump',
    'MT': 'Trump',
    'NC': 'Trump',
    'ND': 'Trump',
    'NE': 'Trump',
    'NH': 'Clinton',
    'NJ': 'Clinton',
    'NM': 'Clinton',
    'NV': 'Clinton',
    'NY': 'Clinton',
    'OH': 'Trump',
    'OK': 'Trump',
    'OR': 'Clinton',
    'PA': 'Trump',
    'RI': 'Clinton',
    'SC': 'Trump',
    'SD': 'Trump',
    'TN': 'Trump',
    'TX': 'Trump',
    'UT': 'Trump',
    'VA': 'Clinton',
    'VT': 'Clinton',
    'WA': 'Clinton',
    'WI': 'Trump',
    'WV': 'Trump',
    'WY': 'Trump'
    }
    # Add catagorical column that identifies if state was won by Trump or Clinton
    df['2016 Won By'] = df['state'].map(states_won)
    df_election = df[df['2016 Won By'].notna()] # Define df with states with no vote info (US Territories) removed
    df_election['2016 Won By'] = df_election['2016 Won By'].apply(lambda x: 'States Won By '+str(x))

    return df_election

#%%

def Make_R_B_Sum (df_election) :
    
    R_B_national_cases = df_election.groupby(['date','2016 Won By']).sum()['positiveIncrease'].unstack().reset_index()
    R_B_national_cases=R_B_national_cases.set_index('date').cumsum().reset_index()
    

    fig = make_subplots(rows=1, cols=2,
                    subplot_titles = ['R v B States Total Cases'
                                          , 'R v B States Total Deaths'],
                        )
    
    fig.add_trace(
        go.Line(x=R_B_national_cases['date'],
                y=R_B_national_cases['States Won By Clinton'],
                marker=dict(color= color['Clinton']),
                line=dict(width=4),
                legendgroup='Blue',
                name='Blue States Total'
                ),row=1 , col=1
    )
    
    fig.add_trace(
        go.Line(x=R_B_national_cases['date'],
                y=R_B_national_cases['States Won By Trump'],
                marker=dict(color= color['Trump']),
                line=dict(width=4),
                legendgroup='Red',
                name='Red States Total'
                ),row=1 , col=1
    )
    
       

    fig.update_yaxes(title_text="Total Deaths")
 
    fig.update_xaxes(title_text="Date")
    
    R_B_national_deaths = df_election.groupby(['date','2016 Won By']).sum()['deathIncrease'].unstack().reset_index()
    R_B_national_deaths= R_B_national_deaths.set_index('date').cumsum().reset_index()

    


    fig.add_trace(
        go.Line(x=R_B_national_deaths['date'],
                y=R_B_national_deaths['States Won By Clinton'],
                marker=dict(color= color['Clinton']),
                #showlegend=False,
                line=dict(width=4),
                legendgroup='Blue',
                showlegend=False,
                name='Blue States Deaths Total'
                ),row=1 , col=2
    )
    
    fig.add_trace(
        go.Line(x=R_B_national_deaths['date'],
                y=R_B_national_deaths['States Won By Trump'],
                marker=dict(color= color['Trump']),
                #showlegend=False,
                line=dict(width=4),
                legendgroup='Red',
                showlegend=False,
                name='Red States Deaths Total'
                ),row=1 , col=2
    )
        
    fig.update_layout(
                title= dict(text="Red v Blue States Total Cases & Deaths",
                        font={'size':24},
                        x = 0.5),
                xaxis_title='Date',
                yaxis_title='Total Cases',                
                legend=dict(
                               yanchor="top",
                               y=0.99,
                               xanchor="left",
                               x=0.01,),
                    )

    return fig 

#%%

def Make_Top_Ten(df) :

    df_top = df[['state','date','positiveIncrease','deathIncrease','totalTestResultsIncrease','Population']].reset_index()

    today = df_top.date.max()

    df_top['Date'] = pd.to_datetime(df_top['date'], format= '%Y%m%d')
    df_top.set_index(['state','Date'],inplace=True)
    df_top.sort_index(inplace=True)


    df_top['PosIncScaled'] = df_top['positiveIncrease'] / (df_top['Population']/1000000)
    df_top['TestIncScaled'] = df_top['totalTestResultsIncrease'] / (df_top['Population']/1000000)

    df_top['PosDiffScaled_m'] = df_top.groupby(level='state')['PosIncScaled'].apply(lambda x: (x.rolling(10).mean()))
    df_top['TestIncScaled_m'] = df_top.groupby(level='state')['TestIncScaled'].apply(lambda x: (x.rolling(10).mean()))



    largest = df_top[df_top['date']==today]['PosDiffScaled_m'].nlargest(10).astype(int)
    largest
    df_top_c = pd.DataFrame(largest).reset_index().sort_index(ascending=False)

    states = list(df_top_c.state)

    df_top.reset_index(inplace=True)
    df_top_t = df_top[(df_top['date']==today) & (df_top['state'].isin(states))]
    df_top_t = df_top_t.sort_values(by=['PosDiffScaled_m'],ascending=True)

    fig = make_subplots(rows=1, cols=2,
                    subplot_titles = ['States With Most Daily Cases (per Capita)'
                                          , 'Per Capita Testing'],
                        )
    
    fig.add_trace(
        go.Bar(x= df_top_c['PosDiffScaled_m'],
                y= df_top_c['state'],
                orientation = 'h',
                marker=dict(color=color['Clinton']),
                showlegend=False,
                name= '10-Day Avg Cases per Day'
                ),row=1,col=1)


 
    fig.update_xaxes(title_text="10-Day Avg Tests per 1M"),    

    
    fig.add_trace(
        go.Bar(x= df_top_t['TestIncScaled_m'],
                y= df_top_t['state'],
                marker=dict(color=color['20-day']),
                legendgroup = 'Bar',
                orientation = 'h',
                showlegend=False,
                
                name='10-Day Avg Tests per Day'
                ),row=1, col=2
    )
    

        
    fig.update_layout(
                title= dict(text ="Per Capita Hotspots",
                font=dict(size=24),
                x = 0.5),
                xaxis_title='10-Day Avg Cases per 1M'),
                
    
    return fig

#%%

def Make_National_Test_Plot(df) :
    
    national_test = df.groupby('date')['totalTestResultsIncrease'].sum().reset_index()

    national_test['date'] = national_test.date.dt.strftime('%Y-%m-%d')
    Roll_Avg(national_test, 'totalTestResultsIncrease', [7],shift=False)

    national_case = df.groupby('date')['positiveIncrease'].sum().reset_index()

    national_case['date'] = national_case.date.dt.strftime('%Y-%m-%d')
    Roll_Avg(national_case, 'positiveIncrease', [7],shift=False)

    National = national_case.merge(national_test, on = 'date')

    National['PosPerTest'] = (National['positiveIncrease']/National['totalTestResultsIncrease'])*100
    Roll_Avg(National, 'PosPerTest', [7],shift=False)
    
    #Create Plotly figure objects
    fig = go.Figure()
    fig = make_subplots(specs=[[{"secondary_y": True}]])#secondary y scale for infection rate
    
    # Add barplot of total tests per day
    fig.add_trace(
        go.Bar(x=National['date'],
               y=National['totalTestResultsIncrease'],
               marker=dict(color=color['Bar']),
               name='Total Tests',
               legendgroup = 'Tests',
               offsetgroup=0
               ),
        secondary_y=False
               
    )
    
    # Add barplotof positive tests per day
    fig.add_trace(
        go.Bar(x=National['date'],
               y=National['positiveIncrease'],
               marker=dict(color=color['Bar2']),
               name='Positive Tests',
               offsetgroup=0,
               legendgroup = 'Cases'
               ),
        secondary_y=False
               
    )
    
    #Rolling average trace of testing 
    fig.add_trace(
        go.Line(x=National['date'],
                y=National['roll_totalTestResultsIncrease_7'],
                marker=dict(color='Black'),
                line=dict(width=2),
                name='7-Day Average',
                legendgroup = 'Tests'
                ),
        secondary_y=False
                
        
    )
    
    # Rolling average line of positive tests
    fig.add_trace(
        go.Line(x=National['date'],
                y=National['roll_positiveIncrease_7'],
                marker=dict(color='FireBrick'),
                line=dict(width=2),
                name='7-Day Average',
                legendgroup = 'Cases'
                ),
        secondary_y=False
                
        
    )
    
    # Scatter of d=Infection Rate
    fig.add_trace(
        go.Scatter(x=National['date'],
                y=National['PosPerTest'],
                mode='markers',
                marker=dict(color='Green',size=7),
                name='Infection Rate',
                legendgroup = 'Infection'
                ),
        secondary_y=True           
                
        
    )
    
    # Rolling average of Infection Rate
    fig.add_trace(
        go.Line(x=National['date'],
                y=National['roll_PosPerTest_7'],
                marker=dict(color='forestgreen'),
                line=dict(width=3),
                name='7-Day Average Infection Rate',
                legendgroup = 'Infection'
                ),
        secondary_y=True
    )
    
    # Setup the layout of legend and title 
    fig.update_layout(height=700, width=1000,title=dict(text= 'National Tests and Infection Rate',
                      x=0.5,
                      font=dict(size=24)),
                      legend=dict(
                               yanchor="top",
                               y=0.99,
                               xanchor="left",
                               x=0.01,),
                      yaxis2_showgrid=False
                             
    )
    # Update Axis labels and range
    fig.update_yaxes(title_text="Tests", secondary_y=False)
    fig.update_yaxes(title_text="Infection Rate (%)",secondary_y=True, range=[0,30]) 
    fig.update_xaxes(title_text="Date")
    return fig




















