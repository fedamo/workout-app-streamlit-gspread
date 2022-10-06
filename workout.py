####################################################################
####################################################################
####IMPORT DATA


######################################################################################################################################
##CONNECT TO GOOGLE SHEET#####
from __future__ import print_function
from optparse import Values
import streamlit as st
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import gspread
from google.oauth2 import service_account
from google.oauth2 import service_account
from gspread_dataframe import set_with_dataframe
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive


import pandas as pd
import numpy as np
import altair as alt
from datetime import date
import altair as alt

SCOPES = ['https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive',]
SERVICE_ACCOUNT_FILE = "keys.json"

creds = None
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gauth = GoogleAuth()
drive = GoogleDrive(gauth)

# The ID of spreadsheet.
SAMPLE_SPREADSHEET_ID = "1Hx7YDxcCeGdJGg3YdAdNj5i7l8Qn69fSICamJpffsVM"
gc = gspread.authorize(creds)
gs = gc.open_by_key(SAMPLE_SPREADSHEET_ID)
service = build("sheets", "v4", credentials=creds)

# Call the Sheets API
sheet = service.spreadsheets()

#Get Workout List
result = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range="Workout!A1:DQ9").execute()
values = result.get("values", [])
request = sheet.values().update(
    spreadsheetId=SAMPLE_SPREADSHEET_ID, range="Workout!A1:DQ9", valueInputOption="USER_ENTERED"
)

#Get Workout Tracking Data

result_tracking = sheet.values().get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range="Tracking!A1:F300").execute()
values_tracking = result_tracking.get("values", [])
request_tracking = sheet.values().update(
    spreadsheetId=SAMPLE_SPREADSHEET_ID, range="Tracking!A1:F300", valueInputOption="USER_ENTERED"
)

###Function to append dataframes to GS sheet
@st.cache(allow_output_mutation=True)
def append_df_to_gs(df, sheet_name:str):
    scopes = SCOPES
    credentials= creds
    gsc = gspread.authorize(credentials)
    sheet =  gc.open('Workout')
    params = {'valueInputOption': 'USER_ENTERED'}
    body = {'values': df.values.tolist()}
    sheet.values_append('Tracking!A1:F1', params, body)



df = pd.DataFrame(values)
df = df.convert_dtypes()
workout_set = df.T
workout_set.columns = workout_set.iloc[0]
workout_set = workout_set.drop(df.index[0])

 

######################################################################################################################################
######################################################################################################################################
##STREAMLIT APP##

import streamlit as st
import pandas as pd
import datetime
st.set_page_config(layout="centered", page_icon="🏋️‍♀️", page_title="Workout Logger")
st.title("🏋️‍♀️ Workout Tracker")
tab1, tab2, tab3 = st.tabs(["Logger", "Summary", "Owl"])
with tab1:
    
    

    @st.cache(allow_output_mutation=True)
    def get_data():
        return []


    d = st.date_input("Select date", date.today())
    workouts = workout_set["Workout"]
    workout_select = st.selectbox("Select your workout", workouts)




    buff, col, buff2, buff3 = st.columns(4)
    workout_choice = workout_set[workout_set["Workout"] == workout_select]


    workout_dict = {}
    reps ={}
    sets={}
    weight={}




    # buff.markdown('#')
    buff.subheader("Exercise")
    # col.markdown('#')
    col.subheader('Reps')
    # buff2.markdown('#')
    buff2.subheader("Sets")
    # buff3.markdown('#')
    buff3.subheader("Weight")

    m = st.markdown("""
    <style>
    div.stButton > button:first-child {
        background-color: #f0f2f6;
        color:#fof8ff;
        border-color: #ffffff;
    }

    </style>""", unsafe_allow_html=True)


    for i in workout_set.iloc[:0,-8:]:
        workout_dict[i] = workout_set[workout_set["Workout"] == workout_select][i].iloc[0]

    for i in workout_set.iloc[:0,-8:]:
        with buff:
            st.markdown("#")
            exercise = st.button(workout_dict[i])
        
        with col:
            # reps = st.markdown('#')
            reps[i] = st.number_input("", min_value=1, max_value=10, value=1, step=1, key = i+'a')
        
        with buff2:
            # sets = st.markdown('##')
            sets[i] = st.number_input("", min_value=1, max_value=10, value=1, step=1,key = i+'b')
        
        with buff3:
            # weight = st.markdown('##')
            weight[i] = st.number_input("", min_value=1, max_value=1000, value=5, step=5,key = i+'c')
            



    log=[]

    with col:
        st.markdown('#') 
        if st.button("Print Workout"):
            for i in workout_set.iloc[:0,-8:]:
                log.append({ "Exercise":workout_dict[i],"Reps": reps[i], "Sets": sets[i], "Weight": weight[i]})
    record = pd.DataFrame(log)
    st.write(record)
    record['Date'] = d.strftime('%m/%d/%Y')
    record['Workout'] = workout_select

    with buff2:
        st.markdown('#')
        st.button('Upload Workout', on_click = append_df_to_gs, args = (record,'Tracker'))
        
with tab2:
    df_tracking = pd.DataFrame(values_tracking)
    df_tracking.columns = df_tracking.iloc[0]
    df_tracking = df_tracking.iloc[1:]
    df_tracking = df_tracking.convert_dtypes()
    df_tracking['Reps']=df_tracking['Reps'].astype(int)
    df_tracking['Sets'] = df_tracking['Sets'].astype(int)
    df_tracking['Weight']=df_tracking['Weight'].astype(int)
    df_tracking['Score'] = df_tracking['Reps'] * df_tracking['Sets'] * df_tracking['Weight']
    total_score = df_tracking.groupby(df_tracking['Date'])['Score'].sum().reset_index(name ='Score')


    domain_x = [total_score.min(), total_score.max()]
    domain_y = [0, total_score["Score"].max() + 200]
    line_chart = (
    alt.Chart(total_score)
    .mark_line()
    .encode(
        x=alt.X("Date:T", axis=alt.Axis(format="%b %d", tickCount="day"), title=None),
        y=alt.Y("Score", scale=alt.Scale(domain=domain_y)),
        tooltip=alt.Tooltip("Date:T", title = 'Score')
    ).interactive()
    .properties(width=800)
    .configure_axis(grid=True)
    .properties(width=700, height=400)
    )
    st.altair_chart(line_chart, use_container_width=True)

with tab3:
    st.write(tracking_data)
