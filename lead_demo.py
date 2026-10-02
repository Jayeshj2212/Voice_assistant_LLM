from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Lead:
    name: str
    phone: str
    city: str
    language: str
    interest: str
    status: str = 'new'
    notes: List[str] = field(default_factory=list)


def sample_leads() -> List[Lead]:
    return [
        Lead('Amit Sharma', '+91 98765 43210', 'Delhi', 'hi', 'Home loan', 'new', ['Interested in callback today']),
        Lead('Maria Dsouza', '+91 99887 66554', 'Mumbai', 'en', 'Insurance', 'warm', ['Asked about premium reduction']),
        Lead('Rahul Saha', '+91 90000 12121', 'Kolkata', 'bn', 'Credit card', 'hot', ['Wants product comparison'])
    ]


def get_demo_pipeline() -> Dict[str, int]:
    return {
        'total_leads': 1240,
        'qualified': 318,
        'calls_done': 892,
        'converted': 136,
        'cost_per_lead': 18,
        'answer_rate': 72,
    }
