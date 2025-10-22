from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple


@dataclass
class Card:
	"""Lightweight card container used as placed-card state."""
	id: str
	name: str
	card_type: str
	owner_id: Optional[str] = None
	position: Optional[Tuple[int, int]] = None
	# runtime, template-driven fields (filled by CardFactory)
	template_id: Optional[str] = None
	template: Optional[dict] = None
	back: Optional[str] = None
	template_position: Optional[Tuple[int, int]] = None
	resource: Optional[str] = None
	base_yield: int = 0
	max_capacity: int = 0
	die_value: Optional[int] = None

	stored_resources: Dict[str, int] = field(default_factory=dict)

	# convenience helpers
	def add_resource(self, resource: str, amount: int) -> int:
		"""Add up to `amount` of resource to this card, respecting max_capacity if set.

		Returns the actual amount added.
		"""
		current = self.stored_resources.get(resource, 0)
		maxcap = getattr(self, "max_capacity", None)
		if maxcap and maxcap > 0:
			can_add = max(0, maxcap - current)
			to_add = min(can_add, amount)
			if to_add <= 0:
				return 0
			self.stored_resources[resource] = current + to_add
			return to_add
		else:
			self.stored_resources[resource] = current + amount
			return amount

	def remove_resource(self, resource: str, amount: int) -> int:
		"""Remove up to `amount` of resource from this card and return actual removed."""
		have = self.stored_resources.get(resource, 0)
		take = min(have, amount)
		if take:
			self.stored_resources[resource] = have - take
			if self.stored_resources[resource] == 0:
				del self.stored_resources[resource]
		return take


