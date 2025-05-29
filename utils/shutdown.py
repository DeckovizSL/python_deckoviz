"""
Shutdown handlers for various agent modes in Deckoviz.
"""

import logging
import asyncio
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def personal_painter_shutdown(session, room_name: str, **kwargs):
    """
    Shutdown handler for the personal painter mode.
    
    Args:
        session: The agent session
        room_name: Name of the room
        kwargs: Additional parameters
    """
    logger.info(f"Shutting down personal painter in room {room_name}")
    
    # Save any user data or preferences if needed
    if hasattr(session, "personal_painter"):
        # Get user history before shutting down
        history = session.personal_painter.get_user_history()
        logger.info(f"Personal painter session had {len(history)} interactions")
        
        # Any cleanup needed for the personal painter
        session.personal_painter.clear_history()
    
    # Send a farewell message
    try:
        await session.generate_reply(
            instructions="The user is leaving. Say a brief, friendly goodbye."
        )
    except Exception as e:
        logger.error(f"Error sending farewell message: {e}")
    
    logger.info("Personal painter shutdown complete")

async def onboarding_shutdown(session, room_name: str, **kwargs):
    """
    Shutdown handler for the onboarding mode.
    
    Args:
        session: The agent session
        room_name: Name of the room
        kwargs: Additional parameters
    """
    logger.info(f"Shutting down onboarding in room {room_name}")
    
    # Save any user preferences set during onboarding
    
    # Send a farewell message
    try:
        await session.generate_reply(
            instructions="The user is leaving onboarding. Say a brief goodbye and encourage them to return."
        )
    except Exception as e:
        logger.error(f"Error sending farewell message: {e}")
    
    logger.info("Onboarding shutdown complete")

async def image_search_shutdown(session, room_name: str, **kwargs):
    """
    Shutdown handler for the image search mode.
    
    Args:
        session: The agent session
        room_name: Name of the room
        kwargs: Additional parameters
    """
    logger.info(f"Shutting down image search in room {room_name}")
    
    
    # Send a farewell message
    try:
        await session.generate_reply(
            instructions="The user is leaving image search. Say a brief goodbye."
        )
    except Exception as e:
        logger.error(f"Error sending farewell message: {e}")
    
    logger.info("Image search shutdown complete")
