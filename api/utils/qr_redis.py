"""
Redis utilities for QR code pairing functionality
"""
import json
import time
from typing import Dict, Any, Optional, List, Set
import logging
from redis import Redis

logger = logging.getLogger("qr_redis")

class QRRedisManager:
    """Redis manager for QR code pairing functionality"""
    
    # Redis key prefixes
    DEVICE_ROOM_PREFIX = "qr:device:"
    DEVICE_TIMESTAMP_PREFIX = "qr:timestamp:"
    ACTIVE_ROOMS_PREFIX = "qr:active_rooms:"
    ROOM_CONNECTIONS_PREFIX = "qr:room_connections:"
    ROOM_METADATA_PREFIX = "qr:room_metadata:"
    ROOM_MESSAGES_PREFIX = "qr:room_messages:"
    
    # Default expiration times (in seconds)
    DEFAULT_DEVICE_EXPIRY = 60 * 10  # 10 minutes
    UNPAIRED_DEVICE_EXPIRY = 60 * 5  # 5 minutes
    ROOM_EXPIRY = 60 * 30  # 30 minutes
    MESSAGE_EXPIRY = 60 * 60 * 24  # 24 hours
    
    def __init__(self, redis_client: Redis):
        """
        Initialize with a Redis client
        
        Args:
            redis_client: Redis client instance
        """
        self.redis = redis_client
        
    def store_device_data(self, device_id: str, data: Dict[str, Any], paired: bool = False) -> None:
        """
        Store device data in Redis
        
        Args:
            device_id: Device ID
            data: Device data including room_id
            paired: Whether the device is paired with a room
        """
        try:
            # Create the Redis key
            key = f"{self.DEVICE_ROOM_PREFIX}{device_id}"
            
            # Convert data to JSON
            json_data = json.dumps(data)
            
            # Set expiry time based on whether device is paired
            expiry = self.DEFAULT_DEVICE_EXPIRY if paired else self.UNPAIRED_DEVICE_EXPIRY
            
            # Store in Redis with expiry
            self.redis.set(key, json_data, ex=expiry)
            
            logger.debug(f"Stored device data for {device_id} in Redis")
        except Exception as e:
            logger.error(f"Error storing device data in Redis: {str(e)}")
            raise
    
    def get_device_data(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Get device data from Redis
        
        Args:
            device_id: Device ID
            
        Returns:
            Device data or None if not found
        """
        try:
            key = f"{self.DEVICE_ROOM_PREFIX}{device_id}"
            data = self.redis.get(key)
            print(self.redis.get(key))
            print(key,data)
            
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting device data from Redis: {str(e)}")
            return None
    
    def update_device_timestamp(self, device_id: str) -> None:
        """
        Update the timestamp for a device
        
        Args:
            device_id: Device ID
        """
        try:
            key = f"{self.DEVICE_TIMESTAMP_PREFIX}{device_id}"
            current_time = time.time()
            self.redis.set(key, str(current_time), ex=self.DEFAULT_DEVICE_EXPIRY)
        except Exception as e:
            logger.error(f"Error updating device timestamp in Redis: {str(e)}")
    
    def get_device_timestamp(self, device_id: str) -> Optional[float]:
        """
        Get the timestamp for a device
        
        Args:
            device_id: Device ID
            
        Returns:
            Timestamp as float or None if not found
        """
        try:
            key = f"{self.DEVICE_TIMESTAMP_PREFIX}{device_id}"
            data = self.redis.get(key)
            
            if data:
                return float(data)
            return None
        except Exception as e:
            logger.error(f"Error getting device timestamp from Redis: {str(e)}")
            return None
    
    def add_room(self, room_id: str) -> None:
        """
        Add a room to the active rooms set
        
        Args:
            room_id: Room ID
        """
        try:
            key = f"{self.ACTIVE_ROOMS_PREFIX}list"
            self.redis.sadd(key, room_id)
            # Set expiry for the room (will be refreshed when used)
            self.redis.expire(key, self.DEFAULT_DEVICE_EXPIRY)
        except Exception as e:
            logger.error(f"Error adding room to Redis: {str(e)}")
    
    def remove_room(self, room_id: str) -> None:
        """
        Remove a room from the active rooms set
        
        Args:
            room_id: Room ID
        """
        try:
            key = f"{self.ACTIVE_ROOMS_PREFIX}list"
            self.redis.srem(key, room_id)
        except Exception as e:
            logger.error(f"Error removing room from Redis: {str(e)}")
    
    def get_all_rooms(self) -> Set[str]:
        """
        Get all active room IDs
        
        Returns:
            Set of room IDs
        """
        try:
            key = f"{self.ACTIVE_ROOMS_PREFIX}list"
            rooms = self.redis.smembers(key)
            return {room.decode('utf-8') for room in rooms}
        except Exception as e:
            logger.error(f"Error getting rooms from Redis: {str(e)}")
            return set()
    
    def room_exists(self, room_id: str) -> bool:
        """
        Check if a room exists in the active rooms
        
        Args:
            room_id: Room ID
            
        Returns:
            True if room exists, False otherwise
        """
        try:
            key = f"{self.ACTIVE_ROOMS_PREFIX}list"
            return self.redis.sismember(key, room_id)
        except Exception as e:
            logger.error(f"Error checking room existence in Redis: {str(e)}")
            return False
    
    def get_device_by_room(self, room_id: str) -> Optional[str]:
        """
        Find a device ID by room ID
        
        Args:
            room_id: Room ID
            
        Returns:
            Device ID or None if not found
        """
        try:
            # This is an expensive operation but necessary to find the device by room
            # In a production system, you might want to maintain a separate mapping
            all_keys = self.redis.keys(f"{self.DEVICE_ROOM_PREFIX}*")
            
            for key in all_keys:
                device_id = key.decode('utf-8').replace(self.DEVICE_ROOM_PREFIX, "")
                data = self.get_device_data(device_id)
                
                if data and data.get("room_id") == room_id:
                    return device_id
            
            return None
        except Exception as e:
            logger.error(f"Error finding device by room in Redis: {str(e)}")
            return None
    
    def store_room_metadata(self, room_id: str, metadata: Dict[str, Any]) -> None:
        """
        Store metadata for a room
        
        Args:
            room_id: Room ID
            metadata: Room metadata (creator, creation time, etc.)
        """
        try:
            key = f"{self.ROOM_METADATA_PREFIX}{room_id}"
            json_data = json.dumps(metadata)
            self.redis.set(key, json_data, ex=self.ROOM_EXPIRY)
            logger.debug(f"Stored metadata for room {room_id} in Redis")
        except Exception as e:
            logger.error(f"Error storing room metadata in Redis: {str(e)}")
    
    def get_room_metadata(self, room_id: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a room
        
        Args:
            room_id: Room ID
            
        Returns:
            Room metadata or None if not found
        """
        try:
            key = f"{self.ROOM_METADATA_PREFIX}{room_id}"
            data = self.redis.get(key)
            
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Error getting room metadata from Redis: {str(e)}")
            return None
    
    def increment_room_connections(self, room_id: str) -> int:
        """
        Increment the connection count for a room
        
        Args:
            room_id: Room ID
            
        Returns:
            New connection count
        """
        try:
            key = f"{self.ROOM_CONNECTIONS_PREFIX}{room_id}"
            count = self.redis.incr(key)
            self.redis.expire(key, self.ROOM_EXPIRY)  # Refresh expiration
            return count
        except Exception as e:
            logger.error(f"Error incrementing room connections in Redis: {str(e)}")
            return 0
    
    def decrement_room_connections(self, room_id: str) -> int:
        """
        Decrement the connection count for a room
        
        Args:
            room_id: Room ID
            
        Returns:
            New connection count, or -1 if error
        """
        try:
            key = f"{self.ROOM_CONNECTIONS_PREFIX}{room_id}"
            count = self.redis.decr(key)
            if count <= 0:
                # If no connections left, remove connection key but keep metadata
                self.redis.delete(key)
                return 0
            return count
        except Exception as e:
            logger.error(f"Error decrementing room connections in Redis: {str(e)}")
            return -1
    
    def get_room_connection_count(self, room_id: str) -> int:
        """
        Get the connection count for a room
        
        Args:
            room_id: Room ID
            
        Returns:
            Connection count or 0 if not found
        """
        try:
            key = f"{self.ROOM_CONNECTIONS_PREFIX}{room_id}"
            count = self.redis.get(key)
            return int(count) if count else 0
        except Exception as e:
            logger.error(f"Error getting room connections from Redis: {str(e)}")
            return 0
    
    def store_room_message(self, room_id: str, message: Dict[str, Any]) -> None:
        """
        Store a message for a room in the message history
        
        Args:
            room_id: Room ID
            message: Message data
        """
        try:
            key = f"{self.ROOM_MESSAGES_PREFIX}{room_id}"
            # Add timestamp if not provided
            if 'timestamp' not in message:
                message['timestamp'] = time.time()
            # Convert message to JSON and push to list
            self.redis.lpush(key, json.dumps(message))
            # Trim the list to most recent 100 messages
            self.redis.ltrim(key, 0, 99)
            # Set expiry for message history
            self.redis.expire(key, self.MESSAGE_EXPIRY)
        except Exception as e:
            logger.error(f"Error storing room message in Redis: {str(e)}")
    
    def get_room_messages(self, room_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get message history for a room
        
        Args:
            room_id: Room ID
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of messages, newest first
        """
        try:
            key = f"{self.ROOM_MESSAGES_PREFIX}{room_id}"
            messages = self.redis.lrange(key, 0, limit - 1)
            return [json.loads(msg) for msg in messages]
        except Exception as e:
            logger.error(f"Error getting room messages from Redis: {str(e)}")
            return []
    
    def cleanup_expired_devices(self) -> None:
        """
        Cleanup expired devices (this is handled by Redis expiry,
        but we may need to clean up other related data)
        """
        # Redis handles expiration automatically using the ex parameter
        # This method can be extended if additional cleanup is needed
        pass
