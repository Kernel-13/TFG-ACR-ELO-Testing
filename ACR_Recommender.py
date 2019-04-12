import ACR_Globals

__NUM_RECOMD = 3
__NUM_SOL_1st = 10
__NUM_SOL_2nd = 3
__ONLY_SOLVED = True

# Users from the FIRST half with at least __NUM_SOL_1st solved problems 
users_from_first_half = """SELECT user_id FROM submission
						WHERE id <= {}
						GROUP BY user_id
						HAVING sum(CASE 
									WHEN status = 'AC' THEN 1
									WHEN status = 'PE' THEN 1 
									ELSE 0 
									END) >= {}""".format(ACR_Globals.__DB_SPLITTER, __NUM_SOL_1st)

# Users from the SECOND half with at least __NUM_SOL_2nd solved problems 
users_from_second_half = """SELECT user_id FROM submission
						WHERE id > {}
						AND user_id IN ({})
						GROUP BY user_id
						HAVING sum(CASE 
									WHEN status = 'AC' THEN 1
									WHEN status = 'PE' THEN 1 
									ELSE 0 
									END) >= {}
						ORDER BY id""".format(ACR_Globals.__DB_SPLITTER, users_from_first_half, __NUM_SOL_1st)

def AVERAGE_PRECISION_AT_N():
	pass

def ONE_HIT_GLOBAL():
	user_elos = {}
	user_rcmd = {}
	u_p_pos = {}
	hits = []

	ACR_Globals.__CURSOR.execute("SELECT user_id, elo_global FROM user_scores WHERE user_id IN ({})".format(users_from_second_half))
	for r in ACR_Globals.__CURSOR.fetchall():
		user_elos[r[0]] = r[1]
		user_rcmd[r[0]] = []
		u_p_pos[r[0]] = []

	for k,v in user_elos.items():
		ACR_Globals.__CURSOR.execute("""SELECT problem_id, elo_global, ABS({} - elo_global) as diff FROM problem_scores
			WHERE problem_id NOT IN (
				SELECT DISTINCT(problem_id) FROM submission
				WHERE id < {}
				AND user_id = {}
				AND (status = 'AC' or status = 'PE')
				GROUP BY problem_id
			)
			ORDER BY diff ASC LIMIT {}""".format(v, ACR_Globals.__DB_SPLITTER, k, __NUM_RECOMD))

		for p in ACR_Globals.__CURSOR.fetchall():
			user_rcmd[k].append(p[0])

	# Check if the user solves the problems we would recommend him
	ACR_Globals.__CURSOR.execute("""SELECT user_id, problem_id, status FROM submission
				WHERE id > {}
				{}
				AND user_id IN ({})
				GROUP BY user_id, problem_id, status
				ORDER BY id""".format(ACR_Globals.__DB_SPLITTER, " AND (status = 'AC' OR status='PE') " if __ONLY_SOLVED else "" , users_from_second_half))

	for s in ACR_Globals.__CURSOR.fetchall():
		try:
			usr = s[0]
			prb = s[1]
			if prb in user_rcmd[usr]:
				u_p_pos[usr].append(user_rcmd[usr].index(prb))
				if usr not in hits:
					hits.append(usr)
		except:
			pass

	print_list = []
	for usr in user_elos:
		print_list.append("{} {}\n".format(usr, u_p_pos[usr]))
	print_list.append("\n ONE_HIT: {}".format(len(hits)/len(u_p_pos)))

	with open('ONE HIT (@ {} - {}x{} AC [{}]).txt'.format(__NUM_RECOMD, __NUM_SOL_1st, __NUM_SOL_2nd, "SOLVED ONLY" if __ONLY_SOLVED else "TRIED"), 'w') as fd:
		for p in print_list:
			fd.write(p)

