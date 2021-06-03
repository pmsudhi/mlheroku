import streamlit as st
from streamlit_folium import folium_static
import json
import folium
import requests
import mimetypes
import http.client
import pandas as pd
from folium.plugins import HeatMap
from pandas.io.json import json_normalize
import plotly
import plotly.express as px

st.markdown("<h1 style='text-align: center; '><strong><u>Covid-19 Dashboard</u></strong></h1>", unsafe_allow_html=True)
st.markdown("## Data sourced from Johns Hopkins CSSE . Api Credit to [Kyle Redelinghuys](https://twitter.com/ksredelinghuys)")

# Now learn how to read data from an API, which is more practical scenarios in realworld
conn = http.client.HTTPSConnection("api.covid19api.com")
payload =''
headers={}
conn.request("GET","/summary",payload,headers) # this will get Summary information from every country
res = conn.getresponse()
data=res.read().decode('UTF-8') # Json Response
covid = json.loads(data) 
df=pd.DataFrame(covid['Countries']) # It returns 2 tables. One table represent Global Data and second table for each country. we would be doing on country specific

# Now we have to clean the data for our usage
covid_data=df.drop(columns=['CountryCode','Slug','Date','Premium'],axis=1) # we don't need these data
covid_data['ActiveCases'] = covid_data['TotalConfirmed']-covid_data['TotalRecovered'] #new column
covid_data['ActiveCases'] = covid_data['ActiveCases']-covid_data['TotalDeaths'] #calculate final active cases

#Second set of dataframe (ordered by total ascending cases )
dfn=covid_data.drop(columns=['NewConfirmed','NewDeaths','NewRecovered'],axis=1)
dfn = dfn.groupby('Country')['TotalConfirmed','TotalDeaths','TotalRecovered','ActiveCases'].sum().sort_values(by='TotalConfirmed',ascending=False)
dfn.style.background_gradient(cmap='Oranges') #Styling

#Third set of dataframe(by Max)
dfc = covid_data.groupby('Country')['TotalConfirmed','TotalDeaths','TotalRecovered','ActiveCases'].max().sort_values(by='TotalConfirmed',ascending=False).reset_index()

# Hmm.. dive into unknown territory. Overlay data on Map. basic reference from this article https://towardsdatascience.com/choropleth-maps-with-folium-1a5b8bcdd392

#Todo: Explore how we can reuse this when user changes selections. currently we are creating 3 diffrent objects. is it efficiant way??
m = folium.Map(tiles='Stamen Terrain',min_zoom=1.5) # need to explore more with diffrent tiles
url='https://raw.githubusercontent.com/python-visualization/folium/master/examples/data' #worddata in Json. is it GeoJson ??
country_shapes = f'{url}/world-countries.json'
folium.Choropleth(
geo_data=country_shapes,
min_zoom=2,
name='Covid-19',
data=covid_data,
columns=['Country','TotalConfirmed'],
key_on='feature.properties.name',
fill_color='YlOrRd',
nan_fill_color='black',
legend_name='Total Confirmed Cases',
).add_to(m)
    
m1 = folium.Map(tiles='Stamen Terrain',min_zoom=1.5)
url='https://raw.githubusercontent.com/python-visualization/folium/master/examples/data'
country_shapes = f'{url}/world-countries.json'
folium.Choropleth(
geo_data=country_shapes,
min_zoom=2,
name='Covid-19',
data=covid_data,
columns=['Country','TotalRecovered'],
key_on='feature.properties.name',
fill_color='YlOrRd',
nan_fill_color='black',
legend_name='Total Recovered Cases',
).add_to(m1)

m2 = folium.Map(tiles='Stamen Terrain',min_zoom=1.5)
url='https://raw.githubusercontent.com/python-visualization/folium/master/examples/data'
country_shapes = f'{url}/world-countries.json'
folium.Choropleth(
geo_data=country_shapes,
min_zoom=2,
name='Covid-19',
data=covid_data,
columns=['Country','ActiveCases'],
key_on='feature.properties.name',
fill_color='YlOrRd',
nan_fill_color='black',
legend_name='Active Cases',
).add_to(m2)

