import math 

__MAX_TRIES = 10
__MAX_ELO = 16
__MIN_ELO = 0

def Expectation(Ra, Rb): 
	""" Calculates the 'Expectation' value following the original formula """
	return 1.0 / (1 + math.pow(10, -((Ra - Rb) / 8))) 

def k_factor_new_formula(elo_diff, underdog_won):
	""" Calculates the K-factor """
	if underdog_won: 	return (elo_diff + 16) / 32
	else:				return (0.5 - elo_diff / 32)

def k_factor_new_formula_with_tries(elo_diff, underdog_won, tries, status):
	""" Calculates the K-factor """
	if tries >= __MAX_TRIES: tries = __MAX_TRIES
	if underdog_won: 	return ((elo_diff + 16) / 32) * (tries / __MAX_TRIES)
	else:				return (0.5 - elo_diff / 32) * (tries / __MAX_TRIES)

def k_factor_new_formula_with_tries_bigger_gain(elo_diff, underdog_won, tries, status):
	""" Calculates the K-factor """
	if tries >= __MAX_TRIES: tries = __MAX_TRIES
	if underdog_won: 	return ((elo_diff + __MAX_TRIES) / __MAX_TRIES) * (tries / __MAX_TRIES)
	else:				return (1 - elo_diff / __MAX_TRIES) * (tries / __MAX_TRIES)

def simulate_no_tries(ELO_user, ELO_problem, Submission_State):

	User_Old_Score = ELO_user
	Problem_Old_Score = ELO_problem

	User_Expectation = Expectation(User_Old_Score, Problem_Old_Score) 
	Problem_Expectation = Expectation(Problem_Old_Score, User_Old_Score) 
	ELO_Difference = User_Old_Score - Problem_Old_Score

	"""
	if Submission_State in ('AC', 'PE') and ELO_Difference < 0:			k = k_factor_new_formula(abs(ELO_Difference), True)
	elif Submission_State in ('AC', 'PE') and ELO_Difference >= 0:		k = k_factor_new_formula(abs(ELO_Difference), False)
	elif Submission_State not in ('AC', 'PE') and ELO_Difference < 0:	k = k_factor_new_formula(abs(ELO_Difference), False)
	elif Submission_State not in ('AC', 'PE') and ELO_Difference >= 0:	k = k_factor_new_formula(abs(ELO_Difference), True)
	"""

	if Submission_State in ('AC', 'PE'): 

		if User_Old_Score < Problem_Old_Score: 
			k = k_factor_new_formula(abs(ELO_Difference), True)
		else:	
			k = k_factor_new_formula(abs(ELO_Difference), False)

		User_New_Score = User_Old_Score + k * (1 - User_Expectation)
		Problem_New_Score = Problem_Old_Score + k * (0 - Problem_Expectation)

	else : 

		if Problem_Old_Score < User_Old_Score: 
			k = k_factor_new_formula(abs(ELO_Difference), True)
		else:	
			k = k_factor_new_formula(abs(ELO_Difference), False)

		User_New_Score = User_Old_Score + k * (0 - User_Expectation)
		Problem_New_Score = Problem_Old_Score + k * (1 - Problem_Expectation)

	if User_New_Score < 0 or User_New_Score >16 or Problem_New_Score < 0 or Problem_New_Score >16: 
		User_New_Score = User_Old_Score
		Problem_New_Score = Problem_Old_Score

	#return (User_Old_Score - Problem_Old_Score),(User_New_Score - User_Old_Score), (Problem_New_Score - Problem_Old_Score)
	return User_New_Score, Problem_New_Score

def simulate_with_tries(ELO_user, ELO_problem, Submission_State, tries):
	""" Calculates the new ratings for both player & problem """

	User_Old_Score = ELO_user
	Problem_Old_Score = ELO_problem

	User_Expectation = Expectation(User_Old_Score, Problem_Old_Score) 
	Problem_Expectation = Expectation(Problem_Old_Score, User_Old_Score) 
	ELO_Difference = User_Old_Score - Problem_Old_Score

	# If Player_1 beats Player_2
	if Submission_State in ('AC', 'PE'): 

		# If Player_1 Wins, and his score is lower than Player_2's score
		if User_Old_Score < Problem_Old_Score: 
			k = k_factor_new_formula_with_tries_bigger_gain(abs(ELO_Difference), True, tries, Submission_State)

		# If Player_1 Wins, but his score is higher than Player_2's score
		else:	
			k = k_factor_new_formula_with_tries_bigger_gain(abs(ELO_Difference), False, tries, Submission_State)
		User_New_Score = User_Old_Score + k * (1 - User_Expectation)
		Problem_New_Score = Problem_Old_Score + k * (0 - Problem_Expectation)

	# If Player_2 beats Player_1
	else : 

		# If Player_2 Wins, and his score is lower than Player_1's score
		if Problem_Old_Score < User_Old_Score: 
			k = k_factor_new_formula_with_tries_bigger_gain(abs(ELO_Difference), True, tries, Submission_State)

		# If Player_2 Wins, but his score is higher than Player_1's score
		else:	
			k = k_factor_new_formula_with_tries_bigger_gain(abs(ELO_Difference), False, tries, Submission_State)
		User_New_Score = User_Old_Score + k * (0 - User_Expectation)
		Problem_New_Score = Problem_Old_Score + k * (1 - Problem_Expectation)

	# The following statements prevent the scores from going over 16 or reaching negative values
	if User_New_Score < 0 or User_New_Score >16 or Problem_New_Score < 0 or Problem_New_Score >16: 
		User_New_Score = User_Old_Score
		Problem_New_Score = Problem_Old_Score
	
	return User_New_Score, Problem_New_Score