from nltk.parse.stanford import StanfordDependencyParser
from pprint import pprint
from django.utils.encoding import smart_str, smart_unicode
import urllib
import cv2
import numpy as np
import requests 
import sys
from PIL import Image
import os
from pprint import pprint
from googleapiclient.discovery import build
import pickle
import string as string_lib
import re
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
# import CLEANSTRING as cleanstr
import codecs

# below 3 lines are python wrapper for Stanford CoreNLP java
path_to_jar = 'C:\Users\IBM_ADMIN\Documents\stanford CoreNLP\stanford-corenlp-full-2015-12-09\stanford-parser.jar'
path_to_models_jar = 'C:\Users\IBM_ADMIN\Documents\stanford CoreNLP\stanford-corenlp-full-2015-12-09\stanford-parser-3.4.1-models.jar'
dependency_parser = StanfordDependencyParser(path_to_jar=path_to_jar, path_to_models_jar=path_to_models_jar)

# following is the instance of object for calling Google API
service = build("customsearch", "v1",developerKey="AIzaSyDYdBNOGtXLPmbSAACf7vTLw2PTShsa-ms")

# these are the global vairables that would be stored once executed
main_query_entities = {} #store the entities(head nouns of the query i.e object) of the main query
main_query_instruction_num = {}  # holds the order in which queriers should appear of the whole instruction-set(to represent multiple images for a single instruction in a sequentilal order)
main_query_location = {} #location of image directory for each query
entity_sub_pos = {} #hold position of entites of a single instruction for which images are to be displayed
					#since it is globally declared, it stores record of entites of every instruction

# for pre-processing of user-provided text
p = re.compile('\([^)]*\)') # this removes any bracket enclosed text from instructions-set.
wordnet_lemmatizer = WordNetLemmatizer()
stop = stopwords.words('english')

## this class extracts main_queries and their corresponding tags to be fetched for image-serach in Google API
class entites_extraction:
	def __init__(self, words_pos):
		self.words_pos = words_pos

	# Following function extracts action-verbs and their dependent nouns to form main_queries
	def sub_extract_entities(self,main_query,tags, items, nouns):

		if len(items.keys()) != 0:
			for item in items:
				tag = ""
				if not items[item]:
					main = item
					main_query_entities[main] = ''
					main_query.append(main)
					entity_sub_pos[smart_str(main)] = self.words_pos[smart_str(item)]
				else:
					main = item + " "
					for index, noun in enumerate(items[item]):
						if index == 0:
							if noun in nouns.keys():
								temp = ""
								for adj in nouns[noun]:
									temp += adj + " "
								temp = temp + noun
							else:
								temp = noun

							main += temp

							main_query_entities[main] = wordnet_lemmatizer.lemmatize(smart_str(noun))
							main_query.append(main)
							entity_sub_pos[smart_str(main)] = self.words_pos[smart_str(item)]

							if noun in nouns.keys():
								del nouns[noun]
						else:
							if noun in nouns.keys():
								temp = ""
								for adj in nouns[noun]:
									temp += adj + " "
								temp = temp + noun
							else:
								temp = noun
							tag = temp + ","
				tags.append(tag)
		return (main_query,tags,nouns)


	# for extraction of remaining nouns of the instructions after having extracted head action verbs and their dependent nouns
	def sub_extract_remaining_nouns(self, main_query,tags,nouns):
		if len(nouns.keys()) != 0:
			for noun in nouns:
				tag = ""
				tags.append(tag)
				if not nouns[noun]:
					main_query_entities[noun] = wordnet_lemmatizer.lemmatize(smart_str(noun))
					main_query.append(noun)
					entity_sub_pos[smart_str(noun)] = self.words_pos[smart_str(noun)]
				else:
					temp = ""
					for adj in nouns[noun]:
						temp += adj + " "
					main = temp + noun
					main_query_entities[main] = wordnet_lemmatizer.lemmatize(smart_str(noun))
					main_query.append(main)
					entity_sub_pos[smart_str(main)] = self.words_pos[smart_str(noun)]

		return (main_query,tags)



