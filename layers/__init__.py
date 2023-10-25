# -*- coding: utf-8 -*-

from .aggregator import SumAggregator, ConcatAggregator, NeighAggregator
from .multiAttention import MultiAttention
from .trans_matrix import Trans_Matrix

Aggregator = {
    'sum': SumAggregator,
    'concat': ConcatAggregator,
    'neigh': NeighAggregator
}
