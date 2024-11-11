"""
Multi-Region Extension for GaDL

This extension provides advanced multi-region support for Apple Music downloads,
including:
- Region switching
- Proxy management
- Storefront manipulation
- Download optimization across regions
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import logging
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

from gamdl_extensions import gamdl_extension, BaseExtension
from gamdl.constants import STOREFRONT_IDS

@dataclass
class RegionConfig:
    """
    Represents configuration for a specific region
    """
    code: str
    name: str
    storefront_id: str
    proxy: Optional[str] = None
    cookies_path: Optional[str] = None
    weight: int = 1
    latency: float = 0.0
    success_rate: float = 1.0

class MultiRegionManager:
    """
    Manages multiple regions for download optimization
    """
    
    def __init__(
        self, 
        regions: Optional[List[RegionConfig]] = None,
        max_workers: int = 5,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize Multi-Region Manager
        
        :param regions: List of region configurations
        :param max_workers: Maximum concurrent region checks
        :param logger: Logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.regions = regions or self._load_default_regions()
        self.max_workers = max_workers
        
        # Performance tracking
        self.region_performance: Dict[str, float] = {}
    
    def _load_default_regions(self) -> List[RegionConfig]:
        """
        Load default regions from constants
        
        :return: List of default region configurations
        """
        return [
            RegionConfig(
                code=code, 
                name=self._get_region_name(code), 
                storefront_id=storefront_id
            ) 
            for code, storefront_id in STOREFRONT_IDS.items()
        ]
    
    def _get_region_name(self, code: str) -> str:
        """
        Get human-readable region name
        
        :param code: Region code
        :return: Region name
        """
        # You can expand this with a more comprehensive mapping
        region_names = {
            'US': 'United States',
            'GB': 'United Kingdom',
            'CA': 'Canada',
            # Add more regions as needed
        }
        return region_names.get(code, code)
    
    def test_region_performance(
        self, 
        test_url: str = 'https://amp-api.music.apple.com/v1/catalog'
    ) -> Dict[str, float]:
        """
        Concurrently test region performance
        
        :param test_url: URL to test region connectivity
        :return: Region performance metrics
        """
        performance_results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._test_region, region, test_url): region 
                for region in self.regions
            }
            
            for future in as_completed(futures):
                region = futures[future]
                try:
                    latency = future.result()
                    performance_results[region.code] = latency
                except Exception as e:
                    self.logger.error(f"Region {region.code} test failed: {e}")
        
        return performance_results
    
    def _test_region(
        self, 
        region: RegionConfig, 
        test_url: str
    ) -> float:
        """
        Test individual region performance
        
        :param region: Region configuration
        :param test_url: URL to test
        :return: Latency in seconds
        """
        try:
            session = requests.Session()
            
            # Configure proxy if available
            if region.proxy:
                session.proxies = {'http': region.proxy, 'https': region.proxy}
            
            # Perform latency test
            start_time = time.time()
            response = session.get(
                test_url, 
                timeout=5,
                headers={'Accept': 'application/json'}
            )
            
            # Validate response
            response.raise_for_status()
            
            latency = time.time() - start_time
            return latency
        
        except requests.RequestException as e:
            self.logger.warning(f"Region {region.code} test failed: {e}")
            raise
    
    def select_optimal_region(
        self, 
        criteria: str = 'performance'
    ) -> RegionConfig:
        """
        Select optimal region based on specified criteria
        
        :param criteria: Selection method
        :return: Selected region configuration
        """
        if criteria == 'performance':
            # Test and rank regions by performance
            performance_results = self.test_region_performance()
            
            # Sort regions by lowest latency
            sorted_regions = sorted(
                self.regions, 
                key=lambda r: performance_results.get(r.code, float('inf'))
            )
            
            return sorted_regions[0]
        
        elif criteria == 'random':
            # Randomly select a region with weighted probability
            import random
            return random.choices(
                self.regions, 
                weights=[r.weight for r in self.regions]
            )[0]
        
        else:
            # Fallback to default region
            return self.regions[0]

@gamdl_extension(name='multi_region')
class MultiRegionExtension(BaseExtension):
    """
    Multi-Region Download Extension for GaDL
    
    Provides advanced region management and download optimization
    """
    
    def __init__(self):
        super().__init__()
        self.region_manager = MultiRegionManager(logger=self.logger)
    
    def on_load(self):
        """
        Initialize multi-region capabilities
        """
        self.logger.info("Multi-Region Extension loaded")
        
        # Perform initial region performance test
        performance_results = self.region_manager.test_region_performance()
        self.logger.info(f"Region Performance: {performance_results}")
    
    def select_download_region(self, track_metadata: Dict[str, Any]) -> RegionConfig:
        """
        Select optimal download region for a specific track
        
        :param track_metadata: Track metadata
        :return: Selected region configuration
        """
        # You can add more sophisticated region selection logic here
        # For example, based on track origin, genre, etc.
        return self.region_manager.select_optimal_region()
    
    def get_proxy_for_region(self, region: RegionConfig) -> Optional[str]:
        """
        Retrieve proxy for a specific region
        
        :param region: Region configuration
        :return: Proxy URL or None
        """
        return region.proxy

def main():
    """
    Demonstration of Multi-Region Extension
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(name)s: %(message)s'
    )
    
    # Create Multi-Region Extension
    multi_region_ext = MultiRegionExtension()
    
    # Simulate track metadata
    track_metadata = {
        'id': '1234567890',
        'attributes': {
            'name': 'Example Track',
            'artistName': 'Example Artist'
        }
    }
    
    # Select download region
    optimal_region = multi_region_ext.select_download_region(track_metadata)
    
    print(f"Optimal Download Region: {optimal_region.name} ({optimal_region.code})")
    print(f"Storefront ID: {optimal_region.storefront_id}")

if __name__ == '__main__':
    main()
