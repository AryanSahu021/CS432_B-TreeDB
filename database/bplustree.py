import graphviz
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
            if i >= len(node.children):  # Safety check
                return False
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
            if i >= len(node.children):  # Safety check
                return None
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
            try:
                idx = node.keys.index(key)
                node.keys.pop(idx)
                if node.values and idx < len(node.values):  # Ensure idx is valid for values
                    node.values.pop(idx)
            except ValueError:
                return  # Key not found in this leaf
        else:
            # Find the appropriate child
            idx = 0
            while idx < len(node.keys) and key >= node.keys[idx]:
                idx += 1
            
            # Ensure we don't go out of bounds
            if idx >= len(node.children):
                return
            
            # Check if key exists in the subtree
            if idx < len(node.keys) and key == node.keys[idx]:
                # Key is in this internal node, find predecessor
                predecessor = self._get_predecessor(node.children[idx])
                node.keys[idx] = predecessor
                self._delete(node.children[idx], predecessor)
            else:
                self._delete(node.children[idx], key)
            
            # Check if child needs merging or borrowing
            if len(node.children[idx].keys) < self.min_keys:
                self._fill_child(node, idx)

    def _get_predecessor(self, node: BPlusTreeNode):
        """Get the largest key in the subtree rooted at node"""
        while not node.is_leaf:
            node = node.children[-1]
        return node.keys[-1] if node.keys else None

    def _fill_child(self, parent: BPlusTreeNode, child_idx: int) -> None:
        """Ensure child at given index has enough keys"""
        if child_idx > 0 and len(parent.children[child_idx - 1].keys) > self.min_keys:
            # Borrow from left sibling
            self._borrow_from_prev(parent, child_idx)
        elif child_idx < len(parent.children) - 1 and len(parent.children[child_idx + 1].keys) > self.min_keys:
            # Borrow from right sibling
            self._borrow_from_next(parent, child_idx)
        else:
            # Merge with a sibling
            if child_idx == len(parent.children) - 1:
                # Merge with left sibling
                self._merge(parent, child_idx - 1)
            else:
                # Merge with right sibling
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
            parent.keys[child_idx - 1] = left_sibling.keys[-1] if left_sibling.keys else borrowed_key
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
            parent.keys[child_idx] = right_sibling.keys[0] if right_sibling.keys else borrowed_key
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

        # If parent is root and becomes empty
        if parent == self.root and not parent.keys:
            self.root = left_child

    def update(self, key, new_value) -> bool:
        """Update the value associated with a key. Returns True if successful."""
        node = self.root
        while not node.is_leaf:
            i = 0
            while i < len(node.keys) and key >= node.keys[i]:
                i += 1
            if i >= len(node.children):  # Safety check
                return False
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
            if i >= len(node.children):  # Safety check
                return results
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
            if not node.children:  # Safety check
                return results
            node = node.children[0]
        
        # Traverse all leaf nodes
        while node:
            for i, key in enumerate(node.keys):
                results.append((key, node.values[i] if node.values else None))
            node = node.next
        
        return results

    def validate_tree(self) -> bool:
        """Check tree invariants"""
        return self._validate_node(self.root)

    def _validate_node(self, node: BPlusTreeNode) -> bool:
        if node.is_leaf:
            # Check leaf node properties
            if len(node.keys) > self.max_keys or (node != self.root and len(node.keys) < self.min_keys):
                return False
            return True
        
        # Check internal node properties
        if len(node.keys) > self.max_keys or (node != self.root and len(node.keys) < self.min_keys):
            return False
        
        if len(node.children) != len(node.keys) + 1:
            return False
        
        # Check keys are sorted
        if node.keys != sorted(node.keys):
            return False
        
        # Recursively validate children
        for child in node.children:
            if not self._validate_node(child):
                return False
        
        return True

    def visualize_tree(self, filename: str = 'bplustree') -> None:
        """Generate a visualization of the B+ tree using Graphviz."""
        dot = graphviz.Digraph(comment='B+ Tree', node_attr={'shape': 'box'})
        
        # Add nodes
        nodes = [self.root]
        while nodes:
            node = nodes.pop(0)
            
            if node.is_leaf:
                label = f"Leaf: {node.keys}"
                if node.values:
                    label += f"\nValues: {node.values}"
            else:
                label = f"Node: {node.keys}"
                nodes.extend(node.children)
            
            dot.node(str(id(node)), label=label)
        
        # Add edges
        nodes = [self.root]
        while nodes:
            node = nodes.pop(0)
            if not node.is_leaf:
                for child in node.children:
                    dot.edge(str(id(node)), str(id(child)))
                    nodes.append(child)
        
        # Add leaf links
        if not self.root.is_leaf:
            # Find leftmost leaf
            node = self.root
            while not node.is_leaf:
                if not node.children:  # Safety check
                    break
                node = node.children[0]
            
            # Add links between leaves
            while node and node.next:
                dot.edge(str(id(node)), str(id(node.next)), 
                       style='dashed', constraint='false')
                node = node.next
        
        try:
            dot.render(filename, format='png', cleanup=True)
            print(f"Visualization saved as {filename}.png")
        except Exception as e:
            print(f"Visualization failed: {e}")
            print("Text representation:")
            self.print_tree()

    def print_tree(self) -> None:
        """Print a text representation of the tree"""
        nodes = [(self.root, 0)]
        while nodes:
            node, level = nodes.pop(0)
            prefix = "  " * level
            if node.is_leaf:
                print(f"{prefix}Leaf: {node.keys}")
                if node.values:
                    print(f"{prefix}Values: {node.values}")
            else:
                print(f"{prefix}Node: {node.keys}")
                for child in reversed(node.children):
                    nodes.insert(0, (child, level + 1))
            
            # Show leaf links
            if node.is_leaf and node.next:
                print(f"{prefix}  -> Next leaf: {node.next.keys[:1]}...")