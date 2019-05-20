import os
import json
import numpy as np
import matplotlib.pyplot as pl

# credits to Balduin
def load_json_files():
	# load all json files in directory and return as list of json objects
	json_objects = []
	path = 'experiment'
	for f in os.listdir(path):
		json_objects.append(json.load(open(path + '/' + f)))
	return json_objects


def filter_illusion(json_objects, illusion_name='Popple Illusion'):
	# filter by illusion name, and sort by variation
	results = [[] for i in range(10)]  # length = number of variations
	for obj in json_objects:
		for data_point in obj:
			# print(data_point['illusionName'])
			if data_point['illusionName'] == illusion_name:
				results[data_point['variationID']].append(data_point)
	return results


def plot_results(results):
	hist = False
	if hist:
		for i in range(10):
			slider_vals = [(data_point['distortion']-data_point['sliderStart']) /
							(data_point['sliderEnd']-data_point['sliderStart']) for data_point in results[i]]
			print('variation {}: μ={:.2f}, σ={:.2f}'.format(
				i+1, np.mean(slider_vals), np.std(slider_vals)))
			pl.subplot(10, 1, i+1)
			pl.hist(slider_vals, bins=np.linspace(0, 1, 200))
	else:
		nx = 200
		xs = np.linspace(0, 1, nx)
		bins = 50
		gauss_width = 4 / bins
		for i in range(10):
			slider_vals = [(data_point['distortion']-data_point['sliderStart'])/(data_point['sliderEnd']-data_point['sliderStart']) for data_point in results[i]]
			colors = [data_point['inverted'] for data_point in results[i]]
			#slider_vals_large = np.tile(np.matrix(slider_vals).T, (1, nx))
			#xs_large = np.tile(xs, (len(slider_vals), 1))
			#gauss_pts = np.zeros((len(slider_vals), nx))
			#gauss_width = np.std(slider_vals)
			#gauss_pts = np.exp(-np.square(slider_vals_large - xs_large) / (2*gauss_width**2))
			#gauss_plot = np.sum(np.array(gauss_pts), axis=0)
			print('variation {}: μ={:.2f}, σ={:.2f}'.format(i+1, np.mean(slider_vals), np.std(slider_vals)))
			pl.subplot(10,1,i+1)
			# pl.plot(xs, gauss_plot/sum(gauss_plot)*nx)
			pl.plot(xs, np.exp(-np.square(xs - np.mean(slider_vals)) / (2*np.std(slider_vals)**2))*10 )
			# pl.subplot(10,1,i+1)
			colors = np.array(colors)
			slider_vals = np.array(slider_vals)
			pl.hist(slider_vals, bins=bins, normed =True)
			#for i in range(5):
			#pl.hist(slider_vals[colors==i+1], bins=np.linspace(0,1,50), normed=True)
	pl.show()

def main():
	json_objects = load_json_files()
	results = filter_illusion(json_objects)
	plot_results(results)

if __name__ == '__main__':
	main()
