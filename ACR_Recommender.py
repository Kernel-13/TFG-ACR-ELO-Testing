import ACR_Globals

__NUM_RECOMD = 5		# Nº of problems recommended
__NUM_SOL_1st = 5 		# Nº of 'Solved Problems' from the FIRST half that the user needs in order to get a recommendation
__NUM_SOL_2nd = 5 		# Nº of 'Solved Problems' from the SECOND half that the user needs in order to get a recommendation 
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
						ORDER BY id""".format(ACR_Globals.__DB_SPLITTER, users_from_first_half, __NUM_SOL_2nd)

def ONE_HIT_GLOBAL(r_type):
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
		GLOBAL_RECOMMENDATION(r_type, user_id=k, user_elo=v)

		for p in ACR_Globals.__CURSOR.fetchall():
			user_rcmd[k].append(p[0])

	# Check if the user solves the problems we would have recommended him
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

	with open('ONE HIT (@ {} - {}x{} AC [{}]).txt'.format(__NUM_RECOMD, __NUM_SOL_1st, __NUM_SOL_2nd, "SOLVED" if __ONLY_SOLVED else "TRIED"), 'w') as fd:
		for p in print_list:
			fd.write(p)

	print('ONE_HIT: {}	-	GLOBAL (@ {} - {}x{} AC [{}])'.format(len(hits)/len(u_p_pos), __NUM_RECOMD, __NUM_SOL_1st, __NUM_SOL_2nd, "SOLVED" if __ONLY_SOLVED else "TRIED"))

def ONE_HIT_CATEGORIES(r_type):
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
				CATEGORIES_RECOMMENDATION(r_type, user_id=usr, user_elo=elo, code=categs_codes[categs_title.index(cat)])
			else:
				GLOBAL_RECOMMENDATION(r_type, user_id=usr, user_elo=elo)

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

	print_list = []

	for usr in user_elos:
		print_list.append("\nUser: {}".format(usr))
		for cat, prb in u_p_pos[usr].items():
			print_list.append("\n	{}: {}".format(cat,prb))
	print_list.append("\n ONE_HIT: {}".format(len(hits)/len(u_p_pos)))


	with open('ONE HIT CAT(@ {} - {}x{} AC [{}]).txt'.format(__NUM_RECOMD, __NUM_SOL_1st, __NUM_SOL_2nd, "SOLVED" if __ONLY_SOLVED else "TRIED"), 'w') as fd:
		for p in print_list:
			fd.write(p)

	print('ONE_HIT: {}	-	CATEGORIES (@ {} - {}x{} AC [{}])'.format(len(hits)/len(u_p_pos), __NUM_RECOMD, __NUM_SOL_1st, __NUM_SOL_2nd, "SOLVED" if __ONLY_SOLVED else "TRIED"))

def GLOBAL_RECOMMENDATION(r_type, user_id, user_elo):
	if r_type == 1:
		ACR_Globals.__CURSOR.execute("""SELECT problem_id, elo_global, ABS({} - elo_global) as diff FROM problem_scores
			WHERE problem_id NOT IN (
				SELECT DISTINCT(problem_id) FROM submission
				WHERE id < {}
				AND user_id = {}
				AND (status = 'AC' or status = 'PE')
				GROUP BY problem_id
			)
			ORDER BY elo_global ASC LIMIT {}""".format(user_elo, ACR_Globals.__DB_SPLITTER, user_id, __NUM_RECOMD))
	elif r_type == 2:
		ACR_Globals.__CURSOR.execute("""SELECT problem_id, elo_global, ABS({} - elo_global) as diff FROM problem_scores
			WHERE elo_global >= {}
			AND problem_id NOT IN (
				SELECT DISTINCT(problem_id) FROM submission
				WHERE id < {}
				AND user_id = {}
				AND (status = 'AC' or status = 'PE')
				GROUP BY problem_id
			)
			ORDER BY elo_global ASC LIMIT {}""".format(user_elo, user_elo, ACR_Globals.__DB_SPLITTER, user_id, __NUM_RECOMD))

def CATEGORIES_RECOMMENDATION(r_type, user_id, user_elo, code):
	if r_type == 1:
		ACR_Globals.__CURSOR.execute("""SELECT problem_id, ABS({} - elo_global) as diff FROM problem_scores 
			WHERE problem_id IN (
				SELECT problem_id FROM problemcategories
				WHERE categoryId = {})
			AND problem_id NOT IN (
				SELECT DISTINCT(problem_id) FROM submission
				WHERE id < {}
				AND user_id = {}
				AND (status = 'AC' or status = 'PE')
				GROUP BY problem_id	)
			ORDER BY elo_global ASC LIMIT {}""".format(user_elo, code, ACR_Globals.__DB_SPLITTER, user_id, __NUM_RECOMD))
	elif r_type == 2:
		ACR_Globals.__CURSOR.execute("""SELECT problem_id, ABS({} - elo_global) as diff FROM problem_scores 
			WHERE elo_global >= {} 
			AND problem_id IN (
				SELECT problem_id FROM problemcategories
				WHERE categoryId = {})
			AND problem_id NOT IN (
				SELECT DISTINCT(problem_id) FROM submission
				WHERE id < {}
				AND user_id = {}
				AND (status = 'AC' or status = 'PE')
				GROUP BY problem_id	)
			ORDER BY elo_global ASC LIMIT {}""".format(user_elo, user_elo, code, ACR_Globals.__DB_SPLITTER, user_id, __NUM_RECOMD))

for i in [3,5,10]:
	for j in [1,3,5,8,10]:
		for k in [1,3,5,8,10]:
			for b in [False, True]:

				__NUM_RECOMD = i
				__NUM_SOL_1st = k
				__NUM_SOL_2nd = j
				__ONLY_SOLVED = b

				users_from_first_half = """SELECT user_id FROM submission
										WHERE id <= {}
										GROUP BY user_id
										HAVING sum(CASE 
													WHEN status = 'AC' THEN 1
													WHEN status = 'PE' THEN 1 
													ELSE 0 
													END) >= {}""".format(ACR_Globals.__DB_SPLITTER, __NUM_SOL_1st)

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

				ONE_HIT_GLOBAL(2)
				ONE_HIT_CATEGORIES(2)