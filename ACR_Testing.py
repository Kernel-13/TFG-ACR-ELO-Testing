import os
import math
import pymysql
import datetime
import time
import ELO
import ACR_Stats
import matplotlib.pyplot as plt

# Users checked: 1148, 1184, 1316, 1504, 1842, 1882, 1990, 2000, 2046, 206, 2107, 2127, 2134, 2245, 2269, 2372, 2504, 2568, 2659, 2724, 2726, 2727, 2856, 2863, 2880, 2951, 2976, 2979, 3058, 3062, 3098, 3147, 3175, 3197, 3223, 3286, 3580, 3591, 3690, 3699, 3711, 3788, 3843, 3886, 3983, 4047, 4055, 4221, 4225, 4246, 4312, 4324, 4352, 4442, 4444, 4458, 4488, 4501, 4582, 4788, 4790, 4793, 483, 4969, 5024, 5035, 5129, 5138, 5363, 5403, 542, 5501, 5521, 5550, 5561, 5708, 5718, 5731, 5766, 5841, 6125, 6210, 6230, 6243, 6286, 6335, 6348, 6356, 6457
# Problems checked: 10, 109, 117, 134, 150, 17, 178, 181, 19, 2, 224, 23, 233, 250, 258, 275, 282, 307, 316, 325, 331, 340, 39, 443, 465, 470, 506, 520, 533, 544, 561, 570, 575, 606, 613, 621, 629, 680, 699, 747, 748, 751, 806, 814, 834, 859, 861, 866, 923, 925, 955, 97

# Category Codes
categories = {
	25: 'elo_adhoc',
	26: 'elo_recorr',
	27: 'elo_search',
	28: 'elo_bin_srch',
	29: 'elo_sorting',
	30: 'elo_vrz',
	31: 'elo_dnmc',
	32: 'elo_dyv',
	33: 'elo_bk_trk',
	34: 'elo_space',
	43: 'elo_graph',
	44: 'elo_geo' 
}

# Database connection
connection = pymysql.connect(host="127.0.0.1",user="root",passwd="",database="tfg")
__cursor = connection.cursor()