#we need geo cordinates. again googled and find this repo. But if the initial Json by folium itself could have been geoJson instead of normal Json, this additional step could have avoided. May be diffrent option be there. need to explore more
coordinates = pd.read_csv('https://raw.githubusercontent.com/VinitaSilaparasetty/covid-map/master/country-coordinates-world.csv')
covid_final = pd.merge(covid_data,coordinates,on='Country')
dfn
confirmed_tot = int(covid_data['TotalConfirmed'].sum())
deaths_tot = int(covid_data['TotalDeaths'].sum())
recovered_tot = int(covid_data['TotalRecovered'].sum())  
active_tot = int(covid_data['ActiveCases'].sum()) 
st.write('TOTAL CONFIRMED CASES FROM ALL OVER THE WORLD - ',confirmed_tot)
st.write('TOTAL DEATH CASES FROM ALL OVER THE WORLD - ',deaths_tot)
st.write('TOTAL RECOVERED CASES FROM ALL OVER THE WORLD - ',recovered_tot)
st.write('TOTAL ACTIVE CASES FROM ALL OVER THE WORLD - ',active_tot)

#Setup Side Bar
st.sidebar.markdown("<h1 style='text-align: center; '><strong><u>Covid-19 Dashboard</u></strong></h1>", unsafe_allow_html=True)
st.sidebar.subheader('Analysis through Map - Folium')
select = st.sidebar.selectbox('Choose Map Type',['Confirmed Cases','Recovered Cases','Active Cases','Deaths'],key='1')

if not st.sidebar.checkbox("Hide Map",True):
    
    if select == "Confirmed Cases": 
        folium_static(m)
    elif select == "Recovered Cases":
        folium_static(m1)
    elif select == "Active Cases":
        folium_static(m2)
    else:
           m2 = folium.Map(tiles='StamenToner',min_zoom=1.5)
           deaths=covid_final['TotalDeaths'].astype(float)
           lat=covid_final['latitude'].astype(float)
           long=covid_final['longitude'].astype(float)
          
           m2.add_child(HeatMap(zip(lat,long,deaths),radius=0)) # MAp overlay with additional layer
           folium_static(m2)

st.sidebar.subheader('Analysis through Bar Chart - Plotly')

select = st.sidebar.selectbox('Choose Bar Chart',['Confirmed Cases','Recovered Cases','Active Cases','Deaths'],key='2')
if not st.sidebar.checkbox("Hide Bar Chart",True):
        
    if select == "Confirmed Cases": 
        fig = px.bar(dfc.head(10), y='TotalConfirmed',x='Country',color='Country',height=400)
        fig.update_layout(title='Comparison of Total Confirmed Cases of 10 Most Affected Countries',xaxis_title='Country',yaxis_title='Total Confirmed Case',template="plotly_dark")
        st.plotly_chart(fig)
    elif select == "Recovered Cases":
        fig = px.bar(dfc.head(10), y='TotalRecovered',x='Country',color='Country',height=400)
        fig.update_layout(title='Comparison of Total Recovered of 10 Most Affected Countries',xaxis_title='Country',yaxis_title='Total Recovered',template="plotly_dark")
        st.plotly_chart(fig)
    elif select == "Active Cases":
        fig = px.bar(dfc.head(10), y='ActiveCases',x='Country',color='Country',height=400)
        fig.update_layout(title='Comparison of Active Cases of 10 Most Affected Countries',xaxis_title='Country',yaxis_title='Total Recovered',template="plotly_dark")
        st.plotly_chart(fig)
    else:
        fig = px.bar(dfc.head(10), y='TotalDeaths',x='Country',color='Country',height=400)
        fig.update_layout(title='Comparison of Total Deaths of 10 Most Affected Countries',xaxis_title='Country',yaxis_title='Total Deaths',template="plotly_dark")
        st.plotly_chart(fig)

# Intresting here to see the axis label is auto rotated beatifully, in the case of seaborn, we have to specify label rotation

st.markdown("## Assignment by Sudheesh PM: [source code](https://github.com/pmsudhi/mlheroku)")