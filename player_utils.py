import json
from pathlib import Path
    
videos_in_queue = []
current_video_index = 0

def change_channel(nuevo_canal_id, resetear_cola=True):

    global videos_in_queue, current_video_index

    with open("/srv/tvargenta/content/active_channel.json", "w", encoding="utf-8") as f:
        json.dump({"channel_id": nuevo_canal_id}, f, indent=2)

    with open("/srv/tvargenta/content/channels.json", "r", encoding="utf-8") as f:
        channels = json.load(f)

    with open("/srv/tvargenta/content/metadata.json", "r", encoding="utf-8") as f:
        metadata = json.load(f)

    with open("/srv/tvargenta/content/configuration.json", "r", encoding="utf-8") as f:
        configuration = json.load(f)
        tags_excluidos = set(configuration.get("tags_excluidos", []))

    channel_info = channels.get(nuevo_canal_id, {})
    tags_prioridad = set(channel_info.get("tags_prioridad", []))

    if resetear_cola:
        videos_in_queue.clear()
        for video_id, datos in metadata.items():
            video_tags = set(datos.get("tags", []))
            if tags_prioridad & video_tags and not (video_tags & tags_excluidos):
                videos_in_queue.append(video_id)
        current_video_index = 0

    if videos_in_queue:
        print(f"[CANAL] {nuevo_canal_id} tiene {len(videos_in_queue)} video(s) validos.")
        print(f"[DEBUG] Lista de videos en cola for {nuevo_canal_id}:")
        for i, vid in enumerate(videos_in_queue):
            print(f"  {i+1}. {vid}")
    else:
        print(f"[CHANNEL] No valid videos for channel {nuevo_canal_id}")
