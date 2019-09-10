import fabric


def vrf_from_ctx(apic, ctx):
	d = apic.qr('fvCtx', filter=f'eq(fvCtx.seg, "{ctx}"').output
	if d.count <= 0:
		raise Exception(f'CTX, {ctx}, not found.')
	return d.value('dn').strip('uni/tn-').replace('/ctx-', ':')


def lookup_epg(apic, ctx, pctag):
	filter = f'and(eq(l3extInstP.scope, "{ctx}"), eq(l3extInstP.pcTag, "{pctag}"))'
	src = apic.qr('l3extInstP', filter=filter).output
	if src.count == 0:
		return None
	return src.value('dn').strip('uni/tn-').replace('out-', '').replace('instP-', '')


def policy_list(node, net=None):
	if net is None:
		return node.qr('actrlPfxEntry').output.attribute('dn')
	else:
		return node.qr('actrlPfxEntry', filter=f'eq(actrlPfxEntry.addr, "{net}")').output.attribute('dn')


def policy_check(apic, nodes, pol, net):
	pols = list(set(pol[0] + pol[1]))
	prt = ""
	if net is None:
		prt += f'\n  Missing from {nodes[0].name}:'
		for dn in pols:
			if dn not in pol[0]:
				ctx = dn[dn.find('[vxlan-')+7:dn.find(']')]
				vrf = vrf_from_ctx(apic, ctx)
				net = dn[dn.rfind('[')+1:-1]
				# print(f'node:{nodes[1].id} dn:{dn} ctx:{ctx} vrf:{vrf} net:{net}')
				epg = lookup_epg(apic, ctx, nodes[1].qr(dn).output.value('pcTag'))
				prt += f'\n    {vrf}   {net}   {epg}'
		if prt[-1] == ':':
			prt += '\n    none'
		return prt
	if len(pol[0] == 0):
		return f'\n  {nodes[0].name}: {net} not found.'
	else:
		for dn in pols:
			ctx = dn[dn.find('[vxlan-')+7:dn.find(']')]
			vrf = vrf_from_ctx(apic, ctx)
			net = dn[dn.rfind('[')+1:-1]
			if dn in pol[0]:
				epg = lookup_epg(apic, ctx, nodes[0].qr(dn).value('pcTag'))
				found = 'Found'
			else:
				epg = lookup_epg(apic, ctx, nodes[1].qr(dn).value('pcTag'))
				found = 'Missing'
			prt += f'\n  {nodes[0].name}: {found}  {vrf}  {net}  {epg}'
	return prt


# Check for policy mismatch between VPC pairs
def check(apic, net=None):
	vpcs = apic.qr('fabricExplicitGEp').data.attribute('dn')
	for vpc in vpcs:
		nodes = [apic.node(o) for o in apic.qr(vpc, target='children', target_class='fabricNodePEp').data.attribute('id')]
		prt = ""
		if nodes[0].check_connection() and nodes[1].check_connection():
			pols = [policy_list(node, net) for node in nodes]
			prt = "\nComparing %s and %s" % (nodes[0].name, nodes[1].name)
			prt += policy_check(apic, nodes, pols, net)
			nodes.reverse()
			pols.reverse()
			prt += policy_check(apic, nodes, pols, net)
		print(prt)


"""
# Collect l1PhysIf and ethpmPhysIf attributes, re-key them to node/interface and output to dictionary object
# if filename is provided, the data will be saved to file.
def interface_data(fabric, filename=None):
	import json
	ifc_query_data = fabric.qr('l1PhysIf', subtree='children', subtree_class='ethpmPhysIf').data
	data = {}
	for ifc in ifc_query_data.imdata:
		atts = ifc['l1PhysIf']['attributes']
		ethpmatts = ifc['l1PhysIf']['children'][0]['ethpmPhysIf']['attributes']
		dn = atts['dn']
		node = dn[dn.find('/node-')+6:dn.find('/sys')]
		physif = dn[dn.find('/phys-[')+7:-1]
		for att in ethpmatts:
			atts[f'ethpm-{att}'] = ethpmatts[att]
		data[f'{node}/{physif}'] = atts
	if filename is not None:
		file = open(filename, 'w')
		file.write(json.dumps(data, indent=2))
		file.close()
	return data
"""


