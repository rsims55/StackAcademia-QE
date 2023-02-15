import requests
import time
import html2text
import json
import pandas as pd
import numpy as np

h = html2text.HTML2Text()

TAG = "research-undergraduate"
SITE = "academia"
CLIENT_ID = "25205"

# URL for access token: https://stackexchange.com/oauth/dialog?client_id=25205&scope=no_expiry&redirect_uri=https://stackexchange.com/oauth/login_success
# StackOverflow guide: https://stackoverflow.com/questions/36343556/how-to-use-oauth2-to-access-stackexchange-api
# Info for Stack: https://stackapps.com/apps/oauth/view/25205
API_KEY = "qjzOtJjAwrt1Jrb5htXJKg(("
NOEXPIRY_ACCESS_TOKEN = "4Q7EtMc7Tsh87qR9dg5gxw))"

def define_usertype(useraboutme):
	"""Takes the user about me information and returns an estimate of the user's academic stage"""

	phd = ["phd", "doctorate", "dr", "graduated", "graduate student", "grad student"]
	masters = ["masters"]
	undergraduate = ["student", "undergraduate", "bachelor", "bachelors", "baccalaureate", "undergrad", "freshman", "junior", "sophomore", "senior"]
	professor = ["professor", "faculty", "lecturer"]
	graduate_student = ["student", "graduate", "candidate", "grad"]
	postdoc = ["postdoc", "postdoctorate", "postgraduate", "post-graduate", "post graduate", "post-doctoral",
			   "post doc", "fellow", "graduated in", "degree in"]
	# Try to determine what career stage
	if any(x in useraboutme.lower().replace(".", "") for x in phd):
		if any(y in useraboutme.lower().replace(".", "") for y in professor):
			return "professor"
		elif any(y in useraboutme.lower().replace(".", "") for y in postdoc):
			return "post doctorate"
		elif any(y in useraboutme.lower().replace(".", "") for y in graduate_student):
			return "graduate student"
		else:
			return "graduated_phd"
	elif any(x in useraboutme.lower().replace(".", "") for x in masters):
		if any(y in useraboutme.lower().replace(".", "") for y in graduate_student):
			return "graduate student"
		elif any(y in useraboutme.lower().replace(".", "") for y in professor):
			return "professor"
		else:
			return "graduated_masters"
	elif any(x in useraboutme.lower().replace(".", "") for x in undergraduate):
		if any(y in useraboutme.lower().replace(".", "") for y in graduate_student):
			return "undergraduate student"
		elif any(y in useraboutme.lower().replace(".", "") for y in professor):
			return "professor"
		else:
			return "graduated_undergraduate"
	elif any(x in useraboutme.lower().replace(".", "") for x in professor):
		return "professor"
	elif any(x in useraboutme.lower().replace(".", "") for x in postdoc):
		return "post doctorate"
	elif any(x in useraboutme.lower().replace(".", "") for x in graduate_student):
		return "graduate student"
	elif useraboutme.lower().replace(".", "") == "  ":
		return "No user information"
	else:
		return useraboutme



def get_questionids(page_count = 1):
	"""Gets question ids to feed into the raw data function"""

	api_res = f"https://api.stackexchange.com/2.3/questions?key={API_KEY}&access_token={NOEXPIRY_ACCESS_TOKEN}&page={int(page_count)}&pagesize=100&order=desc&sort=activity&tagged={TAG}&site={SITE}"
	response = requests.get(api_res)
	question_list = response.json()
	has_more = question_list['has_more']
	quota_remain = question_list['quota_remaining']
	question_ids = []
	while has_more:
		try:
			for entry_num in range(len(question_list["items"])):
				question_id = question_list["items"][entry_num]["question_id"]
				question_ids.append(question_id)
			quota_remain = question_list['quota_remaining']
			has_more = question_list['has_more']
			print(quota_remain)
			page_count += 1
			api_res = f"https://api.stackexchange.com/2.3/questions?key={API_KEY}&access_token={NOEXPIRY_ACCESS_TOKEN}&page={int(page_count)}&pagesize=100&order=desc&sort=activity&tagged={TAG}&site={SITE}"
			response = requests.get(api_res)
			question_list = response.json()
			'''One-second break after each call to prevent request overload'''
			time.sleep(2)
		except KeyError:
			has_more = False
	return question_ids


def get_raw_data(question_id):
	"""Gets raw data from the question id and puts it in a dictionary with the question ID"""

	api_res = f"https://api.stackexchange.com//2.3/questions/{question_id}?key={API_KEY}&access_token={NOEXPIRY_ACCESS_TOKEN}&order=desc&sort=activity&site={SITE}&filter=!22jPRAK.dmqh.RCdSxWC*"
	response = requests.get(api_res)
	response.raise_for_status()
	if response.status_code != 200:
		return{question_id: "No Data Found"}
	else:
		data = response.json()
		try:
			raw_data = {question_id: data}
			return raw_data
		except KeyError:
			return{question_id: "No Data Found"}