def create_and_alter_needed_tables():
	__cursor.execute("DROP TABLE IF EXISTS User_Scores")
	__cursor.execute(f"""CREATE TABLE IF NOT EXISTS User_Scores(
		user_id INT PRIMARY KEY, 
		elo_global FLOAT(18,16) NOT NULL DEFAULT 8.0,
		elo_adhoc FLOAT(18,16) NOT NULL DEFAULT 8.0,
		elo_recorr FLOAT(18,16) NOT NULL DEFAULT 8.0,
		elo_search FLOAT(18,16) NOT NULL DEFAULT 8.0,
		elo_bin_srch FLOAT(18,16) NOT NULL DEFAULT 8.0,
		elo_sorting FLOAT(18,16) NOT NULL DEFAULT 8.0,
		elo_vrz FLOAT(18,16) NOT NULL DEFAULT 8.0,
		elo_dnmc FLOAT(18,16) NOT NULL DEFAULT 8.0,
		elo_dyv FLOAT(18,16) NOT NULL DEFAULT 8.0,
		elo_bk_trk FLOAT(18,16) NOT NULL DEFAULT 8.0,
		elo_space FLOAT(18,16) NOT NULL DEFAULT 8.0,
		elo_graph FLOAT(18,16) NOT NULL DEFAULT 8.0,
		elo_geo FLOAT(18,16) NOT NULL DEFAULT 8.0)""")
	# ADD CONSTRAINT 'fk_user_problem' FOREIGN KEY (user_id) REFERENCES user_table (user_table_id) ON DELETE CASCADE)

	__cursor.execute("SELECT user_id FROM submission GROUP BY user_id")
	for usr in __cursor.fetchall():
		__cursor.execute(f"INSERT INTO User_Scores(user_id) VALUES({usr[0]})")


	__cursor.execute("DROP TABLE IF EXISTS Problem_Scores")
	__cursor.execute(f"""CREATE TABLE IF NOT EXISTS Problem_Scores(
		problem_id INT PRIMARY KEY, 
		elo_global FLOAT(18,16) NOT NULL DEFAULT 8.0,
		FOREIGN KEY (problem_id) REFERENCES problem (internalId) ON DELETE CASCADE)""")

	__cursor.execute("SELECT internalId FROM problem GROUP BY internalId")
	for prb in __cursor.fetchall():
		__cursor.execute(f"INSERT INTO Problem_Scores(problem_id) VALUES({prb[0]})")

	try:
		__cursor.execute("ALTER TABLE submission ADD COLUMN user_elo FLOAT(18,16)")
		__cursor.execute("ALTER TABLE submission ADD COLUMN problem_elo FLOAT(18,16)")
	except:
		__cursor.execute("UPDATE submission SET user_elo=NULL")
		__cursor.execute("UPDATE submission SET problem_elo=NULL")

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
	__cursor.execute("SELECT * FROM submission where submissionDate >= '2015-09-01 00:00:00' and submissionDate < '2017-09-01 00:00:00'")

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
		__cursor.execute("ALTER TABLE submission ADD COLUMN user_elo FLOAT(18,16)")
		__cursor.execute("ALTER TABLE submission ADD COLUMN problem_elo FLOAT(18,16)")
		connection.commit()
	except:
		print('ERROR')


	users = {}
	problems = {}
	problem_already_solved = []

	# The Training Half includes all submissions from September 2015 and September 2017
	__cursor.execute("SELECT * FROM submission where submissionDate >= '2015-09-01 00:00:00' and submissionDate < '2017-09-01 00:00:00'")

	rows = __cursor.fetchall()
	for row in rows:
		if row[2] not in users:	users[row[2]] = 8
		if row[1] not in problems:	problems[row[1]] = 8

		# We check if the problem has already been solved by one specific user
		# This is so we can omit those submissions meant to reduce execution time, memory use, fix the presentation, etc
		if (row[2],row[1]) not in problem_already_solved:
			if row[5] in ('AC', 'PE'): problem_already_solved.append((row[2],row[1]))

			__cursor.execute(f"""SELECT * FROM submission 
							WHERE submissionDate >= '2015-09-01 00:00:00' 
							AND submissionDate < '2017-09-01 00:00:00' 
							AND user_id={row[2]} 
							AND problem_id={row[1]} 
							AND id<{row[0]}
							AND user_elo IS NOT NULL 
							ORDER BY id DESC 
							LIMIT 9""")

			tries = 1
			for r in __cursor.fetchall(): 
				if r[5] in ('AC', 'PE'): break
				else: tries += 1

			users[row[2]], problems[row[1]] = ELO.simulate(users[row[2]], problems[row[1]], row[5],tries)
			__cursor.execute(f"UPDATE submission SET problem_elo={problems[row[1]]}, user_elo={users[row[2]]} WHERE id={row[0]}")

	connection.commit()

