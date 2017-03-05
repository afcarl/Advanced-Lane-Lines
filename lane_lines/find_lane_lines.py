#!/bin/python

import numpy as np
import cv2

class Line():
	def __init__(self, fit, radius_of_curvature, line_base_pos, allx, ally):
		# if the line passes validation
		self.valid = True  
		# #polynomial coefficients for the fit
		self.fit = fit
		#radius of curvature of the line in some meters
		self.radius_of_curvature = radius_of_curvature 
		#distance in meters of vehicle center from the line
		self.line_base_pos = None 
		#x values for detected line pixels
		self.allx = allx
		#y values for detected line pixels
		self.ally = ally

def find_lane_lines(image, original_image, left_fit=None, right_fit=None):
	window_height = 50
	window_width = 50
	margin = 50

	if left_fit is None or right_fit is None:
		# if no previous lane is available, start by finding a line of best fit using
		# a sliding window convolution approach.
		centroids = find_window_centroids(image, window_height, window_width, margin)
		left_fit, right_fit = fit_lines_to_image(centroids[0], centroids[1])

	# using the previous line, or the sliding window convolution, search for points around
	# the lines and use these to fit a new line of best fit.
	return find_lane_lines_from_fit(image, left_fit, right_fit, margin)

def find_lane_lines_from_fit(image, original_image, left_fit, right_fit, margin):
	nonzero = image.nonzero()
	nonzeroy = np.array(nonzero[0])
	nonzerox = np.array(nonzero[1])
	left_lane_inds = ((nonzerox > (left_fit[0]*(nonzeroy**2) + left_fit[1]*nonzeroy + left_fit[2] - margin)) & (nonzerox < (left_fit[0]*(nonzeroy**2) + left_fit[1]*nonzeroy + left_fit[2] + margin))) 
	right_lane_inds = ((nonzerox > (right_fit[0]*(nonzeroy**2) + right_fit[1]*nonzeroy + right_fit[2] - margin)) & (nonzerox < (right_fit[0]*(nonzeroy**2) + right_fit[1]*nonzeroy + right_fit[2] + margin)))  

	# Again, extract left and right line pixel positions
	leftx = nonzerox[left_lane_inds]
	lefty = nonzeroy[left_lane_inds] 
	rightx = nonzerox[right_lane_inds]
	righty = nonzeroy[right_lane_inds]
	# Fit a second order polynomial to each
	left_fit = np.polyfit(lefty, leftx, 2)
	right_fit = np.polyfit(righty, rightx, 2)

	ym_per_pix = 30/300 # meters per pixel in y dimension
	xm_per_pix = 3.7/240 # meters per pixel in x dimension

	left_radius, right_radius = find_radius(image, left_fit, right_fit, leftx, lefty, rightx, righty, ym_per_pix, xm_per_pix)

	left_y_pts = np.linspace(0, image.shape[0] - 1, image.shape[0])
	right_y_pts = np.linspace(0, image.shape[0] - 1, image.shape[0])
	left_x_pts = left_fit[0]*left_y_pts**2 + left_fit[1]*left_y_pts + left_fit[2]
	right_x_pts = right_fit[0]*right_y_pts**2 + right_fit[1]*right_y_pts + right_fit[2]

	center_position = find_line_base_pos(image. original_image, left_fit, right_fit, xm_per_pix)

	return [Line(left_fit, left_radius, center_position, left_y_pts, left_x_pts), 
	Line(right_fit, right_radius, center_position, right_y_pts, right_x_pts)]

def find_radius(image, left_fit, right_fit, leftx, lefty, rightx, righty, ym_per_pix, xm_per_pix):
	y_eval = np.max(image.shape[0] - 1)

	# Fit new polynomials to x,y in world space
	left_fit_cr = np.polyfit(lefty*ym_per_pix, leftx*xm_per_pix, 2)
	right_fit_cr = np.polyfit(righty*ym_per_pix, rightx*xm_per_pix, 2)
	# Calculate the new radii of curvature
	left_curverad = ((1 + (2*left_fit_cr[0]*y_eval*ym_per_pix + left_fit_cr[1])**2)**1.5) / np.absolute(2*left_fit_cr[0])
	right_curverad = ((1 + (2*right_fit_cr[0]*y_eval*ym_per_pix + right_fit_cr[1])**2)**1.5) / np.absolute(2*right_fit_cr[0])
	# Now our radius of curvature is in meters
	return (left_curverad, right_curverad)

def find_line_base_pos(warped_image, original_image, left_fit, right_fit, xm_per_pix):
	center = int(original_image.shape[1] / 2)
	left_x_point = left_fit[0]*(warped_image.shape[0]**2) + left_fit[1]*warped_image.shape[0] + left_fit[2]
	right_x_point = right_fit[0]*(warped_image.shape[0]**2) + right_fit[1]*warped_image.shape[0] + right_fit[2]
	# taken from RoadTransformer.src
	max_pixel = 1200
	min_pixel = 70

	lane_center_warped = int((right_x_point - left_x_point) / 2)
	lane_center = min_pixel + int(lane_center_warped * ((max_pixel - min_pixel) / warped_image.shape[1]))

	return (lane_center - center) * xm_per_pix


def fit_lines_to_image(left_centroids, right_centroids):
	lefty = [c[1] for c in left_centroids]
	leftx = [c[0] for c in left_centroids]
	righty = [c[1] for c in right_centroids]
	rightx = [c[0] for c in right_centroids]
	left_fit = np.polyfit(lefty, leftx, 2)
	right_fit = np.polyfit(righty, rightx, 2)
	return (left_fit, right_fit)

def initial_centers(image):
	histogram = np.sum(image[image.shape[0]/2:,:], axis=0)
	midpoint = np.int(histogram.shape[0]/2)
	leftx_base = np.argmax(histogram[:midpoint])
	rightx_base = np.argmax(histogram[midpoint:]) + midpoint
	return (leftx_base, rightx_base)

def find_window_centroids(image, window_width, window_height, margin):
  left_center, right_center = initial_centers(image)
  left_centroids = find_lane_centroids(image, left_center, window_width, window_height, margin)
  right_centroids = find_lane_centroids(image, right_center, window_width, window_height, margin)
    
  return (left_centroids, right_centroids)

def find_lane_centroids(image, center, window_width, window_height, margin):
  centroids = []

  for level in range(int(image.shape[0]/window_height)):
    height = int(image.shape[0]-(level*window_height))
    found_centroid = find_window_centroid(image, window_width, window_height, margin, center, height)
    
    if found_centroid is not None:
      center = found_centroid
      centroids.append((found_centroid, height))
    
  return centroids
  
def find_window_centroid(image, window_width, window_height, margin, center, height):
  h_start = max(center - int(margin/2) - int(window_width/2), 0)
  h_end = min(center + int(margin/2) + int(window_width/2), image.shape[1])
  v_start = height - window_height
  v_end = height
  
  image_layer = np.sum(image[v_start:v_end, h_start:h_end], axis=0)
  
  # If we found very few pixels over all, skip this point. 
  # It could be a place with no lines
  if np.sum(image_layer) < 30:
    return None
  
  window = np.ones(window_width)
  conv_signal = np.convolve(window, image_layer, 'same')
  
  return np.argmax(conv_signal) + h_start