def get_question_info(raw_data, question_id):
	"""Gets information about the question from the raw data"""

	# Extracts information and parses the HTML
	try:
		question_title = h.handle(raw_data[question_id]["items"][0]["title"]).replace("\n", " ")
	except KeyError:
		question_title = h.handle(raw_data[question_id]["items"][0]["title"])
	try:
		question_body = h.handle(raw_data[question_id]["items"][0]["body"]).replace("\n", " ")
	except KeyError:
		question_body = h.handle(raw_data[question_id]["items"][0]["body"])
	try:
		question_link = h.handle(raw_data[question_id]["items"][0]["link"]).replace("\n","")
	except KeyError:
		question_link = h.handle(raw_data[question_id]["items"][0]["link"])
	question_score = (raw_data[question_id]["items"][0]["score"])
	# Gets information about comments on the question
	try:
		question_comments = raw_data[question_id]["items"][0]["comments"]
		question_comment_number = 0
		question_comment_list = []
		for individual_comment in question_comments:
			question_comment_user_id = individual_comment["owner"]["user_id"]
			try:
				question_comment_body = h.handle(individual_comment["body"]).replace("\n","")
			except KeyError:
				question_comment_body = h.handle(individual_comment["body"])
			try:
				question_comment_repliedto = individual_comment["reply_to_user"]["user_id"]
			except KeyError:
				question_comment_repliedto = "N/A"
			question_comment_number += 1
			question_comment_information = {"question_comment_number": question_comment_number,
											"question_comment_user_id": question_comment_user_id,
											"question_comment_body": question_comment_body,
											"question_comment_repliedto": question_comment_repliedto}
			question_comment_list.append(question_comment_information)
	except KeyError:
		question_comment_list = [{"question_comment_number": "N/A",
								"question_comment_user_id": "N/A",
								"question_comment_body": "N/A",
								"question_comment_repliedto": "N/A"}]
	try:
		question_user_id = raw_data[question_id]["items"][0]["owner"]["user_id"]
	except KeyError:
		question_user_id = "no user id"
	# Puts the question data into a dictionary with the question id as the key
	question_data = [question_title, question_body, question_link, question_user_id, question_score]
	return {"question_data" :
				{"question_title" : question_data[0],
				 "question_body" : question_data[1],
				 "question_link" : question_data[2],
				 "question_user_id" : question_data[3],
				 "question_score": question_data[4],
				 "question_comments": question_comment_list}
			}

def get_answer_info(raw_data, question_id):
	"""Gets information about the answers from the raw data"""

	try:
		list_of_answers = raw_data[question_id]["items"][0]["answers"]
		answer_list = []
		# Runs through all answers in the list and puts the data into a nested list
		try:
			for data in list_of_answers:
				try:
					answer_user_id = data["owner"]["user_id"]
				except KeyError:
					answer_user_id = "User ID Deleted"
				answer_accepted = data["is_accepted"]
				try:
					answer_body = h.handle(data["body"]).replace("\n", " ")
				except KeyError:
					answer_body = h.handle(data["body"])
				answer_score = data["score"]
				# Gets information about comments on particular answers
				try:
					answer_comments = data["comments"]
					answer_comment_number = 0
					answer_comment_list = []
					for individual_comment in answer_comments:
						answer_comment_user_id = individual_comment["owner"]["user_id"]
						try:
							answer_comment_body = h.handle(individual_comment["body"]).replace("\n", "")
						except KeyError:
							answer_comment_body = h.handle(individual_comment["body"])
						try:
							answer_comment_repliedto = individual_comment["reply_to_user"]["user_id"]
						except KeyError:
							answer_comment_repliedto = "N/A"
						answer_comment_number += 1
						answer_comment_information = {"answer_comment_number": answer_comment_number,
														"answer_comment_user_id": answer_comment_user_id,
														"answer_comment_body": answer_comment_body,
														"answer_comment_repliedto": answer_comment_repliedto}
						answer_comment_list.append(answer_comment_information)
				except KeyError:
					answer_comment_list = [{"answer_comment_number": "N/A",
												  "answer_comment_user_id": "N/A",
												  "answer_comment_body": "N/A",
												  "answer_comment_repliedto": "N/A"}]

				answer_information = {"answer_user_id": answer_user_id,
									 "was_answer_accepted": answer_accepted,
									 "answer_body": answer_body,
									  "answer_score": answer_score,
									  "answer_comments": answer_comment_list}
				answer_list.append(answer_information)
			answer_data = {"answer_data": answer_list}
			return answer_data
		except KeyError:
			pass
	except KeyError:
		return {"answer_data" : "NO ANSWERS"}

def get_comment_info(raw_data, question_id):
	"""Gest information about comments and who the comments were to"""
	comment_list = []

