
import mysql.connector
import numpy as np
import csv
from datetime import datetime

def connectdb():
    mydb= mysql.connector.connect(
        host="localhost",user="root",
        passwd="admin1@",database="bpic2016")
    return mydb



def get_all_questions(mydb):
    fp =  open('resources/question_click.csv', mode='w',newline="\n", encoding="utf-8")
    fwriter = csv.writer(fp, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    
    fp_def =  open('resources/question_click_def.csv', mode='w',newline="\n", encoding="utf-8")
    fwriter_def = csv.writer(fp_def, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    
    cursor = mydb.cursor()
    query = ("""select customerid, agecategory, gender, contactdate, questionthemeid, 
                 questionsubthemeid, questiontopicid from questions 
                 where customerid in (select distinct customerid from clicks)""")

    cursor.execute(query)
    response = cursor.fetchall()
    count=0
    for row in response:
        count=count+1
        print(count)
        get_user_clicks(mydb, fwriter,fwriter_def, row)
    
    fp.close()
    fp_def.close()
    cursor.close()
    print('Done!')


def get_user_clicks(mydb, fwriter, fwriter_def, row):
    cursor = mydb.cursor()
    #get the last web session before the click
    query = ("""SELECT t.sessionid, t.timestamp , t.customerid, t.page_name
                FROM ( SELECT sessionid, MAX(timestamp) AS max_t
                FROM clicks where timestamp < %s and customerid= %s
                GROUP BY customerid) AS m INNER JOIN clicks AS t
                ON t.sessionid = m.sessionid""" )

    cursor.execute(query, (row[3],row[0],))
    response = cursor.fetchall()
    for clk in response:
        if(clk[3]=='vacatures_bij_mijn_cv'):
            fwriter_def.writerow([clk[0],clk[3], row])
        else:
            fwriter.writerow([clk[0],clk[3], row])
    cursor.close()
   

if __name__=='__main__':
    mydb = connectdb()
    get_all_questions(mydb)
    mydb.close()