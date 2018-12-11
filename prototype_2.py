import os
import cv2
from scipy.spatial import distance as dist
import matplotlib.pyplot as plt
import numpy as np
import prototype
import operator
import pickle
from django.utils.encoding import smart_str, smart_unicode
import math

## for the time being, returning the first image from set of images
def acquire_base_image(directory):
	image_paths = os.listdir(smart_str(directory))
	img_loc = directory +'\\' + smart_str(image_paths[0])
	return img_loc    



def get_most_coherent_image(base_image, directory):
	index = {}
	images = {}
	image = cv2.imread(smart_str(base_image))
	images[base_image] = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
	# creating 8-bins per channel
	base_hist = cv2.calcHist([image], [0, 1, 2], None, [8, 8, 8],[0, 256, 0, 256, 0, 256])
	base_hist = cv2.normalize(base_hist,base_hist).flatten()
	
	image_paths = os.listdir(smart_str(directory))
	for imagePath in image_paths:
		img_loc = directory +'\\' + smart_str(imagePath)
		image = cv2.imread(img_loc)
		images[img_loc] = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
		hist = cv2.calcHist([image], [0, 1, 2], None, [8, 8, 8],
				[0, 256, 0, 256, 0, 256])
		hist = cv2.normalize(hist,hist).flatten()
		index[img_loc] = hist

	 # METHOD #1: UTILIZING OPENCV
	# initialize OpenCV methods for histogram comparison
	# OPENCV_METHODS = (
	# 	("Correlation", cv2.HISTCMP_CORREL),
	# 	("Chi-Squared", cv2.HISTCMP_CHISQR),
	# 	("Intersection", cv2.HISTCMP_INTERSECT), 
	# 	("Hellinger", cv2.HISTCMP_BHATTACHARYYA))
	methodName = "Correlation"
	method = cv2.HISTCMP_CORREL
	# loop over the comparison methods
	# for (methodName, method) in OPENCV_METHODS:
		# initialize the results dictionary and the sort
		# direction
	results = {}
	reverse = False

	# if we are using the correlation or intersection
	# method, then sort the results in reverse order
	if methodName in ("Correlation", "Intersection"):
		reverse = True

	# loop over the index
	for (k, hist) in index.items():
		# compute the distance between the two histograms
		# using the method and update the results dictionary
		d = cv2.compareHist(base_hist, hist, method)
		results[k] = d

	# # sort the results
	results = sorted([(v, k) for (k, v) in results.items()], reverse = reverse)
	return results[0][1]

def print_final_output(final_images):
	fig = plt.figure("Result")
	fig.suptitle("How to do reverse crunches", fontsize = 20)
	newpath = "C:\Users\IBM_ADMIN\Documents\prototype\\"
	with open(newpath + "instructions.txt",'r') as f:
		instructions = (line.rstrip() for line in f) # All lines including the blank ones
		instructions = list(line for line in instructions if line) # Non-blank lines
	size =len(instructions)
	image_num = 1
	for instruction_num, instruction in enumerate(instructions):
		instruction = instruction.strip('\n')
		image_list = final_images[math.floor(instruction_num+1)]
		# length = len(image_list)
		for index, pic in enumerate(image_list):
			ax = fig.add_subplot(size, size , image_num)
			if index == 0:
				ax.set_title(smart_str(instruction))
			img = cv2.imread(pic)
			plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
			plt.axis("off")
			image_num += 1
		image_num = (1 + instruction_num)*size + 1
	plt.show()
	open(newpath + "instructions.txt",'w').close() # to clear txt file after image is displayed


def main():
	base_images = {} # helps to resolve the problem of coherency
	final_images = {}
	temp = {}
	main_query_entities = pickle.load( open( "C:\Users\IBM_ADMIN\Documents\prototype\main_query_entities.p", "rb" ) )
	main_query_order = pickle.load( open( "C:\Users\IBM_ADMIN\Documents\prototype\main_query_instruction_num.p", "rb" ) )
	main_query_location = pickle.load( open( "C:\Users\IBM_ADMIN\Documents\prototype\main_query_location.p", "rb" ) )
	# print main_query_order
	sorted_list = sorted(main_query_order.items(), key=operator.itemgetter(0))
	# print sorted_list

	# for each entity stored in the list, base image is extracted
	for index, item in enumerate(sorted_list):
		query = smart_str(item[1])
		num = math.floor(item[0]/1000)
		if  num not in final_images.keys():
			final_images[num] = []

		entity = main_query_entities[query]
		if entity not in temp.keys():
			temp[entity] = query
			final_path = acquire_base_image(main_query_location[query])
			final_images[num].append(final_path)
			base_images[item[0]] = final_path
		else:
			base_image = base_images[main_query_order[temp[main_query_entities[query]]]]
			final_path = get_most_coherent_image(base_image, main_query_location[query])
			final_images[num].append(final_path)
			base_images[item[0]] = final_path

	# print final_images
	print_final_output(final_images)


if __name__ == '__main__':

	# prototype.main() 
	main()

