import math
import pymysql
import datetime
import time
import ELO
import ACR_Stats
import matplotlib.pyplot as plt

# Database connection
connection = pymysql.connect(host="localhost",user="root",passwd="",database="acr_dat")
__cursor = connection.cursor()

def create_and_fill_ELO_table(table, row_name, dicc):
	""" Creates 2 new Tables (users_elo & problems_elo) and inserts data from the given dictionary"""
	__cursor.execute(f"SHOW TABLES LIKE '{table}'")
	if __cursor.fetchone():	print(f'Table "{table}" already exists.')
	else: 
		__cursor.execute(f"""CREATE TABLE IF NOT EXISTS {table}({row_name} INT PRIMARY KEY, elo_score DECIMAL(6,4))""")
		for k,v in dicc.items():	
			__cursor.execute(f"INSERT INTO {table}({row_name},elo_score) values({k},{v})")
			connection.commit()

def train_subjects():
	""" Selects the submissions that are going to be used for the Training Half
	Gives every user / problem an initial ELO score of 8 [ELO scores go from 0 to 16]
	Iterates over a selection of rows (Training Half) and simulates a match, which will increase/decrease the ELO score of both User and Problem involved
	Then, it will fill 2 new tables with the Users/Problems and their respective ELO score
	"""
	users = {}
	problems = {}
	problem_already_solved = []

	# The Training Half includes all submissions from September 2015 and September 2017
	__cursor.execute("SELECT * from submission where submissionDate >= '2015-09-01 00:00:00' and submissionDate < '2017-09-01 00:00:00'")

	for row in __cursor.fetchall():
		if row[2] not in users:	users[row[2]] = 8
		if row[1] not in problems:	problems[row[1]] = 8

		# We check if the problem has already been solved by one specific user
		# This is so we can omit those submissions meant to reduce exeution time, memory use, fix presentation, etc
		if (row[2],row[1]) not in problem_already_solved:
			users[row[2]], problems[row[1]] = ELO.simulate(users[row[2]], problems[row[1]], row[5])
			if row[5] in ('AC', 'PE'): problem_already_solved.append((row[2],row[1]))


	create_and_fill_ELO_table('problems_elo', 'problem_id', problems)
	create_and_fill_ELO_table('users_elo', 'user_id', users)

def train_subjects_and_insert_elos():
	""" Selects the submissions that are going to be used for the Training Half
	Gives every user / problem an initial ELO score of 8 [ELO scores go from 0 to 16]
	Iterates over a selection of rows (Training Half) and simulates a match, which will increase/decrease the ELO score of both User and Problem involved
	Then, it will fill 2 new tables with the Users/Problems and their respective ELO score
	"""

	try:
		__cursor.execute("ALTER TABLE submission ADD COLUMN user_elo DECIMAL(6,4)")
		__cursor.execute("ALTER TABLE submission ADD COLUMN problem_elo DECIMAL(6,4)")
		connection.commit()
	except:
		print('ERROR')


	users = {}
	problems = {}
	problem_already_solved = []

	# The Training Half includes all submissions from September 2015 and September 2017
	__cursor.execute("SELECT * from submission where submissionDate >= '2015-09-01 00:00:00' and submissionDate < '2017-09-01 00:00:00'")

	for row in __cursor.fetchall():
		if row[2] not in users:	users[row[2]] = 8
		if row[1] not in problems:	problems[row[1]] = 8

		# We check if the problem has already been solved by one specific user
		# This is so we can omit those submissions meant to reduce execution time, memory use, fix the presentation, etc
		if (row[2],row[1]) not in problem_already_solved:
			if row[5] in ('AC', 'PE'): problem_already_solved.append((row[2],row[1]))
			users[row[2]], problems[row[1]] = ELO.simulate(users[row[2]], problems[row[1]], row[5])
			__cursor.execute(f"UPDATE submission SET problem_elo={problems[row[1]]}, user_elo={users[row[2]]} WHERE id={row[0]}")

	connection.commit()

def users_evolution():
	__cursor.execute("""SELECT user_id, count(id) from submission where submissionDate >= '2015-09-01 00:00:00' and submissionDate < '2017-09-01 00:00:00' 
		AND user_elo IS NOT NULL GROUP BY user_id HAVING count(id) > 5 ORDER BY RAND() LIMIT 15""")
	for u in [r[0] for r in __cursor.fetchall()]:
		__cursor.execute(f"SELECT * from submission where submissionDate >= '2015-09-01 00:00:00' and submissionDate < '2017-09-01 00:00:00' AND user_id={u} AND user_elo IS NOT NULL order by id")
		y = [x[7] for x in __cursor.fetchall()]
		ACR_Stats.show_line_plot(range(len(y)), y,f"Users' ELO History\\User({str(u)})Evolution.png")
		print(u)

def main():
	#train_subjects()
	#train_subjects_and_insert_elos()
	#ACR_Stats.print_elo_distribution(__cursor, 'users_elo', 'Users')
	#ACR_Stats.print_elo_distribution(__cursor, 'problems_elo', 'Problems')
	#ACR_Stats.print_elo_differences(__cursor, kind='perc')
	users_evolution()
	connection.close()

if __name__== "__main__":
	main()