def ONE_HIT_CATEGORIES():
	user_elos = {}
	user_rcmd = {}
	u_p_pos = {}
	hits = []

	# Store ELO per categories
	categs_codes = []
	categs_title = []
	for k,v in ACR_Globals.__CATEGORIES.items():
		categs_codes.append(k)
		categs_title.append(v)

	ACR_Globals.__CURSOR.execute("SELECT * FROM user_scores WHERE user_id IN ({})".format(users_from_second_half))
	for r in ACR_Globals.__CURSOR.fetchall():
		cat_elos = {}
		cat_recm = {}
		cat_posi = {}
		for i, elo in enumerate(r[2:]):
			if elo != 8.0:
				cat_elos[categs_title[i]] = elo
				cat_recm[categs_title[i]] = []
				cat_posi[categs_title[i]] = []

		cat_elos['Global'] = r[1]
		cat_recm['Global'] = []
		cat_posi['Global'] = []

		user_elos[r[0]] = cat_elos
		user_rcmd[r[0]] = cat_recm		
		u_p_pos[r[0]] = cat_posi

	# Select problems to recommend based on ELO difference
	for usr,elos in user_elos.items():
		# usr -> user_id (int)
		# elos -> (dict)
		#		elos.cat -> category (string)
		#		elos.elo -> ELO (float)


		for cat,elo in elos.items():
			if cat != 'Global':
				code = categs_codes[categs_title.index(cat)]
				ACR_Globals.__CURSOR.execute("""SELECT problem_id, ABS(elo_global - {}) as diff FROM problem_scores 
					WHERE problem_id IN (
						SELECT problem_id FROM problemcategories
						WHERE categoryId = {})
					AND problem_id NOT IN (
						SELECT DISTINCT(problem_id) FROM submission
						WHERE id < {}
						AND user_id = {}
						AND (status = 'AC' or status = 'PE')
						GROUP BY problem_id	)
					ORDER BY diff ASC LIMIT {}""".format(elo, code, ACR_Globals.__DB_SPLITTER, usr, __NUM_RECOMD))
			else:
				ACR_Globals.__CURSOR.execute("""SELECT problem_id, ABS(elo_global - {}) as diff FROM problem_scores 
					WHERE problem_id NOT IN (
						SELECT DISTINCT(problem_id) FROM submission
						WHERE id < {}
						AND user_id = {}
						AND (status = 'AC' or status = 'PE')
						GROUP BY problem_id	)
					ORDER BY diff ASC LIMIT 3""".format(elo, ACR_Globals.__DB_SPLITTER, usr))

			for p in ACR_Globals.__CURSOR.fetchall():
				user_rcmd[usr][cat].append(p[0])

	ACR_Globals.__CURSOR.execute("""SELECT user_id, problem_id, status FROM submission
				WHERE id > {}
				{}
				AND user_id IN ({})
				GROUP BY user_id, problem_id, status""".format(ACR_Globals.__DB_SPLITTER, " AND (status = 'AC' OR status='PE') " if __ONLY_SOLVED else "" , users_from_second_half))

	for s in ACR_Globals.__CURSOR.fetchall():
		try:
			usr = s[0]
			prb = s[1]
			for cat,elo in user_rcmd[usr].items():
				if prb in user_rcmd[usr][cat]:
					u_p_pos[usr][cat].append(user_rcmd[usr][cat].index(prb))
					if usr not in hits:
						hits.append(usr)
		except:
			pass

	print(__NUM_RECOMD, __NUM_SOL_1st, __NUM_SOL_2nd)
	print_list = []

	for usr in user_elos:
		print('\nUser: ', usr)
		print_list.append("\nUser: {}".format(usr))
		for cat, prb in u_p_pos[usr].items():
			print(f'	{cat}: ', prb)
			print_list.append("\n	{}: {}".format(cat,prb))
	print_list.append("\n ONE_HIT: {}".format(len(hits)/len(u_p_pos)))


	with open('ONE HIT CAT(@ {} - {}x{} AC [{}]).txt'.format(__NUM_RECOMD, __NUM_SOL_1st, __NUM_SOL_2nd, "SOLVED ONLY" if __ONLY_SOLVED else "TRIED"), 'w') as fd:
		for p in print_list:
			fd.write(p)
	"""
	with open('ONE HIT CAT(@ {} - {}x{} AC).txt'.format(__NUM_RECOMD, __NUM_SOL_1st, __NUM_SOL_2nd), 'w') as fd:
		for u in user_elos:
			print('\nUser: ', usr)
			fd.write("\nUser: {}\n".format(u))
			for cat, prb in u_p_pos[usr].items():
				print(f'	{cat}: ', prb)
				fd.write("	{}: {}\n".format(str(cat), str(prb)))

		fd.write("\n ONE_HIT: {}".format(len(hits)/len(u_p_pos)))
	"""