def train_all_no_tries():
	cnt = 1
	problem_already_solved = []

	# We select all submissions (both halves)
	__cursor.execute("SELECT * FROM submission WHERE submissionDate >= '2015-09-01 00:00:00' AND submissionDate < '2018-09-01 00:00:00' ORDER BY id")

	rows = __cursor.fetchall()
	for row in rows:
		print(cnt, len(rows))
		cnt += 1

		subm_id = row[0]
		p_id = row[1]
		u_id = row[2]
		status = row[5]

		# Both User & Problem ELOs are retrieved from User_scores / Problem_Scores
		__cursor.execute(f"SELECT elo_global FROM User_Scores WHERE user_id={u_id}")
		old_user_elo = __cursor.fetchone()[0]

		__cursor.execute(f"SELECT elo_global FROM Problem_Scores WHERE problem_id={p_id}")
		old_problem_elo = __cursor.fetchone()[0]

		# We check if the problem has already been solved by one specific user
		# This is so we can omit those submissions meant to reduce execution time, memory use, fix the presentation, etc
		if (u_id,p_id) not in problem_already_solved:
			if status in ('AC', 'PE'): 
				problem_already_solved.append((u_id,p_id))

			# Calculates the New Global ELO
			new_user_elo, new_problem_elo = ELO.simulate_no_tries(old_user_elo, old_problem_elo, status)

			# Checks which categories include the problem 
			__cursor.execute(f"SELECT categoryId FROM problemcategories WHERE problemId={p_id}")
			for cat in __cursor.fetchall():
				
				try:
					category = categories[cat[0]]

					# We retrieve the old category ELO and use it to simulate a new fight
					__cursor.execute(f"SELECT {category} FROM User_Scores WHERE user_id = {u_id}")
					Old_Category_ELO = __cursor.fetchone()[0]
					New_Category_ELO, _ = ELO.simulate_no_tries(Old_Category_ELO, old_problem_elo, status)
					
					__cursor.execute(f"UPDATE User_Scores SET {category}={New_Category_ELO} WHERE user_id={u_id}")
				except:
					pass

			# Global ELOs get updated
			__cursor.execute(f"UPDATE submission SET problem_elo={new_problem_elo}, user_elo={new_user_elo} WHERE id={subm_id}")
			__cursor.execute(f"UPDATE User_Scores SET elo_global={new_user_elo} WHERE user_id={u_id}")
			__cursor.execute(f"UPDATE Problem_Scores SET elo_global={new_problem_elo} WHERE problem_id={p_id}")

	connection.commit()

def train_all_with_tries():
	cnt = 1
	problem_already_solved = []

	# We select all submissions (both halves)
	__cursor.execute("SELECT * FROM submission WHERE submissionDate >= '2015-09-01 00:00:00' AND submissionDate < '2018-09-01 00:00:00' ORDER BY id")

	rows = __cursor.fetchall()
	for row in rows:
		print(cnt, ' of ', len(rows), ' processed')
		cnt += 1

		subm_id = row[0]
		p_id = row[1]
		u_id = row[2]
		status = row[5]

		# Both User & Problem ELOs are retrieved from User_scores / Problem_Scores
		__cursor.execute(f"SELECT elo_global FROM User_Scores WHERE user_id={u_id}")
		old_user_elo = __cursor.fetchone()[0]

		__cursor.execute(f"SELECT elo_global FROM Problem_Scores WHERE problem_id={p_id}")
		old_problem_elo = __cursor.fetchone()[0]

		# We check if the problem has already been solved by one specific user
		# This is so we can omit those submissions meant to reduce execution time, memory use, fix the presentation, etc
		if (u_id,p_id) not in problem_already_solved:
			if status in ('AC', 'PE'): 
				problem_already_solved.append((u_id,p_id))

			__cursor.execute(f"""SELECT * FROM submission 
				WHERE user_id={u_id} 
				AND problem_id={p_id} 
				AND id<{subm_id} 
				AND user_elo IS NOT NULL
				ORDER BY id DESC 
				LIMIT 9""")

			tries = 1
			for r in __cursor.fetchall(): 
				if r[5] in ('AC', 'PE'): 
					break
				else: 
					tries += 1

			# Calculates the New Global ELO
			new_user_elo, new_problem_elo = ELO.simulate_with_tries(old_user_elo, old_problem_elo, status, tries)

			# Checks which categories include the problem 
			__cursor.execute(f"SELECT categoryId FROM problemcategories WHERE problemId={p_id}")
			for cat in __cursor.fetchall():
				
				try:
					category = categories[cat[0]]

					# We retrieve the old category ELO and use it to simulate a new fight
					__cursor.execute(f"SELECT {category} FROM User_Scores WHERE user_id = {u_id}")
					Old_Category_ELO = __cursor.fetchone()[0]
					New_Category_ELO, _ = ELO.simulate_with_tries(Old_Category_ELO, old_problem_elo, status, tries)
					
					__cursor.execute(f"UPDATE User_Scores SET {category}={New_Category_ELO} WHERE user_id={u_id}")
				except:
					pass

			# Global ELOs get updated
			__cursor.execute(f"UPDATE submission SET problem_elo={new_problem_elo}, user_elo={new_user_elo} WHERE id={subm_id}")
			__cursor.execute(f"UPDATE User_Scores SET elo_global={new_user_elo} WHERE user_id={u_id}")
			__cursor.execute(f"UPDATE Problem_Scores SET elo_global={new_problem_elo} WHERE problem_id={p_id}")

	connection.commit()

