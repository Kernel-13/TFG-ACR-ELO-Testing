import pymysql
import sys
import datetime
import ACR_Stats

# Database connection
connection = pymysql.connect(host="localhost",user="root",passwd="",database="acr_dat")
__cursor = connection.cursor()

__cursor.execute("""SELECT * from submission where submissionDate >= '2015-09-01 00:00:00' and submissionDate < '2017-09-01 00:00:00' 
	AND user_id=5072 AND problem_id=136 AND id<114899
	AND user_elo IS NOT NULL ORDER BY id DESC LIMIT 9""")

tries = 1
for r in __cursor.fetchall(): 
	if r[5] in ('AC', 'PE'): break
	else: tries += 1

print('tries: ',tries)

connection.close()