def get_crosstag_info(raw_data, question_id):
	"""Gets information about tags that were cross-posted against the question"""

	tag_data = raw_data[question_id]["items"][0]["tags"]
	tag_index = 0
	tag_list = []
	for data in tag_data:
	# Name tags by tagnumber and then iterate through for a dictionary
		tag_information = tag_data[tag_index]
		tag_index += 1
		tag_list.append(tag_information)
	return tag_list

"""RUN SCRIPT HERE"""
list_of_ids = get_questionids()
# list_of_ids = [154609, 82753]
count_down = len(list_of_ids)
list_of_clean_data = []

for question_id in list_of_ids:
	print(question_id)
	count_down -= 1
	print(count_down)
	raw_data = get_raw_data(question_id)
	with open("test_data.json", "w") as qe_notepadfile:
		json.dump(raw_data, qe_notepadfile, indent=2)
	time.sleep(1)
	if raw_data == {question_id: "No Data Found"}:
		pass
	else:
		question_data = get_question_info(raw_data, question_id)
		answer_data = get_answer_info(raw_data, question_id)
		tag_data = get_crosstag_info(raw_data, question_id)
		# REDO FOR DICTIONARY
		clean_data = {question_id:
								{"question_data":question_data["question_data"],
								 "answer_data":answer_data["answer_data"],
								 "tag_data": tag_data}
					  }
		list_of_clean_data.append(clean_data)

clean_data_dict = {}
for question_id in list_of_clean_data:
	clean_data_dict.update(question_id)

with open("test_data.json", "w", encoding="utf8") as qe_notepadfile:
	json.dump(clean_data_dict, qe_notepadfile, indent=2, ensure_ascii=True)
#
with open("test_data.json", "r") as data_file:
	data = json.loads(data_file.read())

# Indexes correctly
df = pd.DataFrame.from_dict(data, orient="index")


# Converts nested question_data in column and moves each key into its own column
df = pd.concat([df.drop(["question_data"], axis=1), df["question_data"].apply(pd.Series)], axis=1)
df.index.names = ["question_id"]
# Explodes answer data and then puts the data into their own columns
df = df.explode("answer_data")
df = pd.concat([df.drop(["answer_data"], axis=1), df["answer_data"].apply(pd.Series)], axis=1)
# Takes lists of comment data and transforms it length-wise, then puts the data into their own columns
df = df.explode("question_comments")
df = pd.concat([df.drop(["question_comments"], axis=1), df["question_comments"].apply(pd.Series)], axis=1)
df = df.explode("answer_comments")
df = pd.concat([df.drop(["answer_comments"], axis=1), df["answer_comments"].apply(pd.Series)], axis=1)

df = df.reset_index()

# Melts all text to duplicate rows of data
to_keep_text = ['question_id', 'tag_data', 'question_title', 'question_link', 'question_user_id', 'question_score', 'answer_user_id', 'was_answer_accepted', 'answer_score', 'question_comment_number', 'question_comment_user_id', 'question_comment_repliedto', 'answer_comment_number', 'answer_comment_user_id', 'answer_comment_repliedto']
to_melt_text = ['question_body', 'answer_body', 'question_comment_body', 'answer_comment_body']
df = pd.melt(df, id_vars=to_keep_text, value_vars=to_melt_text, var_name='text_type', value_name="text")
# Drops all unneccesary duplicates
df = df.drop_duplicates(subset='text', ignore_index=True)
# Goes through rows and gets rid of data that does not pertain to that type of body of text
text_types = ["question", "answer", "question_comment", "answer_comment"]
for text_type in text_types:
	df[f"{text_type}_user_id"].loc[df["text_type"] != f"{text_type}_body"] = "N/A"
	try:
		df[f"{text_type}_number"].loc[df["text_type"] != f"{text_type}_body"] = "N/A"
	except KeyError:
		pass
	try:
		df[f"{text_type}_score"].loc[df["text_type"] != f"{text_type}_body"] = "N/A"
	except KeyError:
		pass
df["was_answer_accepted"].loc[df["text_type"] != "answer_body"] = "N/A"
# Replaces all string n/a's with true n/a's for .fillna
df.replace("N/A", np.nan, inplace=True)
# Fills na's across rows so that there is only one id column and one score column
df["id"] = df["question_user_id"].fillna(df[["answer_user_id", "question_comment_user_id", "answer_comment_user_id"]].max(1))
df["score"] = df["question_score"].fillna(df["answer_score"])
df["comment_number"] = df["question_comment_number"].fillna(df["answer_comment_number"])
# Drops unneccessary columns
df = df.drop(columns=["question_user_id",
					  "question_score",
					  "answer_user_id",
					  "answer_score",
					  "question_comment_user_id",
					  "answer_comment_user_id",
					  "question_comment_number",
					  "answer_comment_number",
					  "question_comment_repliedto",
					  "answer_comment_repliedto"])


df.to_csv("test_data.csv", encoding='utf-8', na_rep="N/A")