def train_all_elo_gain_plot():
	cnt = 1
	elo_differences = []
	user_gain = []
	problem_gain = []
	problem_already_solved = []

	# We select all submissions (both halves)
	__cursor.execute("""SELECT * FROM submission 
		WHERE submissionDate >= '2015-09-01 00:00:00' 
		AND submissionDate < '2018-09-01 00:00:00' 
		AND user_elo IS NOT NULL
		AND problem_elo IS NOT NULL
		ORDER BY id""")

	rows = __cursor.fetchall()
	for row in rows:

		if cnt == 10000:
			break

		print(cnt, len(rows))
		cnt += 1

		subm_id = row[0]
		p_id = row[1]
		u_id = row[2]
		status = row[5]
		old_user_elo = row[7]
		old_problem_elo = row[8]

		# We check if the problem has already been solved by one specific user
		# This is so we can omit those submissions meant to reduce execution time, memory use, fix the presentation, etc
		if (u_id,p_id) not in problem_already_solved:
			if status in ('AC', 'PE'): 
				problem_already_solved.append((u_id,p_id))

			# Calculates the New Global ELO
			x,y1,y2 = ELO.simulate_no_tries(old_user_elo, old_problem_elo, status)

			#if y1 != 0 and y2 != 0:
			elo_differences.append(x)
			user_gain.append(y1)
			problem_gain.append(y2)

	ACR_Stats.show_ELO_gain(elo_differences, user_gain, problem_gain,x_label = "USER ELO - PROBLEM ELO", y_label="OLD ELO - NEW ELO", title="ELO Gain For Different ELO Differences")
	#ACR_Stats.show_scatter(elo_differences, user_gain, "User Gain",x_label = "USER ELO - PROBLEM ELO", y_label="OLD ELO - NEW ELO", title="ELO Gain For Different ELO Differences")
	#ACR_Stats.show_scatter(elo_differences, problem_gain, "Problem Gain",x_label = "USER ELO - PROBLEM ELO", y_label="OLD ELO - NEW ELO", title="ELO Gain For Different ELO Differences")

def users_evolution():
	if not os.path.exists("Users' ELO History"):
		os.makedirs("Users' ELO History")

	__cursor.execute("""SELECT user_id, count(id) FROM submission 
		WHERE submissionDate >= '2015-09-01 00:00:00' 
		AND submissionDate < '2017-09-01 00:00:00' 
		AND user_elo IS NOT NULL 
		AND user_id in (1148, 1184, 1316, 1504, 1842, 1882, 1990, 2000, 2046, 206, 2107, 2127, 2134, 2245, 2269, 2372, 2504, 2568, 2659, 2724, 2726, 2727, 2856, 2863, 2880, 2951, 2976, 2979, 3058, 3062, 3098, 3147, 3175, 3197, 3223, 3286, 3580, 3591, 3690, 3699, 3711, 3788, 3843, 3886, 3983, 4047, 4055, 4221, 4225, 4246, 4312, 4324, 4352, 4442, 4444, 4458, 4488, 4501, 4582, 4788, 4790, 4793, 483, 4969, 5024, 5035, 5129, 5138, 5363, 5403, 542, 5501, 5521, 5550, 5561, 5708, 5718, 5731, 5766, 5841, 6125, 6210, 6230, 6243, 6286, 6335, 6348, 6356, 6457) 
		GROUP BY user_id 
		ORDER BY user_id""")
	
	for u in [r[0] for r in __cursor.fetchall()]:

		__cursor.execute(f"""SELECT * FROM submission 
		WHERE submissionDate >= '2015-09-01 00:00:00' 
		AND submissionDate < '2017-09-01 00:00:00' 
		AND user_id={u} 
		AND user_elo IS NOT NULL 
		ORDER BY id""")
		
		y = [x[7] for x in __cursor.fetchall()]
		y.insert(0,8)

		ACR_Stats.show_line_plot(range(len(y)), y,f"Users' ELO History\\User({str(u)})Evolution.png")
		#print(u)