## main function for extracting entities that calls the class entites_extraction
def extract_entities(verbs,nouns,error,instruction):
	main_query =[]
	tags = []

# for getting position of words in a sentence without any punctuations and extra spaces.
	s = smart_str(instruction)
	s = p.sub('', s)
	s = s.translate(string_lib.maketrans("",""), string_lib.punctuation)
	s = re.sub(' +',' ',s)
	l= s.split()
	words_pos = dict((s, l.index(s)+1) for s in set(l))
	# print words_pos
	obj = entites_extraction(words_pos)
	(main_query, tags, nouns) = obj.sub_extract_entities(main_query, tags, verbs, nouns)
	(main_query, tags, nouns) = obj.sub_extract_entities(main_query, tags, error, nouns)
	(main_query, tags) = obj.sub_extract_remaining_nouns(main_query, tags, nouns)
	return (main_query, tags)

	## creating grammar rules for extraction of entities
class create_grammar:

	def __init__(self, instruction):
		self.instruction = instruction


	def grammar(self):
		result = dependency_parser.raw_parse(self.instruction)
		dep = result.next()
		dependency_parsed = list(dep.triples())
		print dependency_parsed

		# identify_other_verbs_or_nouns are relations to identify other verbs and nouns associated with our main_verb
		identify_other_verbs_or_nouns = ['conj','ccomp','advcl','nmod','advmod']
		# object of the main_verb. For the time being subject of the verb is skipped.
		for_verb_tags = ['dobj']
		# for modifiers of nouns
		for_noun_tags = ['num','nn','predet','amod','nummod','advmod','appos','preconj','number','compound']
		verbs= {}
		nouns = {}
		error = {}
		for item in dependency_parsed:
			head = smart_str(item[0][0]).translate(string_lib.maketrans("",""), string_lib.punctuation)
			head_tag = item[0][1]
			dependent = smart_str(item[2][0]).translate(string_lib.maketrans("",""), string_lib.punctuation)
			dependent_tag =item[2][1]
			relation = item[1]
			
			if head not in stop: # to avoid any stop words as heads
				if head_tag.startswith('V'):
					# if head not in verbs.keys():
					# 		verbs[head] =[]
					if relation in identify_other_verbs_or_nouns:
						if head not in verbs.keys():
							verbs[head] =[]
						if dependent_tag.startswith('V') and dependent not in stop:
							 if dependent not in verbs.keys():
								verbs[dependent] = []
						elif dependent_tag.startswith('J'):  #specifically for xcomp and ccomp relations 
							if dependent not in stop:	
								verbs[head].append(dependent)
						elif dependent_tag.startswith('N') and dependent not in stop:
							verbs[head].append(dependent)
							if dependent not in nouns.keys():
								nouns[dependent] = []
					elif relation in for_verb_tags:
						if head not in verbs.keys():
							verbs[head] =[]
						if dependent not in stop:		
							verbs[head].append(dependent)
					elif relation == 'dep': # 'dep' relation occurs when system fails to determine dependency relation between the words.
						if head not in error.keys() and head not in verbs.keys(): # to avoid the error from giving main_query already present in verbs
							error[head] =[]
						if dependent not in stop:
							error[head].append(dependent)
					
				if head_tag.startswith('N'):
					if relation in for_noun_tags:
						if head not in nouns.keys():
							nouns[head] =[]
						nouns[head].append(dependent)
					elif relation == 'conj':
						if head not in nouns.keys():
							nouns[head] =[]
						if dependent not in nouns.keys() and dependent not in stop:
							nouns[dependent] =[]
					elif relation == 'nmod' and dependent_tag.startswith('N'):
						if head not in nouns.keys():
							nouns[head] =[]
						nouns[head].append(dependent)
					elif relation == 'dep':
						if head not in error.keys() and head not in verbs.keys():
							error[head] =[]
						error[head].append(dependent)
				
		# print verbs
		# print nouns
		# print error
		return extract_entities(verbs,nouns,error,self.instruction)

