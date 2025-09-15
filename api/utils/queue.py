
import json
from  api.schemas.rooms import Collection

class Queue:
    def __init__(self, redis_client, key, max_queue_size=20, precision_factor=100):
        """
        Initialize a new queue.
        
        Parameters:
        -----------
        redis_client : Redis
            Redis client for queue operations
        key : str
            Redis key for the queue
        max_queue_size : int
            Maximum number of items to keep in the queue
        """
        self.redis_client = redis_client
        self.max_queue_size = max_queue_size
        self.precision_factor = 100
        self.key = key
    
    def __str__(self):
        return f"Queue(key={self.key}, queue_length={self.get_queue_length()})"
    
    def __repr__(self):
        return str(self)
    
    def get_max_size(self):
        return self.max_queue_size
    
    def get_queue_length(self):
        """
        Retrieve the current length of the queue.
        
        Returns:
        --------
        int
            Number of items currently in the queue
        """
        return self.redis_client.llen(self.key)
    

    def select_collections_fitting_space(self, available_space_mb):
        """
        Select collections that fit within the available space constraint,
        optimizing for maximum space utilization.
        
        Parameters:
        -----------
        available_space_mb : float
            Available space in MB
                
        Returns:
        --------
        list
            List of collections that fit within the space constraint while
            maximizing space utilization
        """
        collections = self.get_all_collections()
        
        # Convert available_space_mb to an integer representation for DP
        # Multiply by 100 to handle 2 decimal places without floating point issues
        
        available_space = int(available_space_mb * self.precision_factor)
        
        # Create mappings from indices to collections for later retrieval
        collection_sizes = []
        for c in collections:
            # Convert to integer representation
            size = int(c['space_mb'] * self.precision_factor)
            collection_sizes.append(size)
        
        n = len(collections)
        
        # Initialize DP table
        dp = [[0 for _ in range(available_space + 1)] for _ in range(n + 1)]
        
        # Fill the DP table
        for i in range(1, n + 1):
            for j in range(available_space + 1):
                size = collection_sizes[i-1]
                if size <= j:
                    # Max of including or excluding this item
                    dp[i][j] = max(size + dp[i-1][j-size], dp[i-1][j])
                else:
                    # Can't include this item
                    dp[i][j] = dp[i-1][j]
        
        # Backtrack to find selected collections
        selected_collections = []
        total_size = dp[n][available_space]
        remaining_space = available_space
        
        for i in range(n, 0, -1):
            # Check if this collection was included
            if dp[i][remaining_space] != dp[i-1][remaining_space]:
                selected_collections.append(collections[i-1])
                remaining_space -= collection_sizes[i-1]
        
        return selected_collections

    # Alternative approach using a greedy approximation algorithm
    def select_collections_fitting_space_greedy(self, available_space_mb):
        """
        Select collections that fit within the available space constraint using
        a greedy approach that sorts by value density.
        
        Parameters:
        -----------
        available_space_mb : float
            Available space in MB
                
        Returns:
        --------
        list
            List of collections that fit within the space constraint
        """
        available_collections = self.get_all_collections()
        
        # Sort collections by size in ascending order (prefer smaller collections first)
        available_collections.sort(key=lambda x: x['space_mb'])
        
        selected_collections = []
        total_size_mb = 0.0
        
        for collection in available_collections:
            space_mb = collection["space_mb"]
            
            if total_size_mb + space_mb <= available_space_mb:
                selected_collections.append(collection)
                total_size_mb += space_mb
            
        return selected_collections

    def exists(self, collection_id):
        """
        Check if a collection exists in the queue by ID.
        
        Parameters:
        -----------
        collection_id : str
            ID of the collection to check
        
        Returns:
        --------
        bool
            True if collection exists, False otherwise
        """
        return collection_id in [c.get('id') for c in self.get_all_collections()]
    
    def add_collection(self, collection:Collection):
        """
        Add a collection to the queue.
        
        Parameters:
        -----------
        collection : Collection
            Collection data to add to queue
        """
        collections = self.get_all_collections()
        if collection.id in [c.get('id') for c in collections]: 
            return
        
        self.redis_client.rpush(self.key, json.dumps(collection.dict())) 

        # Maintain queue size limit (keep only latest 20 collections)
        self.redis_client.ltrim(self.key, - self.max_queue_size, -1)  

    def get_all_collections(self):
        """
        Retrieve and parse all collections from the queue.
        
        Returns:    
        --------
        list
            List of valid collection dictionaries from the queue
        """
        return [json.loads(item) for item in self.get_queue_items()]
    
    def get_queue_items(self):
        """
        Retrieves all collections from queue

        Returns:
        --------
        list
            List of valid collections from the queue
        """
        return self.redis_client.lrange(self.key,0,-1)

    def remove_collection(self, collection_id):
        """
        Remove a specific collection from the queue by ID.
        
        Parameters:
        -----------
        collection_id : str
            ID of the collection to remove
            
        Returns:
        --------
        int
            Number of items removed from the queue
        """
        for item in self.get_all_collections():
            if item.get('id') == str(collection_id):
                removed = self.redis_client.lrem(self.key,1,json.dumps(item))
                return removed  
        return 0

    def remove_collections(self, collections):
        """
        Remove a list of collections from the queue by ID.
        
        Parameters:
        -----------
        collections : list
            List of collections to remove
        """
        for collection in collections:
            self.redis_client.lrem(self.key,1,json.dumps(collection))

 