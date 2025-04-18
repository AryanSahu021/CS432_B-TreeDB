# bplustree.py
import graphviz
import random
from typing import List, Dict, Tuple, Optional, Union

class BPlusTreeNode:
    def __init__(self, is_leaf: bool = False):
        self.keys: List = []
        self.children: List = []
        self.is_leaf: bool = is_leaf
        self.next: Optional['BPlusTreeNode'] = None  # For leaf nodes
        self.values: List = []  # Only for leaf nodes

class BPlusTree:
    def __init__(self, degree: int = 3):
        self.degree: int = degree
        self.root: BPlusTreeNode = BPlusTreeNode(is_leaf=True)
        self.min_keys: int = degree - 1
        self.max_keys: int = 2 * degree - 1

    def search(self, key) -> bool:
        """Search for a key in the B+ tree. Return True if found, False otherwise."""
        node = self.root
        while not node.is_leaf:
            # Find the appropriate child to traverse
            i = 0
            while i < len(node.keys) and key >= node.keys[i]:
                i += 1
            node = node.children[i]
        
        # Search in the leaf node
        return key in node.keys

    def get(self, key) -> Optional[object]:
        """Get the value associated with a key, or None if not found."""
        node = self.root
        while not node.is_leaf:
            i = 0
            while i < len(node.keys) and key >= node.keys[i]:
                i += 1
            node = node.children[i]
        
        try:
            idx = node.keys.index(key)
            return node.values[idx]
        except ValueError:
            return None

    def insert(self, key, value=None) -> None:
        """Insert a key-value pair into the B+ tree."""
        if self.search(key):
            self.update(key, value)
            return

        # If root is full, split it
        if len(self.root.keys) == self.max_keys:
            old_root = self.root
            self.root = BPlusTreeNode()
            self.root.children.append(old_root)
            self._split_child(self.root, 0)
        
        self._insert_non_full(self.root, key, value)

    def _insert_non_full(self, node: BPlusTreeNode, key, value) -> None:
        if node.is_leaf:
            # Insert into leaf node
            idx = 0
            while idx < len(node.keys) and key > node.keys[idx]:
                idx += 1
            node.keys.insert(idx, key)
            node.values.insert(idx, value)
        else:
            # Find the appropriate child
            idx = 0
            while idx < len(node.keys) and key > node.keys[idx]:
                idx += 1
            
            # If child is full, split it
            if len(node.children[idx].keys) == self.max_keys:
                self._split_child(node, idx)
                if key > node.keys[idx]:
                    idx += 1
            
            self._insert_non_full(node.children[idx], key, value)

    def _split_child(self, parent: BPlusTreeNode, child_idx: int) -> None:
        child = parent.children[child_idx]
        new_node = BPlusTreeNode(is_leaf=child.is_leaf)
        
        split_point = len(child.keys) // 2
        mid_key = child.keys[split_point]
        
        # Split keys and children
        new_node.keys = child.keys[split_point + (0 if child.is_leaf else 1):]
        child.keys = child.keys[:split_point]
        
        if not child.is_leaf:
            new_node.children = child.children[split_point + 1:]
            child.children = child.children[:split_point + 1]
        else:
            new_node.values = child.values[split_point:]
            child.values = child.values[:split_point]
            new_node.next = child.next
            child.next = new_node
        
        # Insert the new node into parent
        parent.keys.insert(child_idx, mid_key)
        parent.children.insert(child_idx + 1, new_node)

    def delete(self, key) -> bool:
        """Delete a key from the B+ tree. Returns True if successful, False if key not found."""
        if not self.search(key):
            return False
        
        self._delete(self.root, key)
        
        # If root becomes empty after deletion
        if not self.root.keys and self.root.children:
            self.root = self.root.children[0]
        
        return True

    def _delete(self, node: BPlusTreeNode, key) -> None:
        if node.is_leaf:
            # Delete from leaf node
            idx = node.keys.index(key)
            node.keys.pop(idx)
            if node.values:  # Only if we're storing values
                node.values.pop(idx)
        else:
            # Find the appropriate child
            idx = 0
            while idx < len(node.keys) and key >= node.keys[idx]:
                idx += 1
            
            self._delete(node.children[idx], key)
            
            # Check if child needs merging or borrowing
            if len(node.children[idx].keys) < self.min_keys:
                self._fill_child(node, idx)

    def _fill_child(self, parent: BPlusTreeNode, child_idx: int) -> None:
        # Try to borrow from left sibling
        if child_idx > 0 and len(parent.children[child_idx - 1].keys) > self.min_keys:
            self._borrow_from_prev(parent, child_idx)
        # Try to borrow from right sibling
        elif child_idx < len(parent.children) - 1 and len(parent.children[child_idx + 1].keys) > self.min_keys:
            self._borrow_from_next(parent, child_idx)
        # Merge with sibling if borrowing isn't possible
        else:
            if child_idx == len(parent.children) - 1:
                self._merge(parent, child_idx - 1)
            else:
                self._merge(parent, child_idx)

    def _borrow_from_prev(self, parent: BPlusTreeNode, child_idx: int) -> None:
        child = parent.children[child_idx]
        left_sibling = parent.children[child_idx - 1]
        
        if child.is_leaf:
            # Borrow key from left sibling
            borrowed_key = left_sibling.keys.pop()
            borrowed_value = left_sibling.values.pop() if left_sibling.values else None
            child.keys.insert(0, borrowed_key)
            if borrowed_value is not None:
                child.values.insert(0, borrowed_value)
            parent.keys[child_idx - 1] = borrowed_key
        else:
            # Borrow from internal node
            borrowed_key = parent.keys[child_idx - 1]
            borrowed_child = left_sibling.children.pop()
            child.keys.insert(0, borrowed_key)
            child.children.insert(0, borrowed_child)
            parent.keys[child_idx - 1] = left_sibling.keys.pop()

    def _borrow_from_next(self, parent: BPlusTreeNode, child_idx: int) -> None:
        child = parent.children[child_idx]
        right_sibling = parent.children[child_idx + 1]
        
        if child.is_leaf:
            # Borrow key from right sibling
            borrowed_key = right_sibling.keys.pop(0)
            borrowed_value = right_sibling.values.pop(0) if right_sibling.values else None
            child.keys.append(borrowed_key)
            if borrowed_value is not None:
                child.values.append(borrowed_value)
            parent.keys[child_idx] = right_sibling.keys[0]
        else:
            # Borrow from internal node
            borrowed_key = parent.keys[child_idx]
            borrowed_child = right_sibling.children.pop(0)
            child.keys.append(borrowed_key)
            child.children.append(borrowed_child)
            parent.keys[child_idx] = right_sibling.keys.pop(0)

    def _merge(self, parent: BPlusTreeNode, child_idx: int) -> None:
        left_child = parent.children[child_idx]
        right_child = parent.children[child_idx + 1]
        
        if left_child.is_leaf:
            # Merge leaf nodes
            left_child.keys += right_child.keys
            left_child.values += right_child.values
            left_child.next = right_child.next
        else:
            # Merge internal nodes
            left_child.keys.append(parent.keys.pop(child_idx))
            left_child.keys += right_child.keys
            left_child.children += right_child.children
        
        parent.children.pop(child_idx + 1)

    def update(self, key, new_value) -> bool:
        """Update the value associated with a key. Returns True if successful."""
        node = self.root
        while not node.is_leaf:
            i = 0
            while i < len(node.keys) and key >= node.keys[i]:
                i += 1
            node = node.children[i]
        
        try:
            idx = node.keys.index(key)
            node.values[idx] = new_value
            return True
        except ValueError:
            return False

    def range_query(self, start_key, end_key) -> List[Tuple]:
        """Return all key-value pairs where start_key <= key <= end_key."""
        results = []
        
        # Find the starting leaf node
        node = self.root
        while not node.is_leaf:
            i = 0
            while i < len(node.keys) and start_key > node.keys[i]:
                i += 1
            node = node.children[i]
        
        # Traverse leaf nodes
        while node:
            for i, key in enumerate(node.keys):
                if start_key <= key <= end_key:
                    results.append((key, node.values[i] if node.values else None))
                elif key > end_key:
                    return results
            node = node.next
        
        return results

    def get_all(self) -> List[Tuple]:
        """Return all key-value pairs in the tree."""
        results = []
        node = self.root
        
        # Find the leftmost leaf
        while not node.is_leaf:
            node = node.children[0]
        
        # Traverse all leaf nodes
        while node:
            for i, key in enumerate(node.keys):
                results.append((key, node.values[i] if node.values else None))
            node = node.next
        
        return results

    def visualize_tree(self, filename: str = 'bplustree') -> None:
        """Generate a visualization of the B+ tree using Graphviz."""
        dot = graphviz.Digraph(comment='B+ Tree')
        self._add_nodes(dot, self.root)
        self._add_edges(dot, self.root)
        
        # Add links between leaf nodes
        if self.root.is_leaf:
            return
        
        # Find the leftmost leaf
        node = self.root
        while not node.is_leaf:
            node = node.children[0]
        
        # Add links between leaf nodes
        while node.next:
            dot.edge(str(id(node)), str(id(node.next)), style='dashed', constraint='false')
            node = node.next
        
        dot.render(filename, format='png', cleanup=True)

    def _add_nodes(self, dot, node: BPlusTreeNode) -> None:
        """Recursively add nodes to the Graphviz object."""
        if node.is_leaf:
            label = '|'.join([f'<f{idx}> {key}' for idx, key in enumerate(node.keys)])
            dot.node(str(id(node)), label=f'{{{label}}}', shape='record')
        else:
            label = '|'.join([f'<f{idx}> {key}' for idx, key in enumerate(node.keys)])
            dot.node(str(id(node)), label=f'{{{label}}}', shape='record')
            for child in node.children:
                self._add_nodes(dot, child)

    def _add_edges(self, dot, node: BPlusTreeNode) -> None:
        """Add edges between nodes in the Graphviz object."""
        if not node.is_leaf:
            for i, child in enumerate(node.children):
                dot.edge(f'{id(node)}:f{i}', f'{id(child)}')
                self._add_edges(dot, child)