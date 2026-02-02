"""
Encoder & Gaming Mod

Provides NES controller encoder input and RetroPie gaming mode integration.
Routes for entering/exiting gaming mode and encoder-related functionality.
"""

import subprocess
import logging
from flask import jsonify, request

logger = logging.getLogger("tvargenta.encoder_mod")


def init_mod(registry):
    """Initialize encoder mod."""
    logger.info("Encoder & Gaming mod initialized")


def get_routes():
    """Return list of (rule, function, methods) tuples for Flask."""
    return [
        ("/api/gaming", api_gaming, ["POST"]),
    ]


def get_hooks():
    """Return dict of hook registrations for inter-mod communication."""
    return {}


def api_gaming():
    """
    Switch between TVArgenta and gaming mode (RetroPie).

    POST body:
      - action: "enter" -> stop TVArgenta and start EmulationStation (via enter-gaming.service)
      - action: "exit"  -> stop EmulationStation and return to TVArgenta (via return-tvargenta.service)
    """
    data = request.get_json(force=True) or {}
    action = (data.get("action") or "").lower()

    try:
        if action == "enter":
            subprocess.Popen([
                "/usr/bin/sudo",
                "/bin/systemctl",
                "start",
                "enter-gaming.service"
            ])
            logger.info("Switching to gaming mode")
            return jsonify({"ok": True, "switched": "to_gaming"})

        elif action == "exit":
            subprocess.Popen([
                "/usr/bin/sudo",
                "/bin/systemctl",
                "start",
                "return-tvargenta.service"
            ])
            logger.info("Returning from gaming mode")
            return jsonify({"ok": True, "switched": "to_tv"})

        else:
            return jsonify({"ok": False, "error": "unsupported action"}), 400

    except Exception as e:
        logger.error(f"Error in gaming mode switch: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500