## class images save images for the queries 
class images:

	def __init__(self,main_query,tags,topic):
		self.main_query = main_query
		self.tags = tags
		self.topic = topic

	def save_images(self,instruction_num):

		for index, query in enumerate(self.main_query):
			# order of the entities are stored as per the position of their head verb/noun in the original instruction
			# ex: first entity of first instruction is stored as 1001(if entity is also present at the beginning of the sentence)
			main_query_instruction_num[(instruction_num + 1)*1000 + entity_sub_pos[query]] = query

			newpath =  "C:\Users\IBM_ADMIN\Documents\prototype\#" + str(instruction_num+1) + '\\' + query
			main_query_location[query] = newpath
			if not os.path.exists(newpath): 
				os.makedirs(newpath)		
			res = service.cse().list(
			q= query,								# query for which images are to be searched
			cx='014813793344385571915:g69yuti-moi',
			searchType='image',
			num=6, 									# specify number of images to be saved for each query(if limit exceeds, resort to a small number)
			imgType='clipart',
			fileType='jpg',
			imgSize = 'large',
			orTerms = self.tags[index],				## extract this from the main topic(serves as tags for each image)
			exactTerms = self.topic,
			safe= 'off',
			imgColorType = 'color'
			).execute()
			for iteration, item in enumerate(res['items']):
			    link = item['link']
			    req = urllib.urlopen(link)
			    arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
			    img = cv2.imdecode(arr,-1)
			    urllib.urlretrieve(smart_str(link),newpath + '\\' + query + '_'+str(iteration + 1) +  ".jpg")

def main(topic):
	newpath = "C:\Users\IBM_ADMIN\Documents\prototype\\"
	with open(newpath + "instructions.txt",'r') as f:
		instructions = (line.rstrip() for line in f) # All lines including the blank ones
		instructions = list(line for line in instructions if line) # Read only Non-blank lines

	for instruction_num, instruction in enumerate(instructions):
		instruction = instruction.replace("Image Title: ","")
		instruction = instruction.replace("\n","")
		instruction =  p.sub('', instruction) #for ignoring brackets
		# for removing punctuation (can use CLEANSTRING.py for manual implementation)
		instruction = smart_str(instruction.translate(string_lib.maketrans("",""), string_lib.punctuation))
		print instruction
		grammar_obj = create_grammar(instruction)
		(main_query, tags) = grammar_obj.grammar()
		print main_query
		print tags

	## uncomment to store images and global variables in computer memory.

	# 	newpath = "C:\Users\IBM_ADMIN\Documents\prototype\#" + str(instruction_num+1)
	# 	if not os.path.exists(newpath): 
	# 		os.makedirs(newpath)
	# 	image_obj = images(main_query,tags,topic)
	# 	image_obj.save_images(instruction_num)

	# pickle.dump(main_query_entities, open( "C:\Users\IBM_ADMIN\Documents\prototype\main_query_entities.p", "wb" ) )
	# pickle.dump(main_query_instruction_num, open( "C:\Users\IBM_ADMIN\Documents\prototype\main_query_instruction_num.p", "wb" ) )
	# pickle.dump(main_query_location, open( "C:\Users\IBM_ADMIN\Documents\prototype\main_query_location.p", "wb" ) )


## use this class only for training purposes. This class extracts images for classifier training

