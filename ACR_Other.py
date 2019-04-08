import pymysql
import os
import ELO
import ACR_Stats
import ACR_Globals

# Database connection
connection = pymysql.connect(host="localhost",user="root",passwd="",database=ACR_Globals.__DB_NAME)
__cursor = connection.cursor()

def create_and_alter_needed_tables():

	# Filters submissions
	__cursor.execute("SELECT * FROM submission WHERE status = 'AC' OR status = 'PE' GROUP BY user_id, problem_id, status ORDER BY user_id")
	rows = __cursor.fetchall()

	for r in rows:
		try:
			__cursor.execute(f"DELETE FROM submission WHERE user_id={r[2]} AND problem_id={r[1]} AND id > {r[0]}")
		except:
			pass

	# Creates a table that will store ELO scores for each user (Global ELO and ELO for each category)
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


	# Creates a table that will store ELO scores for each problem
	__cursor.execute("DROP TABLE IF EXISTS Problem_Scores")
	__cursor.execute(f"""CREATE TABLE IF NOT EXISTS Problem_Scores(
		problem_id INT PRIMARY KEY, 
		elo_global FLOAT(18,16) NOT NULL DEFAULT 8.0,
		FOREIGN KEY (problem_id) REFERENCES problem (internalId) ON DELETE CASCADE)""")

	__cursor.execute("SELECT internalId FROM problem GROUP BY internalId")
	for prb in __cursor.fetchall():
		__cursor.execute(f"INSERT INTO Problem_Scores(problem_id) VALUES({prb[0]})")

	# Adds 2 new columns to the 'submission' table (user_elo, problem_elo)
	# These store the resulting ELOs for both user and problem after a simulation
	try:
		__cursor.execute("ALTER TABLE submission ADD COLUMN user_elo FLOAT(18,16)")
		__cursor.execute("ALTER TABLE submission ADD COLUMN problem_elo FLOAT(18,16)")
	except:
		__cursor.execute("UPDATE submission SET user_elo=NULL")
		__cursor.execute("UPDATE submission SET problem_elo=NULL")

	connection.commit()

def train_subjects():
	current_fights = {}
	tries_per_couple = {}

	__cursor.execute("SELECT * FROM submission WHERE id <= {} ORDER BY id".format(ACR_Globals.__DB_SPLITTER))

	rows = __cursor.fetchall()
	for row in rows:
		print(0)
		subm_id = row[0]
		p_id = row[1]
		u_id = row[2]
		status = row[5]

		# Checks the Nº of tries
		if (u_id,p_id) not in tries_per_couple:
			tries_per_couple[(u_id,p_id)] = 1
		else:
			if tries_per_couple[(u_id,p_id)] == ACR_Globals.__MAX_TRIES:
				tries_per_couple[(u_id,p_id)] = 1
			else:
				tries_per_couple[(u_id,p_id)] += 1

		# Checks if the user hasn't switched problems
		if u_id not in current_fights:
			current_fights[u_id] = p_id

		# Checks all conditions that could trigger a simulation (AC/PE, Problem Switch and 10 tries)
		if current_fights[u_id] != p_id or status in ('AC', 'PE') or tries_per_couple[(u_id,p_id)] == ACR_Globals.__MAX_TRIES:

			if current_fights[u_id] != p_id:	current_fights[u_id] = p_id
			elif status in ('AC', 'PE'):		del current_fights[u_id]

			__cursor.execute("SELECT elo_global FROM User_Scores WHERE user_id = {}".format(u_id))
			old_user_elo = __cursor.fetchone()[0]

			__cursor.execute("SELECT elo_global FROM Problem_Scores WHERE problem_id = {}".format(p_id))
			old_problem_elo = __cursor.fetchone()[0]

			new_user_elo, new_problem_elo = ELO.simulate_with_tries(old_user_elo, old_problem_elo, status, tries_per_couple[(u_id,p_id)])

			__cursor.execute("SELECT categoryId FROM problemcategories WHERE problemId = {}".format(p_id))
			for cat in __cursor.fetchall():
				try:
					category = ACR_Globals.__CATEGORIES[cat[0]]
					__cursor.execute("SELECT {} FROM User_Scores WHERE user_id = {}".format(category, u_id))
					Old_Category_ELO = __cursor.fetchone()[0]
					New_Category_ELO, _ = ELO.simulate_with_tries(Old_Category_ELO, old_problem_elo, status, tries_per_couple[(u_id,p_id)])
					
					__cursor.execute("UPDATE User_Scores SET {} = {} WHERE user_id = {}".format(category, New_Category_ELO, u_id))
				except:
					pass

			__cursor.execute("UPDATE submission SET problem_elo = {}, user_elo = {} WHERE id = {}".format(new_problem_elo, new_user_elo, subm_id))
			__cursor.execute("UPDATE User_Scores SET elo_global = {} WHERE user_id = {}".format(new_user_elo, u_id))
			__cursor.execute("UPDATE Problem_Scores SET elo_global = {} WHERE problem_id = {}".format(new_problem_elo, p_id))

	connection.commit()

# Put on Stats
def users_evolution():
	if not os.path.exists("Users' ELO History"):
		os.makedirs("Users' ELO History")

	__cursor.execute("""SELECT user_id, count(id) FROM submission 
		WHERE id <= {}
		AND user_elo IS NOT NULL 
		AND user_id in {}
		GROUP BY user_id 
		ORDER BY user_id""".format(ACR_Globals.__DB_SPLITTER, str(ACR_Globals.__USRS_CHKD)))
	
	for usr in [r[0] for r in __cursor.fetchall()]:
		__cursor.execute("""SELECT * FROM submission 
		WHERE id <= {}
		AND user_id = {}
		AND user_elo IS NOT NULL 
		ORDER BY id""".format(ACR_Globals.__DB_SPLITTER, usr))
		
		y = [x[7] for x in __cursor.fetchall()]
		y.insert(0,8)

		ACR_Stats.show_line_plot(range(len(y)), y,f"Users' ELO History\\User({str(usr)})Evolution.png")

# Put on Stats
def problems_evolution():
	if not os.path.exists("Problems' ELO History"):
		os.makedirs("Problems' ELO History")

	__cursor.execute("""SELECT problem_id, count(id) FROM submission 
		WHERE id <= {}
		AND problem_id in {} 
		AND problem_elo IS NOT NULL 
		GROUP BY problem_id 
		ORDER BY problem_id""".format(ACR_Globals.__DB_SPLITTER, str(ACR_Globals.__PRBS_CHKD)))

	for prob in [r[0] for r in __cursor.fetchall()]:

		__cursor.execute("""SELECT * FROM submission 
			WHERE id <= {}
			AND problem_id = {}
			AND problem_elo IS NOT NULL 
			ORDER BY id""".format(ACR_Globals.__DB_SPLITTER, prob))

		y = [x[8] for x in __cursor.fetchall()]
		y.insert(0,8)

		ACR_Stats.show_line_plot(range(len(y)), y,f"Problems' ELO History\\Problem({str(prob)})Evolution.png")

# Put on Stats
def user_categories():
	if not os.path.exists("Categories' ELO"):
		os.makedirs("Categories' ELO")

	__cursor.execute("""SELECT * FROM User_Scores WHERE user_id in {}""".format(str(ACR_Globals.__USRS_CHKD)))

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

def main():
	#create_and_alter_needed_tables()
	#train_subjects()

	#ACR_Stats.print_elo_differences(__cursor)

	#users_evolution()
	#problems_evolution()
	#user_categories()
	connection.close()

if __name__== "__main__":
	main()