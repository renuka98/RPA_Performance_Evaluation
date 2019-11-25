import mysql.connector
from datetime import datetime
import csv

#this files reads each entry in the csv file and inserts into the database
#why code - the mysql workbench import doesn't work beyond 39k rows
def connectdb():
    mydb= mysql.connector.connect(
        host="localhost",user="root",
        passwd="admin1@",database="bpic2016")
    return mydb

def load_db(mydb):
    sql_insert_query = """ INSERT INTO questions (customerID, AgeCategory,
                            Gender, Office_U, Office_W, ContactDate,
                             ContactTimeStart, ContactTimeEnd, QuestionThemeID,
                              QuestionSubThemeID, QuestionTopicID) 
                           VALUES (%s, %s, %s, %s, %s, STR_TO_DATE(%s, '%d/%m/%Y'),
                           STR_TO_DATE(%s, '%H:%i:%S'),
                           STR_TO_DATE(%s, '%H:%i:%S'), %s,%s,%s)"""
    cursor = mydb.cursor()
    with open('resources/BPI2016_Question_trim.csv', 'r') as f:
        reader = csv.reader(f,delimiter=',')
        count=0
        for row in reader:
            count +=1
            print (row)
            print(count)
            #row[6]=row[6][:7]
            #row[7]=row[7][:7]
            cursor.execute(
               sql_insert_query,
                row
            )
    mydb.commit()
    print(cursor.rowcount, "Record inserted successfully into python_users table")

    cursor.close()
    mydb.close()
    print("connection is closed")



if __name__=='__main__':
    mydb=connectdb()
    load_db(mydb)
   

