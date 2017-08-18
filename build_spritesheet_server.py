import sys
import os.path
from PIL import Image
import math
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import parse
import io
import json
import base64
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--image_size", help="The size every image would be resized to.", type=int)
parser.add_argument("--images_path", help="The path to the folder containing all the images.")

args = parser.parse_args()

path = args.images_path

IMG_SIZE = args.image_size

ID_img_map = {}

print("Loading images from %s" % path)

for directory, subdirectories, files in os.walk(path):
	file_count = len(files)
	parsed = 0
	prev_completed_per = -1
	for file in files:
		try:
			photo_path = "/Users/danielzautner/projects/facebook_profiles_downloader/photos/" + file
			ID = file.split('.')[0]
			ID_img_map[ID] = Image.open(photo_path).resize((IMG_SIZE, IMG_SIZE), Image.ANTIALIAS)
			parsed += 1
			completed_per = math.floor(parsed / file_count * 100)
			if completed_per > prev_completed_per:
				print('Loaded %s%% of the images' % completed_per)
				prev_completed_per = completed_per
		except Exception as e:
			print("%s. skipping." % e)
			pass



def make_spritesheet(ids):
	count = len(ids)
	images_per_row = math.ceil(math.sqrt(count))
	width = height = images_per_row * IMG_SIZE
	spritemap = Image.new('RGB', (width,height))
	curr = 0
	coordinates = {}
	for ID in ids:
		try:
			current_row = math.floor(curr / images_per_row)
			x = (curr - (current_row * images_per_row)) * IMG_SIZE
			y = current_row * IMG_SIZE
			coordinates[ID] = (x, y)
			curr += 1
			img = ID_img_map[ID]
			spritemap.paste(img, (x, y))			
		except Exception as e:
			print(e)
			pass
	return (spritemap, coordinates)



# HTTPRequestHandler class
class RequestHandler(BaseHTTPRequestHandler):

	def writeJson(self, dict):
		self.wfile.write(json.dumps(dict).encode("utf-8"))

	def do_GET(self):
		self.send_response(200)
		self.send_header('Content-type', 'application/json')
		self.end_headers()
		params = parse.parse_qs(self.path[2:])
		if not 'ids' in params:
			self.writeJson({ 'error': "missing ids field" })
		ids = params['ids'][0].split(',')
		img, coordinates = make_spritesheet(ids)
		imgByteArr = io.BytesIO()
		img.save(imgByteArr, format='JPEG')

		content = base64.b64encode(imgByteArr.getvalue())
		self.writeJson({
			'image': "%s" % content,
			'coordinates': coordinates,
			'error': None
		})
		return

def run():
	print('starting server...')
	server_address = ('127.0.0.1', 9999)
	httpd = HTTPServer(server_address, RequestHandler)
	print('running server...')
	httpd.serve_forever()

run()