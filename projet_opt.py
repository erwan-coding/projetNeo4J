from py2neo import Graph
graph = Graph("bolt://localhost:7687", auth=("neo4j", "p"))
import pandas as pd

l_categorie = list(pd.read_csv('csv/cat_names.csv')['0'])

l_ambience = ['divey',
 'hipster',
 'casual',
 'touristy',
 'trendy',
 'intimate',
 'romantic',
 'classy',
 'upscale']

r_users = graph.run("match (u:User) return u.user_id").to_table()
l_users = [elt[0] for elt in r_users]


def res_to_dict(res):
	dic = {}
	for user in l_users: #on traite si neo4j ne renvoie rien pour ne pas avoir d'erreur
		dic[user] = 0
	for elt in res:
		user = elt[0]
		other = int(elt[1])
		dic[user] = other
	return dic


def build_score(city,ambs,cats,price_range):

	q_n_friends = "match (u:User )-[Friend]->(u1:User) return u.user_id,count(u1)"
	n_friends = graph.run(q_n_friends).to_table()
	n_friends_dic = res_to_dict(n_friends)
	
	q_max_friend = "match (u:User)-[f:Friend]->(u1:User) return u.user_id,count(u1) order by count(u1) desc limit 1"
	max_friend = graph.run(q_max_friend).to_table()[0][1]

	s1_dic = {}
	for user in l_users:
		s1_dic[user] = n_friends_dic[user]/max_friend 
	
	q_n_friend_friend = "match (u:User )-[f:Friend]->(u1:User)-[f1:Friend]->(u2:User) return u.user_id,count(u2)"
	n_friend_friend = graph.run(q_n_friend_friend).to_table()
	n_friend_friend_dic = res_to_dict(n_friend_friend)

	q_max_friend_friend= "match (u:User)-[f:Friend]->(u1:User)-[f1:Friend]->(u2:User) return u,count(u2) order by count(u2) desc limit 10"
	max_friend_friend = graph.run(q_max_friend_friend).to_table()[0][1]
	
	s2_dic = {}
	for user in l_users:
		s2_dic[user] = n_friend_friend_dic[user]/max_friend_friend
	
	q_n_fan = "match (u:User ) return u.user_id,u.fans"
	n_fan = graph.run(q_n_fan).to_table()
	n_fan_dic = res_to_dict(n_fan)

	q_max_fan = "match (u:User) return u.user_id,u.fans order by u.fans desc limit 1"
	max_fan = int(graph.run(q_max_fan).to_table()[0][1])

	s3_dic = {}
	for user in l_users:
		s3_dic[user] = n_fan_dic[user]/max_fan

	f_centralite_dic = {}
	for user in l_users:
		f_centralite_dic[user] = (s1_dic[user]+s2_dic[user]+s3_dic[user])/3
	
	q_n_review = "match (u:User )-[Wrote]->(r:Review) return u.user_id,count(r)"
	n_review = graph.run(q_n_review).to_table()
	n_review_dic = res_to_dict(n_review)
	
	q_n_review_ut = "match (u:User )-[Wrote]->(r:Review) where toInteger(r.useful)>0 return u.user_id,count(r)"
	n_review_ut = graph.run(q_n_review_ut).to_table()
	n_review_ut_dic = res_to_dict(n_review_ut)

	s4_dic = {}
	for user in l_users:
		s4_dic[user] = n_review_ut_dic[user]/n_review_dic[user]
	
	q_n_review_cool = "match (u:User )-[Wrote]->(r:Review) where toInteger(r.cool)>0 return u.user_id,count(r)"
	n_review_cool = graph.run(q_n_review_cool).to_table()
	n_review_cool_dic = res_to_dict(n_review_cool)
	
	s5_dic = {}
	for user in l_users:
		s5_dic[user] = n_review_cool_dic[user]/n_review_dic[user]
	
	f_validite_dic = {}
	for user in l_users:
		f_validite_dic[user] = (s4_dic[user]+s5_dic[user])/2
	
	rp_a = [] #contiendra un dictionnaire par ambiance
	for amb in ambs:
		q_n_review_pos_ambience = "match (u:User  )-[Wrote]->(r:Review)-[Critics]->(Restaurant)-[HasAmbience]->(a:Ambience) where toInteger(r.stars)>=4 and a.ambience_name = $amb_name return u.user_id,count(r)"
		n_review_pos_ambience = graph.run(q_n_review_pos_ambience,amb_name=amb).to_table()
		n_review_pos_ambience_dic = res_to_dict(n_review_pos_ambience)
		rp_a.append(n_review_pos_ambience_dic)
	
	s6_dic = {}
	n_amb = len(ambs)
	for user in l_users:
		total_user_reviews = n_review_dic[user]
		user_total = 0
		for d_amb in rp_a:
			user_total += d_amb[user]/total_user_reviews
		s6_dic[user] = user_total / n_amb
	
	rp_c = []
	for cat in cats:
		q_n_review_pos_categorie = "match (u:User )-[Wrote]->(r:Review)-[Critics]->(Restaurant)-[HasCategory]->(c:Categorie) where toInteger(r.stars)>=4 and c.category_name = $cat_name return u.user_id,count(r)"
		n_review_pos_categorie = graph.run(q_n_review_pos_categorie,cat_name=cat).to_table()
		n_review_pos_categorie_dic = res_to_dict(n_review_pos_categorie)
		rp_c.append(n_review_pos_categorie_dic)

	s7_dic = {}
	n_cat = len(cats)
	for user in l_users:
		total_user_reviews = n_review_dic[user]
		user_total = 0
		for d_cat in rp_c:
			user_total += d_cat[user]/total_user_reviews
		s7_dic[user] = user_total / n_cat
		

	q_n_review_pos_price_r = "match (u:User )-[Wrote]->(r:Review)-[Critics]->(res:Restaurant) where toInteger(r.stars)>=4 and toInteger(res.price_range)=$p_range return u.user_id,count(r)"
	n_review_pos_price_r = graph.run(q_n_review_pos_price_r,p_range=price_range).to_table()
	n_review_pos_price_r_dic = res_to_dict(n_review_pos_price_r)

	s8_dic = {}
	for user in l_users:
		s8_dic[user] = n_review_pos_price_r_dic[user]/n_review_dic[user]

	f_adequation_dic={}
	for user in l_users:
		f_adequation_dic[user] = (s6_dic[user]+s7_dic[user]+s8_dic[user])/3

	q_r_friends_city = "match (res1:Restaurant)<-[c1:Critics]-(r1:Review)<-[w2:Wrote]-(u1:User)<-[Friend]-(u:User )-[w:Wrote]->(r:Review)-[c:Critics]->(res:Restaurant) where $c_name = res1.city  return u.user_id,count(r1)"
	q_r_friends = "match (res1:Restaurant)<-[Critics]-(r1:Review)<-[Wrote]-(u1:User)<-[Friend]-(u:User ) return u.user_id,count(r1)"
	n_r_friends_city = graph.run(q_r_friends_city,c_name=city).to_table()
	n_r_friends = graph.run(q_r_friends).to_table()
	n_r_friends_city_dic = res_to_dict(n_r_friends_city)
	n_r_friends_dic = res_to_dict(n_r_friends)

	s9_dic = {}
	for user in l_users:
		user_r_friends = n_r_friends_dic[user]
		if user_r_friends>0:
			s9_dic[user] = n_r_friends_city_dic[user]/user_r_friends
		else:
			s9_dic[user] = 0

	f_geo_dic = s9_dic

	total_score_dic = {}
	for user in l_users:
		total_score_dic[user]=0.3*f_centralite_dic[user] + 0.3*f_validite_dic[user] + 0.3*f_adequation_dic[user] + 0.1*f_geo_dic[user]
	return total_score_dic 


score1 = build_score('Wilmington',['casual'],['Pizza','Burgers','Italian'],1)
score2 = build_score('Wilmington',['casual','romantic'],['Chinese'],2)
score3 = build_score('Wilmington',['hipster'],['Nightlife','Bars'],1)
score4 = build_score('New Castle',['casual','classy'],['Coffee & Tea'],2)
score5 = build_score('New Castle',['classy'],['Seafood'],1)

# import json

# with open('json/score1.json', "w") as outfile:
# 	json.dump(score1,outfile)

# with open('json/score2.json', "w") as outfile:
# 	json.dump(score2,outfile)

# with open('json/score3.json', "w") as outfile:
# 	json.dump(score3,outfile)

# with open('json/score4.json', "w") as outfile:
# 	json.dump(score4,outfile)

# with open('json/score5.json', "w") as outfile:
# 	json.dump(score5,outfile)
