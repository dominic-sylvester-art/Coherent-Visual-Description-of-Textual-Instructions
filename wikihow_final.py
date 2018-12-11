import os
import urllib
from bs4 import BeautifulSoup
import cv2
import numpy as np
import requests	
import sys
from PIL import Image
from django.utils.encoding import smart_str, smart_unicode




def print_images_case1(tags2,tags1,title,index,query_path,query):
	newpath = query_path
	with open(newpath + "\image_title.txt",'w') as f:
		for ttle in title:
			f.write("Image Title: " + smart_str(ttle) + "\n")
	with open(newpath + "\image_info.txt",'w') as f:		
		for tag in tags1:
			f.write("Image Info: ")
			f.write(smart_str(tag.contents))
			f.write("\n")		
	with open(newpath + "\image_url.txt",'w') as f:		
		for tag2 in tags2:
			url = tag2.img.get('data-src')
			f.write("Image url: ")
			f.write(smart_str(url))
			f.write("\n")
	for i, tag2 in enumerate(tags2):
		url = tag2.img.get('data-src')
		req = urllib.urlopen(url)
		arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
		img = cv2.imdecode(arr,-1)

		# print "saving image"
		cv2.imwrite(newpath + '\#' + str(i + 1) + '.png',img)




def print_images_case2(tags2,tags1,method,title,index,query_path,query):
	newpath = query_path + '\#' + str(index + 1)
	if not os.path.exists(newpath): 
		os.makedirs(newpath)

	with open(newpath + "\method_info.txt",'w') as f:
		f.write("Page Url:" + smart_str(query)  +  '\n')
		f.write(smart_str(method.string))

	with open(newpath + "\image_title.txt",'w') as f:
		for ttle in title:
			f.write("Image Title: " + smart_str(ttle) + "\n")
	with open(newpath + "\image_info.txt",'w') as f:		
		for tag in tags1:
			f.write("Image Info: ")
			f.write(smart_str(tag.contents))
			f.write("\n")		
	with open(newpath + "\image_url.txt",'w') as f:		
		for tag2 in tags2:
			url = tag2.img.get('data-src')
			f.write("Image url: ")
			f.write(smart_str(url))
			f.write("\n")
	

	for i, tag2 in enumerate(tags2):
		url = tag2.img.get('data-src')
		req = urllib.urlopen(url)
		arr = np.asarray(bytearray(req.read()), dtype=np.uint8)
		img = cv2.imdecode(arr,-1)
		cv2.imwrite(newpath + '\#' + str(i + 1) + '.png',img)		

		# img = cv2.resize(img,(960,540))   # resizing images so that they can fit 					#to print images from wikihow
		# cv2.imshow(str(index+1)+'_'+title[i],img)
		# if cv2.waitKey() & 0xff == 27:
		#  	quit()

def extract(m_list,s):
	for temp in m_list:
		if smart_str(temp.string) == "None":
			s = extract(temp,s)
		else:
			s = s + smart_str(temp.string)
	return s


def find_titles(tags1):
	title = []
	for tag1 in tags1:
		s=""
		st=extract(tag1.contents,s)
		title.append(st)
	return title

def save_queries(queries_list):
	with open("C:\Users\IBM_ADMIN\Documents\database\queries_list_test.txt",'w') as f:
		for index, query in enumerate(queries_list):
			f.write(query + "\n")

def store_methods(test_tag,newpath):
	with open(newpath + '\method_titles.txt','w') as f:
		for index, method_tag in enumerate(test_tag):
				method = method_tag.find('span',class_='mw-headline')
				f.write(smart_str(method.string) + "\n")

	


# wiki = "http://www.wikihow.com/index.php?title=Special:PopularPages/%26limit%3D1&limit=5000&offset=5000"  #enter here the wikihow url containing list of queries
# page = urllib.urlopen(wiki)
# soup = BeautifulSoup(page,'lxml')

# qlist = soup.find('ol', class_='special')
# queries_list_tag = qlist.find_all('a')
# queries_list = []
# for query in queries_list_tag:
# 	queries_list.append("https://www.wikihow.com" + query.get("href"))    						#saving the queries

#del(queries_list[0])

#save_queries(queries_list) #to save query list in .txt format

with open("C:\Users\IBM_ADMIN\Documents\qtest_list.txt",'r') as f:
	queries_list=f.readlines()


directory_num = 11
for query in queries_list:
	directory_num += 1
	# if directory_num + 1 < 9836:	
	# 	continue										            # use this if statement to control queries for which u wnat to run the program
	query = query.strip('\n')
	print "query num " + str(directory_num) +":"+ query	
		
	newpath = 'C:\Users\IBM_ADMIN\Documents\database_test\#' + str(directory_num)
	if not os.path.exists(newpath): 
		os.makedirs(newpath)


	page = urllib.urlopen(query)
	soup = BeautifulSoup(page,'lxml')


	test_tag = soup.find('div', class_='altblock')
	if test_tag is None:																		#case1: for queries with single method as a part of solution
		index=1
		title_tags = soup.find_all('b', class_='whb')
		title = find_titles(title_tags)
		image_tags = soup.find_all('div', class_='mwimg  largeimage  floatcenter ')
		text_tags=soup.find_all('div',class_='step')
		print_images_case1(image_tags,text_tags,title,index,newpath,query)

	else:																						#case2: for queries with multiple methods as a part of solution
		test_tag = soup.find_all('div', class_='section steps   sticky ')
		store_methods(test_tag,newpath)
		for index, method_tag in enumerate(test_tag):
			method = method_tag.find('span',class_='mw-headline')
			#print method.string					#displaying which method you are in

			title_tags = method_tag.find_all('b', class_='whb')		#finding titles
			title = find_titles(title_tags)

			text_tags=method_tag.find_all('div',class_='step')	
			image_tags = method_tag.find_all('div', class_='mwimg  largeimage  floatcenter ')			#displaying images
			print_images_case2(image_tags,text_tags,method,title,index,newpath,query)






