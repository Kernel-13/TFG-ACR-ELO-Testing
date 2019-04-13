import pymysql
import ELO
import ACR_Stats
import ACR_Globals
from tqdm import tqdm

def CREATE_AND_ALTER_NEEDED_TABLES():

	# Filters submissions
	ACR_Globals.__CURSOR.execute("SELECT * FROM submission WHERE status = 'AC' OR status = 'PE' GROUP BY user_id, problem_id, status ORDER BY user_id")
	rows = ACR_Globals.__CURSOR.fetchall()

	for r in rows:
		try:
			ACR_Globals.__CURSOR.execute(f"DELETE FROM submission WHERE user_id={r[2]} AND problem_id={r[1]} AND id > {r[0]}")
		except:
			pass

	# Creates a table that will store ELO scores for each user (Global ELO and ELO for each category)
	ACR_Globals.__CURSOR.execute("DROP TABLE IF EXISTS User_Scores")
	ACR_Globals.__CURSOR.execute(f"""CREATE TABLE IF NOT EXISTS User_Scores(
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

	ACR_Globals.__CURSOR.execute("SELECT user_id FROM submission GROUP BY user_id")
	for usr in ACR_Globals.__CURSOR.fetchall():
		ACR_Globals.__CURSOR.execute(f"INSERT INTO User_Scores(user_id) VALUES({usr[0]})")


	# Creates a table that will store ELO scores for each problem
	ACR_Globals.__CURSOR.execute("DROP TABLE IF EXISTS Problem_Scores")
	ACR_Globals.__CURSOR.execute(f"""CREATE TABLE IF NOT EXISTS Problem_Scores(
		problem_id INT PRIMARY KEY, 
		elo_global FLOAT(18,16) NOT NULL DEFAULT 8.0,
		FOREIGN KEY (problem_id) REFERENCES problem (internalId) ON DELETE CASCADE)""")

	ACR_Globals.__CURSOR.execute("SELECT internalId FROM problem GROUP BY internalId")
	for prb in ACR_Globals.__CURSOR.fetchall():
		ACR_Globals.__CURSOR.execute(f"INSERT INTO Problem_Scores(problem_id) VALUES({prb[0]})")

	# Adds 2 new columns to the 'submission' table (user_elo, problem_elo)
	# These store the resulting ELOs for both user and problem after a simulation
	try:
		ACR_Globals.__CURSOR.execute("ALTER TABLE submission ADD COLUMN user_elo FLOAT(18,16)")
		ACR_Globals.__CURSOR.execute("ALTER TABLE submission ADD COLUMN problem_elo FLOAT(18,16)")
	except:
		ACR_Globals.__CURSOR.execute("UPDATE submission SET user_elo=NULL")
		ACR_Globals.__CURSOR.execute("UPDATE submission SET problem_elo=NULL")

	ACR_Globals.__CONNECTION.commit()

def TRAIN_SUBJECTS():
	current_fights = {}

	ACR_Globals.__CURSOR.execute("SELECT * FROM submission WHERE id <= {} ORDER BY id".format(ACR_Globals.__DB_SPLITTER))

	rows = ACR_Globals.__CURSOR.fetchall()
	for row in tqdm(rows, desc="Calculating ELOs"):
		subm_id = row[0]
		p_id = row[1]
		u_id = row[2]
		status = row[5]

		# Checks if the user hasn't switched problems
		if u_id not in current_fights:
			current_fights[u_id] = p_id

		# Checks all conditions that could trigger a simulation (AC/PE, Problem Switch)
		if current_fights[u_id] != p_id or status in ('AC', 'PE'):

			# If he switches
			if current_fights[u_id] != p_id:
				CHANGE_ELOS(subm_id, u_id, current_fights[u_id], status)
				current_fights[u_id] = p_id

			# If he wins
			if status in ('AC', 'PE'):			
				del current_fights[u_id]
				CHANGE_ELOS(subm_id, u_id, p_id, status)

def CHANGE_ELOS(subm_id, u_id, p_id, status):
	ACR_Globals.__CURSOR.execute("SELECT elo_global FROM User_Scores WHERE user_id = {}".format(u_id))
	old_user_elo = ACR_Globals.__CURSOR.fetchone()[0]

	ACR_Globals.__CURSOR.execute("SELECT elo_global FROM Problem_Scores WHERE problem_id = {}".format(p_id))
	old_problem_elo = ACR_Globals.__CURSOR.fetchone()[0]

	new_user_elo, new_problem_elo = ELO.SIMULATE(old_user_elo, old_problem_elo, status)

	ACR_Globals.__CURSOR.execute("SELECT categoryId FROM problemcategories WHERE problemId = {}".format(p_id))
	for cat in ACR_Globals.__CURSOR.fetchall():
		try:
			category = ACR_Globals.__CATEGORIES[cat[0]]
			ACR_Globals.__CURSOR.execute("SELECT {} FROM User_Scores WHERE user_id = {}".format(category, u_id))
			Old_Category_ELO = ACR_Globals.__CURSOR.fetchone()[0]
			New_Category_ELO, _ = ELO.SIMULATE(Old_Category_ELO, old_problem_elo, status)
			
			ACR_Globals.__CURSOR.execute("UPDATE User_Scores SET {} = {} WHERE user_id = {}".format(category, New_Category_ELO, u_id))
		except:
			pass

	ACR_Globals.__CURSOR.execute("UPDATE submission SET problem_elo = {}, user_elo = {} WHERE id = {} and user_id = {} and problem_id = {}".format(new_problem_elo, new_user_elo, subm_id, u_id, p_id))
	ACR_Globals.__CURSOR.execute("UPDATE User_Scores SET elo_global = {} WHERE user_id = {}".format(new_user_elo, u_id))
	ACR_Globals.__CURSOR.execute("UPDATE Problem_Scores SET elo_global = {} WHERE problem_id = {}".format(new_problem_elo, p_id))
	ACR_Globals.__CONNECTION.commit()

def main():
	
	CREATE_AND_ALTER_NEEDED_TABLES()
	TRAIN_SUBJECTS()
	
	ACR_Stats.GRAPH_USERS_EVOLUTION()
	ACR_Stats.GRAPH_PROBLEMS_EVOLUTION()
	ACR_Stats.GRAPH_USER_CATEGORIES()

	ACR_Stats.GRAPH_ELO_DISTRIBUTION('Users')
	ACR_Stats.GRAPH_ELO_DISTRIBUTION('Problems')

	ACR_Stats.GRAPH_ELO_DIFFERENCES('<=')
	ACR_Stats.GRAPH_ELO_DIFFERENCES('>')

	ACR_Globals.__CONNECTION.close()

if __name__== "__main__":
	main()