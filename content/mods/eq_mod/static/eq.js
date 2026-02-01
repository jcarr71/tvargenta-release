/**
 * Audio Equalizer Module
 * 
 * Provides a 3-band parametric equalizer using Web Audio API.
 * - Bass: 100 Hz (±12 dB)
 * - Mid: 1000 Hz (±12 dB)
 * - Treble: 8000 Hz (±12 dB)
 * 
 * Features:
 * - Real-time adjustment (no restart needed)
 * - 5 preset curves (Flat, Warm, Bright, Bass Boost, Dialogue)
 * - Settings persistence
 * - Smooth Q factor for natural sound
 */

class AudioEqualizer {
    constructor(videoElement) {
        this.videoElement = videoElement;
        this.enabled = false;
        this.audioContext = null;
        this.audioSource = null;
        this.gains = {}; // Will hold the three gain nodes
        this.destination = null;
        
        this.settings = {
            bass_gain: 0,
            mid_gain: 0,
            treble_gain: 0,
            active_preset: 'flat'
        };
        
        this.presets = {}; // Will be loaded from server
        
        this.connected = false;
    }
    
    /**
     * Initialize the equalizer and load settings from server.
     */
    async init() {
        console.log('[EQ] Initializing Audio Equalizer...');
        
        try {
            // Load presets from server
            const response = await fetch('/api/eq/presets');
            if (response.ok) {
                const data = await response.json();
                this.presets = data.presets || {};
                console.log('[EQ] Presets loaded:', Object.keys(this.presets));
            }
            
            // Load saved settings
            const settingsResponse = await fetch('/api/eq/settings');
            if (settingsResponse.ok) {
                const data = await settingsResponse.json();
                this.settings = { ...this.settings, ...data.settings };
                console.log('[EQ] Settings loaded:', this.settings);
            }
            
            this.enabled = true;
            console.log('[EQ] Initialized successfully');
        } catch (e) {
            console.error('[EQ] Initialization failed:', e);
            this.enabled = false;
        }
    }
    
    /**
     * Set up Web Audio graph: video → source → bass filter → mid filter → treble filter → destination
     */
    setupAudioGraph() {
        if (this.connected) {
            console.log('[EQ] Audio graph already connected');
            return;
        }
        
        try {
            // Create audio context if needed
            if (!this.audioContext || this.audioContext.state === 'closed') {
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
                console.log('[EQ] Audio context created');
            }
            
            // Resume context if suspended
            if (this.audioContext.state === 'suspended') {
                this.audioContext.resume().then(() => {
                    console.log('[EQ] Audio context resumed');
                });
            }
            
            // Get the media element audio source
            if (!this.audioSource) {
                this.audioSource = this.audioContext.createMediaElementAudioSource(this.videoElement);
            }
            
            // Create filter nodes for each band
            const bassFilter = this.audioContext.createBiquadFilter();
            bassFilter.type = 'lowshelf';
            bassFilter.frequency.value = 100;
            bassFilter.gain.value = this.settings.bass_gain;
            
            const midFilter = this.audioContext.createBiquadFilter();
            midFilter.type = 'peaking';
            midFilter.frequency.value = 1000;
            midFilter.Q.value = 1.0;
            midFilter.gain.value = this.settings.mid_gain;
            
            const trebleFilter = this.audioContext.createBiquadFilter();
            trebleFilter.type = 'highshelf';
            trebleFilter.frequency.value = 8000;
            trebleFilter.gain.value = this.settings.treble_gain;
            
            this.gains = {
                bass: bassFilter,
                mid: midFilter,
                treble: trebleFilter
            };
            
            // Create output node
            this.destination = this.audioContext.destination;
            
            // Connect: source → bass → mid → treble → destination
            this.audioSource.connect(bassFilter);
            bassFilter.connect(midFilter);
            midFilter.connect(trebleFilter);
            trebleFilter.connect(this.destination);
            
            this.connected = true;
            console.log('[EQ] Audio graph connected');
        } catch (e) {
            console.error('[EQ] Failed to set up audio graph:', e);
            this.connected = false;
        }
    }
    
    /**
     * Disconnect the audio graph.
     */
    disconnect() {
        if (!this.connected || !this.audioSource) return;
        
        try {
            this.audioSource.disconnect();
            Object.values(this.gains).forEach(filter => filter.disconnect());
            this.connected = false;
            console.log('[EQ] Audio graph disconnected');
        } catch (e) {
            console.error('[EQ] Failed to disconnect:', e);
        }
    }
    
    /**
     * Set individual band gain.
     * @param {string} band - 'bass', 'mid', or 'treble'
     * @param {number} value - Gain in dB (-12 to +12)
     */
    setBandGain(band, value) {
        if (!this.connected || !this.gains[band]) return;
        
        // Clamp value
        value = Math.max(-12, Math.min(12, value));
        
        this.gains[band].gain.value = value;
        this.settings[`${band}_gain`] = value;
        
        console.log(`[EQ] ${band} set to ${value.toFixed(1)} dB`);
    }
    
    /**
     * Apply a preset curve.
     * @param {string} presetName - Preset key (e.g., 'warm', 'bright')
     */
    applyPreset(presetName) {
        const preset = this.presets[presetName];
        if (!preset) {
            console.warn(`[EQ] Preset not found: ${presetName}`);
            return;
        }
        
        console.log(`[EQ] Applying preset: ${preset.name}`);
        
        this.setBandGain('bass', preset.bass_gain);
        this.setBandGain('mid', preset.mid_gain);
        this.setBandGain('treble', preset.treble_gain);
        
        this.settings.active_preset = presetName;
        this.saveSettings();
    }
    
    /**
     * Reset to flat (no equalization).
     */
    reset() {
        console.log('[EQ] Resetting to flat');
        this.setBandGain('bass', 0);
        this.setBandGain('mid', 0);
        this.setBandGain('treble', 0);
        this.settings.active_preset = 'flat';
        this.saveSettings();
    }
    
    /**
     * Save current settings to server.
     */
    async saveSettings() {
        try {
            const response = await fetch('/api/eq/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ settings: this.settings })
            });
            
            if (response.ok) {
                console.log('[EQ] Settings saved');
            } else {
                console.error('[EQ] Failed to save settings');
            }
        } catch (e) {
            console.error('[EQ] Save failed:', e);
        }
    }
    
    /**
     * Get current settings.
     */
    getSettings() {
        return { ...this.settings };
    }
    
    /**
     * Get all presets.
     */
    getPresets() {
        return { ...this.presets };
    }
}

// Export for use in player
if (typeof window !== 'undefined') {
    window.AudioEqualizer = AudioEqualizer;
}
