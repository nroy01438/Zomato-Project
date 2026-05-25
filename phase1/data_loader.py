# Stub module for phase1 data_loader
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

@dataclass
class RestaurantData:
    """Stub RestaurantData class"""
    name: str
    location: str
    cuisines: List[str]
    rating: float
    cost_for_two: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "location": self.location,
            "cuisines": self.cuisines,
            "rating": self.rating,
            "cost_for_two": self.cost_for_two,
        }
