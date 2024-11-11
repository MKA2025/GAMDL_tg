"""
Quality Selector Extension for GaDL

Provides advanced quality selection and management for downloads,
including:
- Intelligent quality selection
- Bandwidth-based optimization
- User preference management
- Detailed quality metrics
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Any, Optional, List, Union

from gamdl_extensions import gamdl_extension, BaseExtension

class QualityLevel(Enum):
    """
    Standardized quality levels for different media types
    """
    LOWEST = auto()
    LOW = auto()
    MEDIUM = auto()
    HIGH = auto()
    HIGHEST = auto()
    LOSSLESS = auto()
    CUSTOM = auto()

@dataclass
class QualityProfile:
    """
    Comprehensive quality profile for different media types
    """
    name: str
    media_type: str
    level: QualityLevel
    bitrate: Optional[int] = None
    resolution: Optional[str] = None
    codec: Optional[str] = None
    sample_rate: Optional[int] = None
    
    def __repr__(self):
        return (
            f"QualityProfile(name={self.name}, "
            f"type={self.media_type}, "
            f"level={self.level.name})"
        )

class QualityPreferenceManager:
    """
    Manages user quality preferences and intelligent selection
    """
    
    def __init__(
        self, 
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize Quality Preference Manager
        
        :param logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        
        # Default quality profiles
        self.default_profiles = {
            'song': [
                QualityProfile(
                    name='Low Quality',
                    media_type='song',
                    level=QualityLevel.LOW,
                    bitrate=128,
                    codec='AAC'
                ),
                QualityProfile(
                    name='High Quality',
                    media_type='song',
                    level=QualityLevel.HIGH,
                    bitrate=256,
                    codec='AAC'
                ),
                QualityProfile(
                    name='Lossless',
                    media_type='song',
                    level=QualityLevel.LOSSLESS,
                    bitrate=1411,
                    codec='ALAC'
                )
            ],
            'music_video': [
                QualityProfile(
                    name='SD',
                    media_type='music_video',
                    level=QualityLevel.LOW,
                    resolution='480p'
                ),
                QualityProfile(
                    name='HD',
                    media_type='music_video',
                    level=QualityLevel.HIGH,
                    resolution='1080p'
                ),
                QualityProfile(
                    name='4K',
                    media_type='music_video',
                    level=QualityLevel.HIGHEST,
                    resolution='2160p'
                )
            ]
        }
        
        # User preferences storage
        self.user_preferences: Dict[str, QualityProfile] = {}
    
    def set_user_preference(
        self, 
        media_type: str, 
        profile: QualityProfile
    ):
        """
        Set user preference for a specific media type
        
        :param media_type: Type of media
        :param profile: Quality profile
        """
        self.user_preferences[media_type] = profile
        self.logger.info(f"Updated {media_type} quality preference: {profile}")
    
    def get_quality_profile(
        self, 
        media_type: str, 
        preferred_level: Optional[QualityLevel] = None
    ) -> QualityProfile:
        """
        Intelligently select quality profile
        
        :param media_type: Type of media
        :param preferred_level: Optional preferred quality level
        :return: Selected quality profile
        """
        # Check user preferences first
        if media_type in self.user_preferences:
            return self.user_preferences[media_type]
        
        # If no user preference, use intelligent selection
        profiles = self.default_profiles.get(media_type, [])
        
        if preferred_level:
            # Find closest match to preferred level
            matching_profiles = [
                p for p in profiles if p.level == preferred_level
            ]
            if matching_profiles:
                return matching_profiles[0]
        
        # Default to medium/high quality
        return next(
            (p for p in profiles if p.level == QualityLevel.HIGH),
            profiles[-1] if profiles else None
        )
    
    def estimate_download_size(
        self, 
        track_metadata: Dict[str, Any], 
        quality_profile: QualityProfile
    ) -> float:
        """
        Estimate download size based on quality profile
        
        :param track_metadata: Track metadata
        :param quality_profile: Selected quality profile
        :return: Estimated file size in MB
        """
        base_duration = track_metadata.get('attributes', {}).get('durationInMillis', 0) / 1000
        
        # Simplified size estimation
        bitrate_multiplier = {
            QualityLevel.LOW: 0.5,
            QualityLevel.MEDIUM: 1.0,
            QualityLevel.HIGH: 1.5,
            QualityLevel.HIGHEST: 2.0,
            QualityLevel.LOSSLESS: 3.0
        }
        
        multiplier = bitrate_multiplier.get(quality_profile.level, 1.0)
        estimated_size = (base_duration * (quality_profile.bitrate or 256) / 8192) * multiplier
        
        return estimated_size

@gamdl_extension(name='quality_selector')
class QualitySelectorExtension(BaseExtension):
    """
    Advanced Quality Selection Extension
    
    Provides intelligent and configurable quality selection for downloads
    """
    
    def __init__(self):
        super().__init__()
        self.quality_manager = QualityPreferenceManager(logger=self.logger)
    
    def on_load(self):
        """
        Initialize quality selector capabilities
        """
        self.logger.info("Quality Selector Extension loaded")
    
    def select_media_quality(
        self, 
        track_metadata: Dict[str, Any], 
        media_type: str
    ) -> QualityProfile:
        """
        Select optimal quality for a track
        
        :param track_metadata: Track metadata
        :param media_type: Type of media
        :return: Selected quality profile
        """
        # Determine media type
        quality_profile = self.quality_manager.get_quality_profile(media_type)
        
        # Estimate download size
        estimated_size = self.quality_manager.estimate_download_size(
            track_metadata, 
            quality_profile
        )
        
        self.logger.info(
            f"Selected Quality Profile: {quality_profile}\n"
            f"Estimated Download Size: {estimated_size:.2f} MB"
        )
        
        return quality_profile
    
    def set_quality_preference(
        self, 
        media_type: str, 
        level: QualityLevel
    ):
        """
        Set user's quality preference
        
        :param media_type: Type of media
        :param level: Desired quality level
        """
        available_profiles = self.quality_manager.default_profiles.get(media_type, [])
        matching_profile = next(
            (p for p in available_profiles if p.level == level),
            None
        )
        
        if matching_profile:
            self.quality_manager.set_user_preference(media_type, matching_profile)
        else:
            self.logger.warning(f"No profile found for {media_type} at {level}")

def main():
    """
    Demonstration of Quality Selector Extension
    """ ```python
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(name)s: %(message)s'
    )
    
    # Create Quality Selector Extension
    quality_selector_ext = QualitySelectorExtension()
    
    # Simulate track metadata
    track_metadata = {
        'id': '0987654321',
        'attributes': {
            'name': 'Sample Track',
            'artistName': 'Sample Artist',
            'durationInMillis': 180000  # 3 minutes
        }
    }
    
    # Select media quality
    media_type = 'song'
    selected_quality = quality_selector_ext.select_media_quality(track_metadata, media_type)
    
    print(f"Selected Quality Profile: {selected_quality.name} ({selected_quality.level.name})")
    print(f"Bitrate: {selected_quality.bitrate} kbps, Codec: {selected_quality.codec}")

if __name__ == '__main__':
    main()
