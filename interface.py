class Interface(object):
	def __init__(self, node, interface):
		self.__node = node
		self.__id = None
		self.__dn = None
		self.__type = None
		self.id = interface

	@property
	def node(self):
		return self.__node

	@property
	def id(self):
		return self.__id

	@id.setter
	def id(self, interface):
		if type(interface) is int:
			interface = f'eth1/{interface}'
		if type(interface) is str:
			if interface.isdigit():
				interface = f'eth1/{interface}'
			else:
				interface = interface.lower().replace('ethernet', 'eth')
		else:
			raise Exception(f'Invalid interface, {interface}, provided.')
		d = self.__node.qr('l1PhysIf', filter=f'eq(l1PhysIf.id, "{interface}"').data
		if d.count != 1:
			raise Exception(f'Interface {interface} was not found on {self.__node.name}.')
		self.__id = interface
		self.__dn = d.value('dn')
		self.__type = d.value('portT')

	@property
	def state(self):
		return self.node.qr(f'{self.dn}/phys').data.value('operSt')

	@property
	def dn(self):
		return self.__dn

	@property
	def type(self):
		return self.__type
