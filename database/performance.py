# performance.py
import time
import random
import sys
from typing import Callable, Tuple, List
from bplustree import BPlusTree
from bruteforce import BruteForceDB
import matplotlib.pyplot as plt

class PerformanceAnalyzer:
    def __init__(self):
        self.results = {
            'insert': {'bptree': [], 'bruteforce': [], 'sizes': []},
            'search': {'bptree': [], 'bruteforce': [], 'sizes': []},
            'delete': {'bptree': [], 'bruteforce': [], 'sizes': []},
            'range_query': {'bptree': [], 'bruteforce': [], 'sizes': []},
            'memory': {'bptree': [], 'bruteforce': [], 'sizes': []}
        }
    
    def _measure_time(self, func: Callable, *args) -> float:
        """Measure execution time of a function."""
        start = time.time()
        func(*args)
        return time.time() - start
    
    def _measure_memory(self, obj) -> int:
        """Approximate memory usage of an object."""
        return sys.getsizeof(obj)
    
    def generate_test_data(self, size: int) -> List[int]:
        """Generate unique random test data."""
        return random.sample(range(size * 10), size)
    
    def run_insertion_test(self, sizes: List[int]) -> None:
        """Test insertion performance."""
        for size in sizes:
            data = self.generate_test_data(size)
            
            # Test B+ Tree
            bptree = BPlusTree(degree=3)
            time_taken = self._measure_time(lambda: [bptree.insert(key) for key in data])
            self.results['insert']['bptree'].append(time_taken)
            self.results['memory']['bptree'].append(self._measure_memory(bptree))
            
            # Test BruteForce
            bruteforce = BruteForceDB()
            time_taken = self._measure_time(lambda: [bruteforce.insert(key) for key in data])
            self.results['insert']['bruteforce'].append(time_taken)
            self.results['memory']['bruteforce'].append(self._measure_memory(bruteforce))
            
            self.results['insert']['sizes'].append(size)
            self.results['memory']['sizes'].append(size)
    
    def run_search_test(self, sizes: List[int]) -> None:
        """Test search performance."""
        for size in sizes:
            data = self.generate_test_data(size)
            search_keys = random.sample(data, min(100, len(data)))  # Search for 100 random keys
            
            # Prepare B+ Tree
            bptree = BPlusTree(degree=3)
            for key in data:
                bptree.insert(key)
            
            # Test B+ Tree search
            time_taken = self._measure_time(lambda: [bptree.search(key) for key in search_keys])
            self.results['search']['bptree'].append(time_taken)
            
            # Prepare BruteForce
            bruteforce = BruteForceDB()
            for key in data:
                bruteforce.insert(key)
            
            # Test BruteForce search
            time_taken = self._measure_time(lambda: [bruteforce.search(key) for key in search_keys])
            self.results['search']['bruteforce'].append(time_taken)
            
            self.results['search']['sizes'].append(size)
    
    def run_delete_test(self, sizes: List[int]) -> None:
        """Test deletion performance."""
        for size in sizes:
            data = self.generate_test_data(size)
            delete_keys = random.sample(data, min(100, len(data)))  # Delete 100 random keys
            
            # Prepare B+ Tree
            bptree = BPlusTree(degree=3)
            for key in data:
                bptree.insert(key)
            
            # Test B+ Tree delete
            time_taken = self._measure_time(lambda: [bptree.delete(key) for key in delete_keys])
            self.results['delete']['bptree'].append(time_taken)
            
            # Prepare BruteForce
            bruteforce = BruteForceDB()
            for key in data:
                bruteforce.insert(key)
            
            # Test BruteForce delete
            time_taken = self._measure_time(lambda: [bruteforce.delete(key) for key in delete_keys])
            self.results['delete']['bruteforce'].append(time_taken)
            
            self.results['delete']['sizes'].append(size)
    
    def run_range_query_test(self, sizes: List[int]) -> None:
        """Test range query performance."""
        for size in sizes:
            data = self.generate_test_data(size)
            start = random.randint(0, size * 5)
            end = start + random.randint(size // 10, size // 5)
            
            # Prepare B+ Tree
            bptree = BPlusTree(degree=3)
            for key in data:
                bptree.insert(key)
            
            # Test B+ Tree range query
            time_taken = self._measure_time(lambda: bptree.range_query(start, end))
            self.results['range_query']['bptree'].append(time_taken)
            
            # Prepare BruteForce
            bruteforce = BruteForceDB()
            for key in data:
                bruteforce.insert(key)
            
            # Test BruteForce range query
            time_taken = self._measure_time(lambda: bruteforce.range_query(start, end))
            self.results['range_query']['bruteforce'].append(time_taken)
            
            self.results['range_query']['sizes'].append(size)
    
    def run_all_tests(self, sizes: List[int]) -> None:
        """Run all performance tests."""
        self.run_insertion_test(sizes)
        self.run_search_test(sizes)
        self.run_delete_test(sizes)
        self.run_range_query_test(sizes)
    
    def plot_results(self) -> None:
        """Plot the performance comparison results."""
        plt.figure(figsize=(15, 10))
        
        # Insertion Performance
        plt.subplot(2, 3, 1)
        plt.plot(self.results['insert']['sizes'], self.results['insert']['bptree'], label='B+ Tree')
        plt.plot(self.results['insert']['sizes'], self.results['insert']['bruteforce'], label='BruteForce')
        plt.xlabel('Data Size')
        plt.ylabel('Time (seconds)')
        plt.title('Insertion Performance')
        plt.legend()
        
        # Search Performance
        plt.subplot(2, 3, 2)
        plt.plot(self.results['search']['sizes'], self.results['search']['bptree'], label='B+ Tree')
        plt.plot(self.results['search']['sizes'], self.results['search']['bruteforce'], label='BruteForce')
        plt.xlabel('Data Size')
        plt.ylabel('Time (seconds)')
        plt.title('Search Performance')
        plt.legend()
        
        # Delete Performance
        plt.subplot(2, 3, 3)
        plt.plot(self.results['delete']['sizes'], self.results['delete']['bptree'], label='B+ Tree')
        plt.plot(self.results['delete']['sizes'], self.results['delete']['bruteforce'], label='BruteForce')
        plt.xlabel('Data Size')
        plt.ylabel('Time (seconds)')
        plt.title('Deletion Performance')
        plt.legend()
        
        # Range Query Performance
        plt.subplot(2, 3, 4)
        plt.plot(self.results['range_query']['sizes'], self.results['range_query']['bptree'], label='B+ Tree')
        plt.plot(self.results['range_query']['sizes'], self.results['range_query']['bruteforce'], label='BruteForce')
        plt.xlabel('Data Size')
        plt.ylabel('Time (seconds)')
        plt.title('Range Query Performance')
        plt.legend()
        
        # Memory Usage
        plt.subplot(2, 3, 5)
        plt.plot(self.results['memory']['sizes'], self.results['memory']['bptree'], label='B+ Tree')
        plt.plot(self.results['memory']['sizes'], self.results['memory']['bruteforce'], label='BruteForce')
        plt.xlabel('Data Size')
        plt.ylabel('Memory (bytes)')
        plt.title('Memory Usage')
        plt.legend()
        
        plt.tight_layout()
        plt.savefig('performance_comparison.png')
        plt.show()