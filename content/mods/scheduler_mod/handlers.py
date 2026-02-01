"""
Broadcast Scheduler Mod

Provides authentic 1990s TV programming with daily/weekly schedule generation.
Routes for schedule management and rebuild endpoints.
"""

def init_mod(registry):
    """Initialize scheduler mod."""
    import logging
    logger = logging.getLogger("tvargenta.scheduler_mod")
    logger.info("Broadcast Scheduler mod initialized")

def get_routes():
    """Return list of (rule, function, methods) tuples for Flask."""
    return [
        ("/api/rebuild_schedule/<canal_id>", rebuild_schedule_endpoint, ["POST"]),
        ("/api/schedule/status", get_schedule_status, ["GET"]),
        ("/api/schedule/rebuild_all", rebuild_all_schedules, ["POST"]),
    ]

def get_hooks():
    """Return list of hook registrations for inter-mod communication."""
    return [
        ("daily_schedule", on_daily_schedule),
        ("weekly_schedule", on_weekly_schedule),
    ]

def rebuild_schedule_endpoint(canal_id):
    """Rebuild schedule for a specific channel."""
    from flask import jsonify
    import logging
    from scheduler import generate_daily_schedule, generate_weekly_schedule
    
    logger = logging.getLogger("tvargenta.scheduler_mod")
    
    try:
        logger.info(f"Rebuilding schedule for channel {canal_id}")
        
        # Regenerate weekly schedule
        generate_weekly_schedule()
        logger.info(f"Weekly schedule regenerated")
        
        # Regenerate daily schedule
        generate_daily_schedule()
        logger.info(f"Daily schedule regenerated")
        
        return jsonify({
            "status": "ok",
            "message": f"Schedule rebuilt for channel {canal_id}"
        })
    except Exception as e:
        logger.error(f"Failed to rebuild schedule: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

def get_schedule_status():
    """Get current schedule status."""
    from flask import jsonify
    from pathlib import Path
    from settings import CONTENT_DIR
    import json
    
    try:
        weekly_file = CONTENT_DIR / "weekly_schedule.json"
        daily_file = CONTENT_DIR / "daily_schedule.json"
        
        weekly_exists = weekly_file.exists()
        daily_exists = daily_file.exists()
        
        weekly_size = weekly_file.stat().st_size if weekly_exists else 0
        daily_size = daily_file.stat().st_size if daily_exists else 0
        
        weekly_time = None
        if weekly_exists:
            mtime = weekly_file.stat().st_mtime
            weekly_time = str(mtime)
        
        daily_time = None
        if daily_exists:
            mtime = daily_file.stat().st_mtime
            daily_time = str(mtime)
        
        return jsonify({
            "status": "ok",
            "weekly_schedule": {
                "exists": weekly_exists,
                "size": weekly_size,
                "modified": weekly_time
            },
            "daily_schedule": {
                "exists": daily_exists,
                "size": daily_size,
                "modified": daily_time
            }
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

def rebuild_all_schedules():
    """Rebuild all schedules."""
    from flask import jsonify
    import logging
    from scheduler import generate_daily_schedule, generate_weekly_schedule
    
    logger = logging.getLogger("tvargenta.scheduler_mod")
    
    try:
        logger.info("Rebuilding all schedules")
        
        # Regenerate weekly schedule
        generate_weekly_schedule()
        logger.info("Weekly schedule regenerated")
        
        # Regenerate daily schedule
        generate_daily_schedule()
        logger.info("Daily schedule regenerated")
        
        return jsonify({
            "status": "ok",
            "message": "All schedules rebuilt successfully"
        })
    except Exception as e:
        logger.error(f"Failed to rebuild schedules: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

def on_daily_schedule(schedule_data):
    """Hook called when daily schedule is generated."""
    import logging
    logger = logging.getLogger("tvargenta.scheduler_mod")
    logger.info("Daily schedule generated")

def on_weekly_schedule(schedule_data):
    """Hook called when weekly schedule is generated."""
    import logging
    logger = logging.getLogger("tvargenta.scheduler_mod")
    logger.info("Weekly schedule generated")
