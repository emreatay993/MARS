"""
Node-related utility helpers for MARS (Modal Analysis Response Solver).

Provides helper functions for node ID mapping and manipulation.
"""

import numpy as np


def _normalize_node_id(node_id):
    """Normalize node IDs from int/float/string inputs into a comparable form."""
    if isinstance(node_id, np.generic):
        node_id = node_id.item()

    if node_id is None:
        return None

    if isinstance(node_id, (int, np.integer)):
        return int(node_id)

    if isinstance(node_id, (float, np.floating)):
        if not np.isfinite(node_id):
            return None
        rounded = int(round(float(node_id)))
        if np.isclose(float(node_id), rounded, atol=1e-9, rtol=0.0):
            return rounded
        return None

    text = str(node_id).strip()
    if not text:
        return None

    # CSV exports or spreadsheets may include separators.
    text = text.replace(',', '')

    try:
        return int(text)
    except ValueError:
        pass

    try:
        as_float = float(text)
    except ValueError:
        return text

    if not np.isfinite(as_float):
        return None

    rounded = int(round(as_float))
    if np.isclose(as_float, rounded, atol=1e-9, rtol=0.0):
        return rounded

    return text


def get_node_index_from_id(node_id, node_ids, log_missing=True):
    """
    Map the given node_id to its corresponding index in the node array.
    
    Args:
        node_id: The node ID to map.
        node_ids: Array of node IDs (numpy array or similar).
    
    Returns:
        int: The index of the node ID in the array, or None if not found.
    """
    normalized_target = _normalize_node_id(node_id)
    node_array = np.asarray(node_ids).reshape(-1)

    if normalized_target is None or node_array.size == 0:
        if log_missing:
            print(f"Node ID {node_id} not found in the list of nodes.")
        return None

    if isinstance(normalized_target, int):
        if np.issubdtype(node_array.dtype, np.integer):
            matches = np.where(node_array.astype(np.int64, copy=False) == normalized_target)[0]
        elif np.issubdtype(node_array.dtype, np.floating):
            matches = np.where(
                np.isfinite(node_array) &
                np.isclose(node_array, normalized_target, atol=1e-9, rtol=0.0)
            )[0]
        else:
            normalized_ids = np.array([_normalize_node_id(value) for value in node_array], dtype=object)
            matches = np.where(normalized_ids == normalized_target)[0]
    else:
        normalized_ids = np.array([_normalize_node_id(value) for value in node_array], dtype=object)
        matches = np.where(normalized_ids == normalized_target)[0]

    if matches.size > 0:
        return int(matches[0])

    if log_missing:
        print(f"Node ID {node_id} not found in the list of nodes.")
    return None