class training:
	def __init__(self, topic):
		self.topic = topic

	## this function reads the instructions from the database to save entites(object and subject of the sentence) for classifier-training
	def save_entities_for_training(self):
		directory_num =1
		count =1
		word_count ={}
		while(directory_num==1):
			print directory_num + 1
			newpath = 'C:\Users\IBM_ADMIN\Documents\database_test\#' + str(directory_num + 1)
			if os.path.exists(newpath + '\image_title.txt'):
				with open(newpath + '\image_title.txt','r') as f:
						data = f.readlines()
				for title in data:
					raw_line = title.replace("Image Title: ","")
					raw_line = raw_line.replace("\n","")
					raw_line = p.sub('',raw_line)
					# raw_lint = cleanstr.main(raw_line)
					raw_line = smart_str(raw_line.translate(string_lib.maketrans("",""), string_lib.punctuation))
					print raw_line
					grammar_obj = create_grammar(raw_line)
					(main_query, tags) = grammar_obj.grammar()
			else:
				count = 1
				flag = True
				while (flag != False):
					newpath = 'C:\Users\IBM_ADMIN\Documents\database_test\#' + str(directory_num + 1) +'\#' + str(count)
				
					with open(newpath + '\image_title.txt','r') as f:
						data = f.readlines()
					
					for title in data:
						raw_line = title.replace("Image Title: ","")
						raw_line = raw_line.replace("\n","")
						raw_line = p.sub('',raw_line)
						# raw_lint = cleanstr.main(raw_line)
						raw_line = smart_str(raw_line.translate(string_lib.maketrans("",""), string_lib.punctuation))
						print raw_line
						grammar_obj = create_grammar(raw_line)
						(main_query, tags) = grammar_obj.grammar()
						# print entites
					count +=1
					newpath = 'C:\Users\IBM_ADMIN\Documents\database_test\#' + str(directory_num + 1) +'\#' + str(count)
					if not os.path.exists(newpath):
						flag = False
			directory_num += 1

		for query in main_query_entities:
			entity = main_query_entities[query]
			if entity not in word_count:
				word_count[entity] = 1
				with open('C:\Users\IBM_ADMIN\Documents\database_test\list.txt','a') as file:
					file.write(smart_str(entity) + '\n')                                      #saving the entities in a .txt file
			else:
				word_count[entity] += 1

	def save_images_for_training(self):
		path_entites_list = 'C:\Users\IBM_ADMIN\Documents\database_test\list.txt'
		img_size_list = ['large', 'medium','xlarge','xxlarge'] # for retrieval of more images from google-API

		# reads entities from list.txt
		with codecs.open(path_entites_list,'r',encoding="utf-8-sig") as f: #to skip the BOM sequence
			entities = (line.rstrip() for line in f)
			entities = list(line for line in entities if line)
		print entities
		for entity in entities:
			path_training_images = 'C:\Users\IBM_ADMIN\Documents\prototype\\training' + '\\' + smart_str(entity)
			if not os.path.exists(path_training_images): 
				os.makedirs(path_training_images)
			iteration = 0
			for size in img_size_list:
				res = service.cse().list(
				q = smart_str(entity),
				cx = '014813793344385571915:g69yuti-moi',
				searchType = 'image',
				num = 10,
				imgType = 'clipart',
				fileType = 'jpg',
				imgSize = size,			
				exactTerms = self.topic,	## extract this from the main topic
				safe = 'off',
				imgColorType = 'color'
				).execute()
				for item in res['items']:
				    link = item['link']
				    req = urllib.urlopen(link)
				    arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
				    img = cv2.imdecode(arr,-1)
				    urllib.urlretrieve(smart_str(link),path_training_images +'\\' + '#_' + str(iteration + 1) +  ".jpg")
				    iteration += 1


if __name__ == "__main__":

	topic ="coffee" # extracted from title
	
	## for training
	training_obj = training(topic)
	# training_obj.save_entities_for_training()
	training_obj.save_images_for_training()

	## for testing
	# main(topic)
	
	## for single line testing, uncomment below written code

	# grammar_obj = create_grammar('Sort the eggs and place them in a saucepan or pot.')
	# (main_query, tags) = grammar_obj.grammar()
	# print main_query
	# print tags
	# image_obj = images(main_query,tags,topic)
	# image_obj.save_images(instruction_num)
