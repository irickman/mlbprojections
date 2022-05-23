import pandas as pd
import pygsheets
from pybaseball import schedule_and_record,playerid_reverse_lookup, statcast, cache
from datetime import datetime, timedelta
import pytz
import time
import argparse
import sys
import os

def run_pull(start_date="2022-04-07"):
    creds=os.environ.get("GDRIVE_API_CREDENTIALS")
    yd=(datetime.now(pytz.timezone('US/Eastern')) - timedelta(1)).strftime('%Y-%m-%d')
    yr=int(start_date[:4])
    new_d=statcast(start_date,yd)
    new_data=new_d[new_d.events.notnull()]
    players_ids=playerid_reverse_lookup(new_data.batter.unique())
    id_df=players_ids[['name_last','name_first','key_mlbam']]
    new_names=new_data.merge(id_df, how = 'left',left_on='batter',right_on='key_mlbam')
    df=new_names
    df.drop_duplicates(inplace=True)
    df['hit']=df.events.apply(lambda x: 1 if x in ["single",'double','home_run','triple'] else 0)
    df['ab']=df.events.apply(lambda x: 0 if x in ['walk','hit_by_pitch',"caught_stealing_2b","pickoff_caught_stealing_2b",'pickoff_1b','catcher_interf','pickoff_caught_stealing_3b','pickoff_2b','pickoff_caught_stealing_home','caught_stealing_3b','caught_stealing_home',"sac_fly",'sac_bunt','sac_fly_double_play','sac_bunt_double_play'] else 1)
    df['player_team']=df.apply(lambda x: x.home_team if x.inning_topbot=="Bot" else x.away_team,axis=1)
    df['Opp']=df.apply(lambda x: x.away_team if x.inning_topbot=="Bot" else x.home_team,axis=1)
    df['Place']=df.apply(lambda x: "Home" if x.inning_topbot=="Bot" else "Away",axis=1)
    teams=df.player_team.unique()
    fixers={"WSH":"WSN","CWS":"CHW"}
    teams_fixed=[x if x not in fixers.keys() else fixers[x] for x in teams]

    team_schedule={}
    missed=[]
    for t in teams_fixed:
        try:
            d=schedule_and_record(yr,t)
            d['fix_date']=d.Date.str.replace("\(\d\)","").str.strip() + " " + str(yr)
            d['game_date']=pd.to_datetime(d.fix_date.apply(lambda x: datetime.strptime(x,"%A, %b %d %Y")).apply(lambda x: x.strftime("%Y-%m-%d")),infer_datetime_format=True)
            d['Place']=d.Home_Away.apply(lambda x: "Home" if x=="Home" else "Away")
            d2=d[d.game_date>yd][['Place',"Opp","game_date"]]
            team_schedule[t]=d2
        except ValueError:
            print(t)
            missed.append(t)

    df['name_last']=df['name_last'].str.capitalize()
    df['name_first']=df['name_first'].str.capitalize()
    df['player_name']=df.name_first + " " + df.name_last
    sm_df=df[['game_date','game_pk','hit','ab','Opp','Place','player_name','player_team','key_mlbam']]
    sm_df.sort_values(['player_name','game_date','game_pk'],inplace=True)
    trim_df=sm_df.groupby(['player_name','game_date','game_pk','Opp','Place','player_team','key_mlbam']).sum().reset_index()

    def player_df(player, d=trim_df):
        temp = d[d.player_name==player]
        temp=temp.sort_values(['game_date']).reset_index(drop=True)
        tm=temp.loc[len(temp)-1,'player_team']
        if tm in fixers.keys():
            sched=team_schedule[fixers[tm]]
        else:
            sched=team_schedule[tm]
        tdf= pd.concat([temp,sched])
        tdf.ab.fillna(0,inplace=True)
        tdf.hit.fillna(0,inplace=True)
        tdf.player_name.fillna(player,inplace=True)
        tdf.player_team.fillna(tm,inplace=True)
        return tdf

    master_df=player_df(trim_df.player_name.unique()[0])
    for p in trim_df.player_name.unique()[1:]:
        got=player_df(p)
        master_df=pd.concat([master_df,got])
    master_df.game_date=master_df.game_date.apply(lambda x: format(x,"%Y-%m-%d"))

    ## now write to the google sheet
    # #authorization
    gc = pygsheets.authorize(service_account_env_var =creds) 
    mlb = 'MLB At Bats'
    sh = gc.open(mlb)

    #select the first sheet
    wks = sh[0]

    wks.set_dataframe(master_df,(1,1))

def main():
    cache.enable()
    run_pull()

if __name__ == '__main__':
    main()

