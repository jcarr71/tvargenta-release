100% vibe-coded with Claude Code.

In the words of Claude:

  This fork adds 87 commits of new features, improvements, and bug fixes to the original TVArgenta v2.0. Below is a comprehensive summary of all additions:

  ---
  1. VCR/NFC Physical Tape System

  A major new feature that brings physical VHS tape interaction to TVArgenta using NFC technology.

  Features:
  - NFC Tape Detection: Insert physical "tapes" (NFC tags) to play specific videos
  - Channel 03 VCR Input: Dedicated channel showing:
    - White noise when no NFC reader attached
    - Blue "INSERT TAPE" screen when reader has no tape
    - VCR position counter during playback
  - Position Persistence: Tape playback position is saved and restored across sessions
  - Auto-Rewind: Tapes automatically rewind when they reach the end
  - Rewind Animation: Authentic VHS rewind effect with sound (36+ seconds with gapless audio)
  - Encoder Controls on VCR Channel:
    - Tap: Toggle pause
    - Hold 3+ seconds: Trigger rewind with visual countdown
  - Background Playback: Tape continues playing silently when not on Channel 03
  - QR Code Recording Flow: Empty tapes show a QR code to upload new content from your phone
  - VCR Admin Interface: Web page to register tapes and assign videos
  - Upload Progress Sync: Real-time progress display synchronized between phone and TV

  ---
  2. Broadcast TV Scheduling System

  Emulates authentic 1990s TV programming with scheduled content blocks.

  Features:
  - Weekly Schedule Generation: Runs Sunday at 2:30 AM, assigns series to time slots
  - Daily Schedule Generation: Runs at 3:00 AM, creates second-by-second playback mapping
  - Time-of-Day Programming Zones:
    - Early Morning (4-7 AM)
    - Late Morning (7 AM-12 PM)
    - Afternoon (12-5 PM)
    - Evening (5-9 PM)
    - Night (9 PM-3 AM)
  - 30-Minute Programming Blocks: Content with commercial breaks at start, middle, and end
  - Episode Cursor Tracking: Remembers position in each series for sequential episode playback
  - Back-to-Back Episodes: Weighted probability for consecutive episode scheduling
  - Test Pattern: Plays between 3-4 AM daily
  - Per-Channel Schedule Rebuild: Regenerate schedule for individual channels via UI button
  - In-Memory Schedule Cache: Eliminates disk I/O during playback for smooth performance
  - Comprehensive Test Suite: 27+ tests covering scheduler edge cases

  ---
  3. TV Series Management

  Directory-based organization for TV shows with automatic detection.

  Features:
  - Structured Directory Organization: content/videos/series/{Show Name}/Season {N}/
  - Automatic Series Detection: Scans and indexes series on startup
  - Episode Count Tracking: Shows episode counts per season in the UI
  - Series-Specific Channels: Create channels that only play content from specific series
  - Upload Interface: Dedicated series upload page with progress tracking
  - No Transcoding: Series files are moved directly without re-encoding
  - SMPTE Color Bars: Displays test pattern when channel has no available content

  ---
  4. Redesigned Web Management Interface

  Consolidated and modernized admin pages.

  Features:
  - Unified Library Page: Merged Library and Content Manager into single interface
  - Inline Expanding Cards: Modern card-based UI for channels and series
  - Redesigned Channels Page: Cleaner channel management with expand/collapse
  - Redesigned TV Series Section: Visual series management
  - Content Type Dropdown: Replace generic upload with Movies/Series/Commercials options
  - Duplicate Detection: Client-side duplicate file detection with "already exists" feedback
  - Upload Progress Indicators: Consistent progress tracking across all upload flows
  - "Finalizing..." State: Shows processing status after upload reaches 100%
  - Rebuild Schedule Button: Per-channel schedule regeneration from channel cards

  ---
  5. Background Metadata Daemon

  Automatic background processing for video metadata.

  Features:
  - Multi-Phase Processing:
    - Phase 0: Scan for new files in videos, series, and commercials
    - Phase 1 (Fast): Extract duration and generate thumbnails
    - Phase 2 (Slow): Analyze audio loudness (LUFS)
  - Low-Priority Execution: Uses nice/ionice to avoid impacting playback
  - Sampling Strategy: Analyzes 30-second samples every 5 minutes (not entire file)
  - Long Movie Support: 1-hour timeout for lengthy films
  - Auto-Start: Daemon starts automatically with the application
  - Atomic File Operations: Safe concurrent access to metadata.json
  - Race Condition Fix: Prevents conflicts between app and daemon

  ---
  6. Audio/Volume Improvements

  Loudness normalization and audio quality fixes.

  Features:
  - Loudness Normalization: Fixed -16 LUFS target for consistent volume
  - Dynamic Volume Adjustment: Real-time volume adjustment based on loudness analysis
  - Commercial Volume Matching: Commercials automatically adjusted to match content volume
  - Audio Pop Elimination: ALSA dmix configuration to prevent pops between videos
  - Same-Channel Pop Prevention: No audio artifacts when staying on the same channel

  ---
  7. Commercial System

  Dedicated commercial break handling.

  Features:
  - Commercial Upload Flow: Dedicated upload interface for commercials
  - H.264 Codec Verification: Validates codec compatibility during upload
  - Commercial Video Serving: Flask route to serve commercial files
  - Ghost Video Detection: Prevents orphaned commercials in the system
  - Volume Normalization: Automatic loudness adjustment for commercials

  ---
  8. Channel Improvements

  Enhanced channel functionality.

  Features:
  - Channel Indicator: Visual display of current channel
  - Improved Channel Changing: Faster, more responsive channel switching
  - Rapid Channel Change Fix: Prevents video freeze during quick channel surfing
  - Player State Sync: Prevents player state from falling behind during changes
  - Category-Based Filtering: Channels can filter by content categories

  ---
  9. Timezone Support

  Features:
  - Configurable timezone setting
  - Uses Python ZoneInfo for accurate time handling
  - Affects schedule generation and time-of-day programming

  ---
  10. Performance Optimizations

  Features:
  - Faster Metadata Scanner: Optimized scanning for large libraries
  - Schedule Cache Warm Start: Pre-loads schedule on startup
  - Reduced Disk I/O: In-memory caching for frequently accessed data
  - Double-Load Prevention: Avoids loading videos twice during channel changes
  - Laggy Playback Fix: Smooth looping in broadcast mode

  ---
  11. Bug Fixes

  - Fix TypeError when duracion is null in metadata
  - Fix video URLs for series playback across all code paths
  - Fix series channels failing due to empty tags_incluidos check
  - Fix upload progress tracking and duplicate detection
  - Fix TV seasons display showing all seasons correctly
  - Disable Cast overlay on video elements
  - Fix multiple VCR channel isolation bugs
  - Include videos without metadata in VHS assignment dropdown

  ---
  Summary Statistics

  | Metric               | Value |
  |----------------------|-------|
  | Total Commits        | 87    |
  | Pull Requests Merged | 10    |
  | Major Features Added | 6     |
  | Test Cases Added     | 27+   |

  ---
  This overview documents all significant changes from the original rsappia/TVArgenta v2.0 release. The fork transforms TVArgenta from a basic retro TV experience into a comprehensive broadcast simulation system with physical VHS tape interaction, scheduled programming, and professional-grade audio management.