def problems_evolution():
	if not os.path.exists("Problems' ELO History"):
		os.makedirs("Problems' ELO History")

	__cursor.execute("""SELECT problem_id, count(id) FROM submission 
		WHERE submissionDate >= '2015-09-01 00:00:00' 
		AND submissionDate < '2017-09-01 00:00:00' 
		AND problem_elo IS NOT NULL 
		AND problem_id in (10, 109, 117, 134, 150, 17, 178, 181, 19, 2, 224, 23, 233, 250, 258, 275, 282, 307, 316, 325, 331, 340, 39, 443, 465, 470, 506, 520, 533, 544, 561, 570, 575, 606, 613, 621, 629, 680, 699, 747, 748, 751, 806, 814, 834, 859, 861, 866, 923, 925, 955, 97) 
		GROUP BY problem_id 
		ORDER BY problem_id""")

	for p in [r[0] for r in __cursor.fetchall()]:

		__cursor.execute(f"""SELECT * FROM submission 
			WHERE submissionDate >= '2015-09-01 00:00:00' 
			AND submissionDate < '2017-09-01 00:00:00' 
			AND problem_id={p} 
			AND problem_elo IS NOT NULL 
			ORDER BY id""")

		y = [x[8] for x in __cursor.fetchall()]
		y.insert(0,8)

		ACR_Stats.show_line_plot(range(len(y)), y,f"Problems' ELO History\\Problem({str(p)})Evolution.png")
		#print(p)

def user_categories():
	if not os.path.exists("Categories' ELO"):
		os.makedirs("Categories' ELO")

	__cursor.execute("""SELECT * FROM User_Scores WHERE user_id in (1148, 1184, 1316, 1504, 1842, 1882, 1990, 2000, 2046, 206, 2107, 2127, 2134, 2245, 2269, 2372, 2504, 2568, 2659, 2724, 2726, 2727, 2856, 2863, 2880, 2951, 2976, 2979, 3058, 3062, 3098, 3147, 3175, 3197, 3223, 3286, 3580, 3591, 3690, 3699, 3711, 3788, 3843, 3886, 3983, 4047, 4055, 4221, 4225, 4246, 4312, 4324, 4352, 4442, 4444, 4458, 4488, 4501, 4582, 4788, 4790, 4793, 483, 4969, 5024, 5035, 5129, 5138, 5363, 5403, 542, 5501, 5521, 5550, 5561, 5708, 5718, 5731, 5766, 5841, 6125, 6210, 6230, 6243, 6286, 6335, 6348, 6356, 6457)""")

	for row in __cursor.fetchall():
		categories_data = {
			'Ad-hoc': row[2],
			'Recorridos': row[3],
			'Búsqueda': row[4],
			'Búsqueda\n Binaria': row[5],
			'Ordenación': row[6],
			'Algoritmos\n voraces': row[7],
			'Programación\n dinámica': row[8],
			'Divide y\n vencerás': row[9],
			'Búsqueda exhaustiva,\n vuelta atrás': row[10],
			'Búsqueda en el espacio\n de soluciones': row[11],
			'Grafos': row[12],
			'Geometría': row[13]
		}
		ACR_Stats.show_spider_chart(chart_data=categories_data,filename=f"Categories' ELO\\User {str(row[0])} Categories.png")
		#print('User: ', row[0])

def main():
	create_and_alter_needed_tables()

	train_all_with_tries()
	#train_all_no_tries()

	ACR_Stats.print_elo_distribution(__cursor, 'Users', '2017-09-01 00:00:00', '2018-09-01 00:00:00')
	ACR_Stats.print_elo_distribution(__cursor, 'Problems', '2017-09-01 00:00:00', '2018-09-01 00:00:00')
	
	#ACR_Stats.print_elo_differences(__cursor)
	#ACR_Stats.print_tries_till_solved(__cursor, '2015-09-01 00:00:00', '2016-09-01 00:00:00')

	users_evolution()
	problems_evolution()
	#user_categories()

	connection.close()

if __name__== "__main__":
	main()