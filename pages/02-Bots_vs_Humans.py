import streamlit as st
import pandas as pd
import altair as alt
from firebolt_connection import get_firebolt_connection
from datetime import date

st.set_page_config(layout="wide", page_title="Bots vs. Humans", page_icon="firebolt-logo.png")


def load_data():
  connection = get_firebolt_connection()
  cursor = connection.cursor()

  # this is an alternative for biggest committers using a cached materialized CTE
#  cursor.execute("""
#  WITH total_count AS (SELECT count(*) AS total_events FROM gharchive),
#     count_per_login AS MATERIALIZED (
#  SELECT actor_login, count(*) AS cnt
#  FROM gharchive
#  GROUP BY actor_login
#  ORDER BY cnt DESC
#  LIMIT 10)
#  SELECT count_per_login.actor_login as actor_login, count_per_login.cnt,
#       ROUND(100*(count_per_login.cnt/total_count.total_events), 2) AS ratio_in_percent
#  FROM total_count,count_per_login;
#  """);
#  most_active_logins = cursor.fetchall()

  # biggest committers
#  cursor.execute("""
#  WITH total_count AS (SELECT count(*) AS total_events FROM gharchive)
#  SELECT gharchive.actor_login, count(actor_login) AS cnt, 
#       ROUND(100*(count(actor_login)/total_count.total_events), 2) AS ratio_in_percent
#  FROM gharchive, total_count
#  GROUP BY actor_login, total_count.total_events
#  ORDER BY cnt DESC
#  LIMIT 10  
#  """)
#  most_active_logins = cursor.fetchall()

  # machines taking over?
  cursor.execute("""
    SELECT EXTRACT(YEAR FROM created_at) as year, payload_user_type, count(*) as cnt
    FROM gharchive
    WHERE payload_user_type IN ('Bot', 'User') AND event_type = 'IssueCommentEvent'
    GROUP BY year, payload_user_type
    ORDER by year, payload_user_type DESC;
  """)
  bots_vs_humans_comments = cursor.fetchall()

  # different query for the above calculation, but a lot slower currently
  #SELECT EXTRACT(YEAR FROM created_at) AS year, 
  #     SUM(CASE WHEN payload_user_type='User' THEN 1 ELSE 0 END) AS user_comments,
  #     SUM(CASE WHEN payload_user_type='Bot' THEN 1 ELSE 0 END) AS bot_comments
  #  FROM gharchive
  #  WHERE event_type = 'IssueCommentEvent' AND payload_user_type IN ('User', 'Bot')
  #  GROUP BY year
  #  ORDER by year;

  connection.close()

  return {
    'comments': bots_vs_humans_comments,
    #'most_active_logins': most_active_logins,
  }

st.title("Bots vs. Humans")

with st.spinner('Fetching data and rendering...'):
  data = load_data()

#st.header("Most active logins")
#st.subheader("by number of events, ratio compared to total events")
#st.dataframe(pd.DataFrame(data["most_active_logins"]))

st.header("Comments")

# dataframe needs some changes to fit our structure
df = pd.DataFrame(data["comments"], columns=['year', 'type', 'count'])
# change data frame to rename count to bot_count as columns
bots = df[df.type=='Bot'].rename(columns={'count':'bot_count'}).drop(columns=['type']).set_index('year')
# change data frame to rename count to user_count for users
users = df[df.type=='User'].rename(columns={'count':'user_count'}).drop(columns=['type']).set_index('year')
# join
df = bots.join(users, how='outer').fillna(0)
# calculate sum
df['total_count'] = df['bot_count'] + df['user_count']

labels=[str(x) for x in df.index.values]
st.line_chart(data=df, x=labels, y=['user_count', 'bot_count', 'total_count'])