def recommender_global():
	""" First we need to simulate ELO fights with the submissions from 2015 to 2017 to calculate ELO values for each problem/user
	After that, we need to choose a group of problems that we want to recommend these users
	With each user and group of recommended problems, we must check if he really tries those problems or not
	If he tries/solves a problem from the group, then its a true positive (should he also solve it?)
	If he doesn't, then its a false positive
	If he tries a problem outside the group of recommended problems, then its a false negative
	If he doesn't try/solve problems that are outside the group of recommended problems, then its a true negative """

	user_elos = {}
	user_rcmd = {}
	u_p_pos = {}

	# Users from the FIRST half with more than 5 solved problems 
	users_from_first_half = """SELECT user_id FROM submission
							WHERE submissionDate >= '2015-09-01 00:00:00' 
							AND submissionDate < '2017-09-01 00:00:00'
							GROUP BY user_id
							HAVING sum(CASE 
										WHEN status = 'AC' THEN 1
										WHEN status = 'PE' THEN 1 
										ELSE 0 
										END) >= 5"""

	# Users from the SECOND half with more than 5 solved problems 
	users_from_second_half = """SELECT user_id FROM submission
				WHERE submissionDate >= '2017-09-01 00:00:00' 
				AND submissionDate < '2018-09-01 00:00:00'
				AND user_id IN (%s)
				GROUP BY user_id
				HAVING sum(CASE 
								WHEN status = 'AC' THEN 1
								WHEN status = 'PE' THEN 1 
								ELSE 0 
								END) >= 5
				ORDER BY id""" % users_from_first_half

	# 
	ACR_Globals.__CURSOR.execute(f"""SELECT user_id, elo_global FROM user_scores WHERE user_id IN ({users_from_second_half})""")
	for r in ACR_Globals.__CURSOR.fetchall():
		user_elos[r[0]] = r[1]
		user_rcmd[r[0]] = []
		u_p_pos[r[0]] = []

	
	for k,v in user_elos.items():
		ACR_Globals.__CURSOR.execute(f"""SELECT problem_id, elo_global, ABS({v} - elo_global) as diff FROM problem_scores ORDER BY diff ASC LIMIT 20""")
		for p in ACR_Globals.__CURSOR.fetchall():
			user_rcmd[k].append(p[0])

	ACR_Globals.__CURSOR.execute(f"""SELECT user_id, problem_id, status FROM submission
				WHERE submissionDate >= '2017-09-01 00:00:00' 
				AND submissionDate < '2018-09-01 00:00:00'
				AND (status = 'AC' OR status='PE')
				AND user_id IN ({users_from_second_half})
				GROUP BY user_id, problem_id, status
				ORDER BY id""")

	for s in ACR_Globals.__CURSOR.fetchall():
		try:
			usr = s[0]
			prb = s[1]
			if prb in user_rcmd[usr]:
				u_p_pos[usr].append(user_rcmd[usr].index(prb))
		except:
			pass

	for u in user_elos:
		print(u, u_p_pos[u])

	"""

	for u in ACR_Globals.__CURSOR.fetchall():
		if u[0] not in user_elos:
			ACR_Globals.__CURSOR.execute("SELECT elo_global FROM user_scores WHERE user_id=%s", (u[0],))
			user_elos[u[0]] = ACR_Globals.__CURSOR.fetchone()[0]

		if u[0] not in user_rcmd:
			ACR_Globals.__CURSOR.execute("SELECT problem_id FROM problem_scores WHERE elo_global BETWEEN %s AND %s ORDER BY elo_global ASC", (user_elos[u[0]]-1,user_elos[u[0]]+1,))
			user_rcmd[u[0]] = [p[0] for p in ACR_Globals.__CURSOR.fetchall()]
	"""
	