def read_object(obj, head=None):
	attributes = obj['attributes']
	if head is not None:
		keys = list(attributes.keys())
		for key in keys:
			attributes[f'{head}-{key}'] = attributes.pop(key)
	if 'children' in obj:
		for i in range(len(obj['children'])):
			child = list(obj['children'][i].keys())[0]
			child_head = child if head is None else f'{head}-{child}'
			attributes.update(read_object(obj['children'][i][child], child_head))
	return attributes


# Collect l1PhysIf and ethpmPhysIf attributes, re-key them to node/interface and output to dictionary object
# if filename is provided, the data will be saved to file.
def interface_data(fabric, filename=None):
	import json
	ifc_query_data = fabric.qr('l1PhysIf', subtree='children', subtree_class='ethpmPhysIf').data
	data = {}
	for ifc in ifc_query_data.imdata:
		atts = read_object(ifc['l1PhysIf'])
		dn = atts['dn']
		node = dn[dn.find('/node-')+6:dn.find('/sys')]
		physif = dn[dn.find('/phys-[')+7:-1]
		data[f'{node}/{physif}'] = atts
	if filename is not None:
		file = open(filename, 'w')
		file.write(json.dumps(data, indent=2))
		file.close()
	return data


def endpoint_data(fabric, filename=None):
	import json
	endpoint_query_data = fabric.qr('fvCEp', subtree='full').data
	data = {}
	for endpoint in endpoint_query_data.imdata:
		atts = endpoint['fvCEp']['attributes']
		atts['reportingNodes'] = []
		for child in endpoint['fvCEp']['children']:
			key = list(child.keys())[0]
			if key == 'fvRsCEpToPathEp':
				atts[key] = child[key]['attributes']['tDn']
			if key =='fvIp':
				atts[key] = child[key]['attributes']['addr']
			if 'children' in child[key]:
				for subchild in child[key]['children']:
					key = list(subchild.keys())[0]
					if key == 'fvReportingNode':
						atts['reportingNodes'].append(subchild['fvReportingNode']['attributes']['id'])
		atts['reportingNodes'] = list(set(atts['reportingNodes']))
		atts['reportingNodes'].sort()
		data[atts['dn']] = atts
	if filename is not None:
		file = open(filename, 'w')
		file.write(json.dumps(data, indent=2))
		file.close()
	return data


# Compare two data sets from something like interface_data() to look for changes.
# input can be the data files or the raw dictionaries.
# attribute value is the attribute key to compare.
def compare_data(data1, data2, attribute=None):
	import os     # used to set for existance of file
	import json   # used to load json data
	dataset = []  # will hold data sets
	# Read data1 and data2 pamaters and load data sets
	for i in [0, 1]:
		data = [data1, data2][i]
		# if parameter is a filename and file exists load data from file
		if type(data) is str and os.path.exists(data):
			file = open(data)
			dataset.append(json.loads(file.read()))
			file.close()
		# if parameter is a data set use that data set
		elif type(data) is dict:
			dataset.append(data)
	# Test for keys missing from second data set
	for key in set(dataset[0].keys()) - set(dataset[1].keys()):
		print(f'{key} not found in second data set.')
	print()
	# Test for keys missing from first data set
	for key in set(dataset[1].keys()) - set(dataset[0].keys()):
		print(f'{key} is new in second data set.')
	print()
	# Parse through data set items and compare values.
	attributes = [attribute]
	for key in set(dataset[0].keys()).intersection(set(dataset[1].keys())):
		if attribute is None:
			attributes = list(dataset[0][key].keys())
		for att in attributes:
			if key in dataset[1] and dataset[0][key][att] != dataset[1][key][att]:
				print(f'{key}: {att} changed. {dataset[0][key][att]} -> {dataset[1][key][att]}')
	print()
	print("Comparison complete")
