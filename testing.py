import pymysql
import sys
import datetime

# Database connection
connection = pymysql.connect(host="localhost",user="root",passwd="",database="acr_dat")
__cursor = connection.cursor()


"""
__cursor.execute(f"SELECT * from {sys.argv[1]}")

with open(sys.argv[2], 'w', encoding='utf-8') as file:
	for row in __cursor.fetchall():
		file.write(str(row)+'\n')
"""

"""
CREATE TABLE 'submission' (
 'id' int(11) NOT NULL AUTO_INCREMENT,
 'problem_id' int(11) DEFAULT NULL,
 'user_id' int(11) DEFAULT NULL,
 'language' varchar(3) COLLATE utf8_unicode_ci NOT NULL,
 'ranking' int(11) DEFAULT NULL,
 'status' varchar(3) COLLATE utf8_unicode_ci NOT NULL,
 'user_elo' DECIMAL(6,4), 									# NEW
 'problem_elo' DECIMAL(6,4), 								# NEW
 'submissionDate' datetime NOT NULL,
 PRIMARY KEY ('id'),
 KEY 'problem_id' ('problem_id'),
 KEY 'user_id' ('user_id'),
 KEY 'submissionDate' ('submissionDate'),
 KEY 'status' ('status'),
 CONSTRAINT 'Submission_ibfk_1' FOREIGN KEY ('problem_id') REFERENCES 'problem' ('internalId'),
 CONSTRAINT 'Submission_ibfk_2' FOREIGN KEY ('user_id') REFERENCES 'users' ('id') ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=260342 DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci
"""


__cursor.execute("ALTER TABLE submission ADD COLUMN user_elo DECIMAL(6,4))")
__cursor.execute("ALTER TABLE submission ADD COLUMN problem_elo DECIMAL(6,4))")

connection.close()