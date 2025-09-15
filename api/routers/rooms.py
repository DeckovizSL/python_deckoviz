from fastapi import APIRouter, Body, Depends
from api.routers.websocket import   notify_new_images
from api.databases.configs import get_redis_client
from api.utils.queue import Queue
from  api.core.logger import logger
import uuid
import threading
import httpx
import time 
from api.schemas.rooms import BatchRequest
from api.utils.websocket_manager import manager


router = APIRouter(
    prefix="/rooms",
    tags=["rooms"]
)
 

# HTTP endpoint to trigger a broadcast of arbitrary JSON payload to a room
@router.post("/{room_id}/notify")
async def trigger_notify(room_id: str, payload: dict = Body(...)):
    """
    HTTP endpoint to broadcast the supplied JSON payload to all WebSocket clients in a room.
    """
    await notify_new_images(room_id, payload)
    return {"status": "notified", "room_id": room_id, "payload": payload}


@router.post("/{room_id}/batch")
async def send_batch(
    room_id: str,
    request: BatchRequest,
    redis_client=Depends(get_redis_client)
):
    """
    Endpoint that processes and sends the next batch of queued collections that fit within
    available space on the TV.
    
    Flow:
    1. Optionally adds a new collection to the queue (if provided in request)
    2. Calculates which collections from the queue fit into the available space
    3. Removes sent collections from the queue and broadcasts them to clients
    4. Schedules automatic retry every 10 minutes if items remain in queue
    
    Parameters:
    -----------
    room_id : str
        Identifier for the room/TV where collections will be sent
    request : BatchRequest
        Contains 'collection' (optional new collection to add) and 'space_mb' 
        (available space in MB on TV)
    redis_client : Redis
        Redis client for queue management
        
    Returns:
    --------
    dict
        Status information including count of sent items and remaining queue length
    """
    # Step 1: Process incoming collection (if any)
    key = f"dz_queue:{room_id}"
    '''
    Check if queue is full or not. If not, add new collection to queue if provided
    '''
    queue = Queue(redis_client, key)
    queue_length = queue.get_queue_length()
    max_size = queue.get_max_size()
    
    # if queue.exists(request.collection.id):
    #     return {"status": "collection_exists", "room_id": room_id, "queue_length": queue_length}
    if request.collection and queue_length > max_size:
        return {"status": "queue_full", "room_id": room_id, "queue_length": queue_length}
    
    # Step 1: Add new collection to queue when validation passes
    queue.add_collection(request.collection)  
    
    # Step 2: Select collections that fit available space
    collections_to_send = queue.select_collections_fitting_space_greedy(request.available_space_mb)
    
    # Step 3: Remove sent collections from queue and broadcast them
    if len(collections_to_send) > 0:
        for collection in collections_to_send:
            if queue.exists(collection.get('id')):
                queue.remove_collection(collection.get('id'))
                await notify_new_images(room_id, collection)
    
    # Step 4: Schedule retry if items remain in queue
    remaining_count = queue.get_queue_length()
    
    if remaining_count > 0:
        _schedule_retry_loop(room_id, request.available_space_mb)
    
    return {
        "status": "batch_sent", 
        "sent_count": len(collections_to_send), 
        "remaining": remaining_count
    }
 

def _schedule_retry_loop(room_id, space_mb):
    """
    Schedule a background thread to retry sending collections every 10 minutes
    until the queue is empty.
    
    Parameters:
    -----------
    room_id : str
        Room identifier for the retry request
    space_mb : float
        Available space in MB for the retry request
    """
    def retry_loop():
        """Background thread function that periodically retries batch sending"""
        while True:
            # Wait 10 minutes between retry attempts
            time.sleep(600)  # 600 seconds = 10 minutes
            
            try:
                # Send retry request to this same endpoint
                response = httpx.post(
                    f"http://localhost:8080/rooms/{room_id}/batch",
                    json={"space_mb": space_mb}
                )
                
                # Stop retrying if queue is empty
                data = response.json()
                if data.get("remaining", 0) <= 0:
                    logger.debug(f"Queue for room {room_id} is empty, stopping retry loop")
                    break
                    
            except Exception as e:
                logger.error(f"Retry attempt failed: {str(e)}")
                # Continue loop even if request fails
                
    # Start retry loop in background thread
    thread = threading.Thread(target=retry_loop, daemon=True)
    thread.start()
    logger.debug(f"Scheduled retry loop for room {room_id}")