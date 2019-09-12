import json


def json_to_xml(js, key=None, indent=0):
	if key is None:
		if type(js) is list:
			rv = ''
			for o in js:
				key = list(o.keys())[0]
				rv += json_to_xml(o[key], key)
			return rv
		elif 'imdata' in js:
			key = 'imdata'
		else:
			key = list(js.keys())[0]
			js = js[key]
	if key is 'imdata' and 'totalCount' in js:
		atts = f' totalCount="{js["totalCount"]}"'
		sub = ''
		for o in js['imdata']:
			subkey = str(list(o.keys())[0])
			sub += json_to_xml(o[subkey], subkey, indent + 2)
		return f'<{key}{atts}>\n{sub}</{key}>\n'
	elif 'attributes' in js:
		atts = ''
		for att in js['attributes'].keys():
			atts += f" {att}='{js['attributes'][att]}'"
		if 'children' in js:
			sub = ''
			for o in js['children']:
				subkey = str(list(o.keys())[0])
				sub += json_to_xml(o[subkey], subkey, indent + 2)
			return ' ' * indent + f'<{key}{atts}>\n{sub}</{key}>\n'
		else:
			return ' ' * indent + f'<{key}{atts}/>\n'
	else:
		print('fault')


def xml_to_json(xml):
	raise Exception("xml_to_json Procedure not ready yet!")
	while "<?" in xml and "?>" in xml:
		xml = xml.replace(xml[xml.find("<?"):xml.find("?>") + 2], "")
	return True


class Data(object):
	def __init__(self, content):
		if type(content) is str:
			if content.strip()[0] == '<':
				content = xml_to_json(content)
			else:
				content = json.loads(content)
		self.__content = content

	@property
	def content(self):
		return self.__content

	@property
	def json(self):
		return self.__content

	@property
	def xml(self):
		return json_to_xml(self.__content)

	@property
	def imdata(self):
		if 'imdata' in self.json:
			return self.json['imdata']
		return self.json

	@property
	def count(self):
		if type(self.json) is dict:
			if 'totalCount' in self.json:
				return int(self.json['totalCount'])
			else:
				raise Exception('totalCount key not found in output.')
		elif type(self.json) is list:
			return len(self.json)

	def attribute(self, attribute, keys=False):
		if type(attribute) is str:
			return [o[list(o)[0]]['attributes'][attribute] for o in self.imdata]
		elif type(attribute) is list:
			lst = []
			for o in self.imdata:
				if keys:
					sub = {a: o[list(o.keys())[0]]['attributes'][a] for a in attribute}
				else:
					sub = [o[list(o.keys())[0]]['attributes'][a] for a in attribute]
				lst.append(sub)
			return lst
		else:
			raise Exception('Invalid attribute type.  Must be String or List.')

	def value(self, attribute):
		value = self.attribute(attribute)
		if len(value) == 0:
			return None
		return value[0]

	def sum(self, attribute, printout=False, minimum=0):
		ret = {}
		for val in self.attribute(attribute):
			ret[val] = ret[val]+1 if val in ret else 0
		for val in list(ret.keys()):
			if ret[val] < minimum:
				_ = ret.pop(val)
		if printout:
			for val in ret:
				if ret[val] > minimum:
					print(f'{val}: {ret[val]}')
		else:
			return ret

	def print(self, index=None, style='json'):
		if index is not None:
			if type(index) is not int:
				raise Exception('Invalid index.  Must be an integer value')
			if not 0 <= index < self.count:
				raise Exception('Invalid index.  Input is out of bounds of output array.')
		if style == 'json':
			if index is None:
				print(json.dumps(self.json, indent=2))
			else:
				print(json.dumps(self.imdata[index], indent=2))
		elif style == 'xml':
			if index is None:
				print(self.xml)
			else:
				print(json_to_xml(self.imdata[index]))
		else:
			print(self.content)

	def save(self, filename, index=None, style='json'):
		if index is None and self.count == 1:
			index = 0
		else:
			if type(index) is not int:
				raise Exception('Invalid index.  Must be an integer value')
			if not 0 <= index < self.count:
				raise Exception('Invalid index.  Out of bounds of output array.')
		if style is 'xml':
			if index is None:
				out = self.xml
			else:
				out = self.json_to_xml(self.imdata[index])
		else:
			if index is None:
				out = json.dumps(self.imdata, indent=2)
			else:
				out = json.dumps(self.imdata[index], indent=2)
		file = open(filename, 'w')
		file.write(out)
		file.close()