def recommender_per_category():
	""" First we need to simulate ELO fights with the submissions from 2015 to 2017 to calculate ELO values for each problem/user
	After that, we need to choose a group of problems that we want to recommend these users
	With each user and group of recommended problems, we must check if he really tries those problems or not
	If he tries/solves a problem from the group, then its a true positive (should he also solve it?)
	If he doesn't, then its a false positive
	If he tries a problem outside the group of recommended problems, then its a false negative
	If he doesn't try/solve problems that are outside the group of recommended problems, then its a true negative """

	user_elos = {}
	user_rcmd = {}
	u_p_pos = {}
	hits = []

	# Users from the FIRST half with more than 5 solved problems 
	users_from_first_half = """SELECT user_id FROM submission
							WHERE id <= {}
							GROUP BY user_id
							HAVING sum(CASE 
										WHEN status = 'AC' THEN 1
										WHEN status = 'PE' THEN 1 
										ELSE 0 
										END) >= 5""".format(ACR_Globals.__DB_SPLITTER)

	# Users from the SECOND half with more than 5 solved problems 
	users_from_second_half = """SELECT user_id FROM submission
				WHERE WHERE id > {}
				AND user_id IN ({})
				GROUP BY user_id
				HAVING sum(CASE 
								WHEN status = 'AC' THEN 1
								WHEN status = 'PE' THEN 1 
								ELSE 0 
								END) >= 5
				ORDER BY id""".format(ACR_Globals.__DB_SPLITTER, users_from_first_half)


	# Store ELO per categories
	categs_codes = []
	categs_title = []
	for k,v in ACR_Globals.__CATEGORIES.items():
		categs_codes.append(k)
		categs_title.append(v)

	ACR_Globals.__CURSOR.execute("SELECT * FROM user_scores WHERE user_id IN ({})".format(users_from_second_half))
	for r in ACR_Globals.__CURSOR.fetchall():
		cat_elos = {}
		cat_recm = {}
		cat_posi = {}
		for i, elo in enumerate(r[2:]):
			if elo != 8.0:
				cat_elos[categs_title[i]] = elo
				cat_recm[categs_title[i]] = []
				cat_posi[categs_title[i]] = []

		cat_elos['Global'] = r[1]
		cat_recm['Global'] = []
		cat_posi['Global'] = []

		user_elos[r[0]] = cat_elos
		user_rcmd[r[0]] = cat_recm		
		u_p_pos[r[0]] = cat_posi

	# Select problems to recommend based on ELO difference
	for usr,elos in user_elos.items():
		# usr -> user_id (int)
		# elos -> (dict)
		#		elos.cat -> category (string)
		#		elos.elo -> ELO (float)


		for cat,elo in elos.items():
			if cat != 'Global':
				code = categs_codes[categs_title.index(cat)]
				ACR_Globals.__CURSOR.execute(f"""SELECT problem_id, ABS(elo_global - {elo}) as diff FROM problem_scores 
					WHERE problem_id IN (
						SELECT problem_id FROM problemcategories
						WHERE categoryId = {code})
					ORDER BY diff ASC""")
			else:
				ACR_Globals.__CURSOR.execute(f"""SELECT problem_id, ABS(elo_global - {elo}) as diff FROM problem_scores ORDER BY diff ASC""")

			for p in ACR_Globals.__CURSOR.fetchall():
				user_rcmd[usr][cat].append(p[0])

	ACR_Globals.__CURSOR.execute(f"""SELECT user_id, problem_id, status FROM submission
				WHERE submissionDate >= '2017-09-01 00:00:00' 
				AND submissionDate < '2018-09-01 00:00:00'
				AND (status = 'AC' OR status='PE')
				AND user_id IN ({users_from_second_half})
				GROUP BY user_id, problem_id, status""")

	for s in ACR_Globals.__CURSOR.fetchall():
		try:
			usr = s[0]
			prb = s[1]
			for cat,elo in user_rcmd[usr].items():
				if prb in user_rcmd[usr][cat]:
					u_p_pos[usr][cat].append(user_rcmd[usr][cat].index(prb))
					if usr not in hits:
						hits.append(usr)
		except:
			pass
	
	for usr in user_elos:
		print('\nUser: ', usr)
		for cat, prb in u_p_pos[usr].items():
			print(f'	{cat}: ', prb)


	print("\n ONE_HIT: ", len(hits)/len(u_p_pos))
	"""

	for u in ACR_Globals.__CURSOR.fetchall():
		if u[0] not in user_elos:
			ACR_Globals.__CURSOR.execute("SELECT elo_global FROM user_scores WHERE user_id=%s", (u[0],))
			user_elos[u[0]] = ACR_Globals.__CURSOR.fetchone()[0]

		if u[0] not in user_rcmd:
			ACR_Globals.__CURSOR.execute("SELECT problem_id FROM problem_scores WHERE elo_global BETWEEN %s AND %s ORDER BY elo_global ASC", (user_elos[u[0]]-1,user_elos[u[0]]+1,))
			user_rcmd[u[0]] = [p[0] for p in ACR_Globals.__CURSOR.fetchall()]
	"""

for i in [3,10,20]:
	for j in [1,3,5,8,10]:
		for k in [1,3,5,8,10]:

			__NUM_RECOMD = i
			__NUM_SOL_1st = k
			__NUM_SOL_2nd = j

			# Users from the FIRST half with more than __NUM_SOL_1st solved problems 
			users_from_first_half = """SELECT user_id FROM submission
									WHERE id <= {}
									GROUP BY user_id
									HAVING sum(CASE 
												WHEN status = 'AC' THEN 1
												WHEN status = 'PE' THEN 1 
												ELSE 0 
												END) >= {}""".format(ACR_Globals.__DB_SPLITTER, __NUM_SOL_1st)

			# Users from the SECOND half with more than __NUM_SOL_1st solved problems 
			users_from_second_half = """SELECT user_id FROM submission
									WHERE id > {}
									AND user_id IN ({})
									GROUP BY user_id
									HAVING sum(CASE 
												WHEN status = 'AC' THEN 1
												WHEN status = 'PE' THEN 1 
												ELSE 0 
												END) >= {}
									ORDER BY id""".format(ACR_Globals.__DB_SPLITTER, users_from_first_half, __NUM_SOL_2nd)

			ONE_HIT_GLOBAL()
