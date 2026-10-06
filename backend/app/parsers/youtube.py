from __future__ import annotations

import json
from app.parsers.base import DocumentBlock


class YouTubeParser:
    async def parse(
        self,
        file_bytes: bytes,
        filename: str,
        mime_type: str | None = None,
        storage_path: str | None = None,
    ) -> list[DocumentBlock]:
        try:
            content_str = file_bytes.decode("utf-8")
            segments = json.loads(content_str)
        except Exception:
            return []

        if not isinstance(segments, list) or not segments:
            return []

        # Extract video_id from filename or storage_path
        # e.g., "dQw4w9WgXcQ.youtube" or "youtube_dQw4w9WgXcQ.youtube"
        base_name = filename.split("/")[-1].split("\\")[-1]
        video_id = base_name.replace(".youtube", "").replace("youtube_", "")

        blocks = []
        current_segments = []
        current_words = 0
        current_duration = 0.0

        def format_time(seconds: float) -> str:
            s = int(seconds)
            h = s // 3600
            m = (s % 3600) // 60
            sec = s % 60
            if h > 0:
                return f"{h:02d}:{m:02d}:{sec:02d}"
            return f"{m:02d}:{sec:02d}"

        def flush_block():
            if not current_segments:
                return
            combined_text = " ".join([seg.get("text", "").strip() for seg in current_segments]).strip()
            if not combined_text:
                return
            
            start_s = current_segments[0].get("start", 0.0)
            last_seg = current_segments[-1]
            end_s = last_seg.get("start", 0.0) + last_seg.get("duration", 0.0)

            time_label = f"[{format_time(start_s)} - {format_time(end_s)}]"
            formatted_content = f"{time_label} {combined_text}"

            # YouTube Watch link with specific start timestamp
            t_seconds = int(start_s)
            yt_media_path = f"https://www.youtube.com/watch?v={video_id}&t={t_seconds}s"

            blocks.append(
                DocumentBlock(
                    type="text",
                    content=formatted_content,
                    page_number=1,  # Videos are page 1
                    media_path=yt_media_path,
                    metadata={
                        "video_id": video_id,
                        "start_seconds": start_s,
                        "end_seconds": end_s,
                        "source": "youtube",
                    },
                )
            )

        for seg in segments:
            text = seg.get("text", "").strip()
            if not text:
                continue
            current_segments.append(seg)
            current_words += len(text.split())
            current_duration += seg.get("duration", 0.0)

            # Flush block when it reaches ~120 words or ~60 seconds of video content
            if current_words >= 120 or current_duration >= 60.0:
                flush_block()
                current_segments = []
                current_words = 0
                current_duration = 0.0

        # Flush any remaining segments
        flush_block()

        return blocks
