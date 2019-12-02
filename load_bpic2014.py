'''get the input feature, create three y variables - impact, urgency and group. Train SVM and compute
get the confusion matrix values. Use this to show how - for the same agents
different levels of autonomy are required.'''

'''1. Create a database connection. 2. Create a join and a table that reads every interaction
and populates another table with values, group and if incident exists 3. Create a feature dictionary
4. Create a npz file 5. Read and create model 6. Print confusion matrix plot'''

import mysql.connector
import numpy as np, collections

import matplotlib.pyplot as plt
import pickle
import os
import pandas as pd
import csv
import datetime


RUN_MODE='TEST'

filePath_testcsv='resources/team_test.csv'
filePath_traincsv='resources/team_train.csv'
filePath_test_output='resources/test_output_small.csv'

def connectdb():
    mydb= mysql.connector.connect(
        host="localhost",user="username",
        passwd="password",database="bpi2014db")
    return mydb



def get_output_class(mydb):
    cursor = mydb.cursor()
    query = ("( select distinct team from activity)")
    cursor.execute(query)
    results = cursor.fetchall()
    team_dict = dict()
    count = 0
    for row in results:
        team_dict[row[0]] = count
        count += 1

    cursor.close()
    return team_dict


def process_data(mydb, citype, cisubtype, servcomp, team_dict):
    cursor = mydb.cursor()
    f = open(filePath_testcsv, 'w', newline='')
    ft = open(filePath_traincsv, 'w', newline='')
    writer = csv.writer(f)
    writer_train = csv.writer(ft)
    htuple=('citype,cisubtype, servcomp, impact, urgency, group, time, interaction,incident')
    writer.writerow(htuple)
    query = ("select a.citype, a.cisubtype, a.servcomp, a.impact, a.urgency, b.t, a.opentime, b.interactionid, b.incident"
             " from "
            "(select interactionid, ciname, citype, cisubtype, servcomp, impact, urgency, opentime from interaction "
             " where length(incident) > 3) as a, "
            "(select interactionid, incident, group_concat(distinct team) as t, count(distinct team) as x from activity "
             " where intype like 'Operator%' and team <>'TEAM9999' group by interactionid having x =1) as b "
            " where a.interactionid=b.interactionid order by a.opentime")

    cursor.execute(query)
    response = cursor.fetchall()
    num_rows = cursor.rowcount
    max_train = num_rows - int(num_rows*0.2)
    max_test = int(num_rows*0.2)
    num_feat = len(citype) + len(cisubtype) + len(servcomp)

    #creating training dataset
    train_XA=np.zeros((max_train, num_feat))
    train_YGr = np.zeros(max_train)

    # creating test dataset
    test_XA = np.zeros((max_test, num_feat))
    test_YGr = np.zeros(max_test)
    count=0
    test_count=0

    for row in response:
        #print(count)
        rtuple = (row[0], row[1],row[2])
        feat=get_feature(rtuple, citype,cisubtype,servcomp)
        if count < max_train:
            train_XA[count,:]=feat
            train_YGr[count] = int(team_dict[row[5]])
            writer_train.writerow(row)
        elif count >= max_train and test_count < max_test:
            test_XA[test_count, :] = feat
            test_YGr[test_count] = int(team_dict[row[5]])
            test_count += 1
            writer.writerow(row)
            print(test_count)
        count += 1

    cursor.close()

    print ('Total datapoints ', count, 'test', test_count, max_test , 'train', max_train)
    print('Done!')

def get_feature(rtuple, citype, cisubtype, servcomp):

    ci_type_feature = [0] * len(citype)
    ci_subtype_feature = [0] * len(cisubtype)
    ci_servcomp = [0] * len(servcomp)

    tdx = citype[rtuple[0]]
    ci_type_feature[tdx] = 1

    stdx = cisubtype[rtuple[1]]
    ci_subtype_feature[stdx] = 1

    cdx = servcomp[rtuple[2]]
    ci_servcomp[cdx] = 1

    feat =  ci_type_feature + ci_subtype_feature + ci_servcomp

    return feat


def get_dictionary(mydb, colname):
    cursor = mydb.cursor()
    query = "( select distinct " + colname + " from interaction)"
    cursor.execute(query)
    results = cursor.fetchall()
    col_dict = dict()
    count = 0
    for row in results:
        col_dict[row[0]] = count
        count += 1

    cursor.close()
    return col_dict


def get_labels(y_true, y_pred, team_dict):
    reverse_dict = {v: k for k, v in team_dict.items()}
    y_true1 = [reverse_dict[k] for k in y_true]
    y_pred1 = [reverse_dict[k] for k in y_pred]
    return y_true1, y_pred1

def update_performance(mydb):

    sql_insert_query = "update teamoutput set performance=%s where interactionid=%s and incident=%s"
    cursor = mydb.cursor()
    with open(filePath_test_output, 'r') as f:
        reader = csv.reader(f)
        count=0
        for row in reader:
            if(len(row[0])=='num'):
                continue
            count +=1
            print(row[8], row[9],row[12])
            cursor.execute(
               sql_insert_query,
                (row[12],row[8],row[9])
            )
    mydb.commit()
    print(cursor.rowcount, "Record inserted successfully into teamoutput table")

    cursor.close()


def update_experience(mydb):
    #first get the max tickets by a team and store in dict, get fscore
    #identify for each day # of tickets before that day. for 18 keep everything as 0
    # update exp, f1-score and level
    cursor = mydb.cursor()

    query = ("SELECT MAX(Total), citype, cisubtype, "
             "servcomp FROM (SELECT COUNT(*) AS total, citype, "
             "cisubtype, servcomp, month(opentime) as x FROM "
             "teamoutput GROUP BY citype, cisubtype, servcomp,x order by t) "
             "AS Results group by citype, cisubtype, servcomp")

    cursor.execute(query)
    max_dict=dict()
    results = cursor.fetchall()
    for row in results:
        key = row[1]+row[2]+row[3]
        max_dict[key]=row[0]*1.4

    # now read each day and update start with the date
    start_date = datetime.datetime.strptime('2014-02-17 00:00:00', "%Y-%m-%d %H:%M:%S")
    exp_query=("select count(*),citype, cisubtype, servcomp from " 
               "teamoutput where opentime>'2014-02-17 09:45:00' and opentime<%s "
                "group by citype, cisubtype, servcomp")

    update_query =("update teamoutput set experience=%s where citype=%s and "
                   " cisubtype=%s and servcomp=%s and day(opentime)=%s and month(opentime)=%s")

    for i in range(1,42):
        end_date = start_date + datetime.timedelta(days=i)
        print(end_date)
        cursor.execute(exp_query, (end_date,))
        res = cursor.fetchall()
        for srow in res:
            key = srow[1]+srow[2]+srow[3]
            maxv = max_dict[key]
            exp = srow[0]/maxv
            #update experience for that day and team values
            cursor.execute(update_query,(exp,srow[1],srow[2],srow[3],end_date.day, end_date.month))

    mydb.commit()
    cursor.close()


if __name__ == '__main__':
    if RUN_MODE=='DATA_EXTRACT':
        mydb = connectdb()

        citype = get_dictionary(mydb,'citype')
        cisubtype = get_dictionary(mydb, 'cisubtype')
        servcomp = get_dictionary(mydb,'servcomp')

        team_dict = get_output_class(mydb)
        process_data(mydb,citype, cisubtype, servcomp, team_dict)
        mydb.close()
    else:
        mydb=connectdb()
        update_experience(mydb)
        mydb.close()