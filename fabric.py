from node import Node
from ip import IP
import copy


class Fabric(object):
	def __init__(self, apic, username=None, password=None):
		if isinstance(apic, Node):
			self.__apic = apic
		else:
			self.__apic = Node(apic, username, password)

	@property
	def apic(self):
		return self.__apic

	@apic.setter
	def apic(self, apic):
		if isinstance(apic, Node):
			self.__apic = apic
		elif type(apic) is str:
			self.__apic = Node(apic)

	@property
	def node_ids(self):
		d = self.apic.qr('fabricNode').output
		nds = [int(n) for n in d.attribute('id')]
		nds.sort()
		return nds

	@property
	def spine_ids(self):
		d = self.apic.qr('fabricNode', filter='role=spine').output
		nds = [int(n) for n in d.attribute('id')]
		nds.sort()
		return nds

	@property
	def leaf_ids(self):
		d = self.apic.qr('fabricNode', filter='role=leaf').output
		nds = [int(n) for n in d.attribute('id')]
		nds.sort()
		return nds

	def node(self, id):
		address = self.apic.qr('topSystem', filter=f'eq(topSystem.id, "{id}")').output.value('oobMgmtAddr')
		n = copy.deepcopy(self.apic)
		n.address = address
		n.fabric = self
		return n

	# Post function used to send Post messages to fabric
	def post(self, path, payload=None):
		return self.apic.post(path, payload)

	def login(self, user=None, password=None):
		return self.apic.login(user, password)

	# Creates a Query object associated with the current fabric with provided parameters
	def query(self, path=None, filter=None, target=None, target_class=None, include=None, subtree=None, subtree_class=None,
						subtree_filter=None, subtree_include=None, order=None):
		return self.apic.query(path=path, filter=filter, target=target, target_class=target_class, include=include,
									subtree=subtree, subtree_class=subtree_class, subtree_filter=subtree_filter,
									subtree_include=subtree_include, order=order)

	# Creates a Query object associated with the current fabric with provided parameters
	def qr(self, path=None, filter=None, target=None, target_class=None, include=None, subtree=None, subtree_class=None,
						subtree_filter=None, subtree_include=None, order=None):
		query = self.apic.qr(path=path, filter=filter, target=target, target_class=target_class, include=include,
									subtree=subtree, subtree_class=subtree_class, subtree_filter=subtree_filter,
									subtree_include=subtree_include, order=order)
		query.run()
		return query

	def transceiver_count(self):
		return self.apic.qr('ethpmFcot').output.sum('typeName', True)

	def change_local_user_password(self, user, old_password=None, new_password=None):
		from getpass import getpass
		if old_password is None:
			old_password = getpass('Current password: ')
		apic = Node(self.apic.address, f'apic#fallback\\\\{user}', old_password)
		while new_password is None:
			new_password = getpass('New password: ')
			if new_password != getpass('Re-enter new password: '):
				new_password = None
				print('Passwords do not match!')
		if apic.post({'aaaUser': {'attributes': {'dn': f'uni/userext/user-{user}', 'pwd': new_password}}}) == 200:
			print(f'Password for local account, {user}, has been changed.')
		else:
			print(apic.response.text)

	def add_epg_static(self, epg_dn, ep_net, next_hop):
		ep_net = IP(ep_net)
		if ep_net.mask is None:
			ep_net.mask = 32
		next_hop = IP(next_hop)
		for ip in ep_net.ips_in_network:
			js = {
				"fvSubnet": {
					"attributes": {
						"ctrl": "no-default-gateway",
						"dn": f"{epg_dn}/subnet-[{ip}/32]",
						"ip": f"{ip}/32",
						"preferred": "no",
						"scope": "public,shared",
						"virtual": "no"
					},
					"children": [
						{
							"fvEpReachability": {
								"attributes": {},
								"children": [
									{
										"ipNexthopEpP": {
											"attributes": {
												"nhAddr": next_hop.ip
											}
										}
									}
								]
							}
						}
					]
				}
			}
			if self.post(js) != 200:
				raise Exception(f"Addition of EPG static Endpoint Route failed. {self.apic.response.text}")
		return True
