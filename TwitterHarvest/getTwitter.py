import requests
import couchdb
import json
import sys
import getopt
import re
from SentimentAnalysis.SentimentAnalysis import sentiment_polarity

auth=('readonly','ween7ighai9gahR6')

def get_geocoded_tweets(url, start_key='["r1h"]',end_key='["r1z"]', include_docs='true',reduce='false',skip='0',limit=None,auth=('readonly','ween7ighai9gahR6')):
    if limit==None:
        payload = {'include_docs': include_docs, 'start_key':start_key,'end_key':end_key, 'reduce': reduce, 'skip': skip}  # without limit
    else:
        payload = {'include_docs': include_docs, 'start_key':start_key,'end_key':end_key, 'reduce': reduce, 'skip': skip,'limit':limit}  # without limit

    auth=auth
    r=requests.get(url=url,params=payload,auth=auth)

    return r.json()

def put_data_into_couchdb(db_json,grid_json,start,end):

    with open(db_json) as f:
        db_info = f.read()
    db_info = json.loads(db_info)

    couch_host = db_info['host']
    couch_port = db_info['port']
    db_name = db_info['processed_database']
    raw_db_name = db_info['raw_database']
    source_url = db_info['tweet_source']
    host_and_port = "http://" + couch_host + ":" + str(couch_port)
    couch = couchdb.Server(host_and_port)
    try:
        db = couch.create(db_name)  # create db
    except:
        db = couch[db_name]  # existing

    try:
        raw_db = couch.create(raw_db_name)  # create db
    except:
        raw_db = couch[raw_db_name]  # existing

    with open(grid_json) as f:
        grids_str = f.read()
    suburbs = json.loads(grids_str)

    total_rows = get_geocoded_tweets(source_url,start_key=start,end_key=end, skip=0, limit=1, auth=auth)['total_rows']



    limit = 100
    for i in range(int(total_rows/limit)):
        skip=str(i*limit)
        geocoded_tweets = get_geocoded_tweets(source_url,start_key=start,end_key=end,skip=skip, limit=limit, auth=auth)
        process_data = []
        raw_data = []
        for tweet in geocoded_tweets['rows']:
            twitter = tweet['doc']
            raw_data.append(twitter)
            info = sentiment_polarity(twitter, suburbs)
            if info != None:
                process_data.append(info)
        raw_db.update(raw_data)
        db.update(process_data)

    geocoded_tweets = get_geocoded_tweets(skip=str(int(skip)+limit), limit=limit, auth=auth)
    db.update(geocoded_tweets['rows'])



def main(argv):
    db_json = 'db.json'
    grid_json = 'vic.json'
    start = 'r1h'
    end = 'r1r'
    try:
        opts, args = getopt.getopt(argv, "hs:e:d:g:", ['database=',"grid="])
    except getopt.GetoptError:
        print ("""-d <database_json>""")
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print ("""-d <database_json>""")
            sys.exit()
        elif opt in ("-s", "--start_geohash"):
            start = arg
        elif opt in ("-e", "--end_geohash"):
            end = arg
        elif opt in ("-d", "--database"):
            db_json = arg
        elif opt in ("-g", "--grid"):
            grid_json = arg

    start = '[\"'+start+'\"]'
    end = '[\"' + end + '\"]'
    put_data_into_couchdb(db_json,grid_json,start,end)


if __name__ == "__main__":
   main(sys.argv[1:])
