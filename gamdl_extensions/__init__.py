"""
GaDL Extensions Module

This module provides a flexible and extensible framework for adding
additional features and plugins to the GaDL (Gamdl) ecosystem.

The extension system allows for:
- Dynamic plugin loading
- Feature registration
- Dependency management
- Lifecycle management
"""

import os
import importlib
import inspect
from typing import Dict, Any, Type, Callable, Optional
from pathlib import Path
import logging

class ExtensionManager:
    """
    Centralized extension management system
    """
    
    def __init__(
        self, 
        extensions_dir: Optional[str] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize Extension Manager
        
        :param extensions_dir: Directory containing extensions
        :param logger: Logger instance
        """
        self.extensions_dir = extensions_dir or os.path.join(
            os.path.dirname(__file__), 'plugins'
        )
        self.logger = logger or logging.getLogger(__name__)
        
        self._registered_extensions: Dict[str, Any] = {}
        self._extension_hooks: Dict[str, list] = {}
        
        # Ensure extensions directory exists
        os.makedirs(self.extensions_dir, exist_ok=True)
    
    def load_extensions(self) -> None:
        """
        Dynamically load all available extensions
        """
        try:
            for filename in os.listdir(self.extensions_dir):
                if filename.endswith('.py') and not filename.startswith('__'):
                    module_name = f"gamdl_extensions.plugins.{filename[:-3]}"
                    try:
                        module = importlib.import_module(module_name)
                        self._register_module_extensions(module)
                    except Exception as e:
                        self.logger.error(f"Failed to load extension {filename}: {e}")
        except Exception as e:
            self.logger.error(f"Extension loading failed: {e}")
    
    def _register_module_extensions(self, module):
        """
        Register extensions found in a module
        
        :param module: Python module to inspect
        """
        for name, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj) and 
                hasattr(obj, '_is_gamdl_extension') and 
                getattr(obj, '_is_gamdl_extension')
            ):
                self.register_extension(name, obj)
    
    def register_extension(
        self, 
        name: str, 
        extension_class: Type[Any]
    ) -> None:
        """
        Register an extension
        
        :param name: Extension name
        :param extension_class: Extension class
        """
        try:
            # Instantiate extension
            extension_instance = extension_class()
            
            # Store extension
            self._registered_extensions[name] = extension_instance
            
            # Log registration
            self.logger.info(f"Registered extension: {name}")
        except Exception as e:
            self.logger.error(f"Failed to register extension {name}: {e}")
    
    def get_extension(self, name: str) -> Optional[Any]:
        """
        Retrieve a registered extension
        
        :param name: Extension name
        :return: Extension instance or None
        """
        return self._registered_extensions.get(name)
    
    def register_hook(
        self, 
        hook_name: str, 
        callback: Callable
    ) -> None:
        """
        Register a global hook
        
        :param hook_name: Name of the hook
        :param callback: Callback function
        """
        if hook_name not in self._extension_hooks:
            self._extension_hooks[hook_name] = []
        
        self._extension_hooks[hook_name].append(callback)
    
    def trigger_hook(
        self, 
        hook_name: str, 
        *args, 
        **kwargs
    ) -> list:
        """
        Trigger a hook and collect results
        
        :param hook_name: Name of the hook
        :param args: Positional arguments
        :param kwargs: Keyword arguments
        :return: List of hook results
        """
        results = []
        for callback in self._extension_hooks.get(hook_name, []):
            try:
                result = callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Hook {hook_name} execution failed: {e}")
        return results

def gamdl_extension(func=None, *, name=None):
    """
    Decorator to mark classes or functions as GaDL extensions
    
    :param func: Function or class to decorate
    :param name: Optional custom extension name
    :return: Decorated extension
    """
    def decorator(obj):
        obj._is_gamdl_extension = True
        obj._extension_name = name or obj.__name__
        return obj
    
    if func:
        return decorator(func)
    return decorator

class BaseExtension:
    """
    Base class for GaDL extensions
    Provides common interface and lifecycle methods
    """
    
    def __init__(self):
        """
        Initialize extension
        """
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def on_load(self):
        """
        Called when extension is loaded
        Can be overridden by subclasses
        """
        pass
    
    def on_unload(self):
        """
        Called when extension is unloaded
        Can be overridden by subclasses
        """
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Provide extension metadata
        
        :return: Dictionary of extension metadata
        """
        return {
            'name': self.__class__.__name__,
            'version': getattr(self, '__version__', '0.1.0'),
            'description': self.__doc__ or 'No description provided'
        }

def main():
    """
    Example usage and testing of Extension System
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(levelname)s] %(name)s: %(message)s'
    )
    
    # Create Extension Manager
    extension_manager = ExtensionManager()
    
    # Load extensions
    extension_manager.load_extensions()
    
    # Register a global hook
    def example_hook(data):
        """Example hook implementation"""
        print(f"Global hook received: {data}")
        return data.upper()
    
    extension_manager.register_hook('process_data', example_hook)
    
    # Trigger hook
    results = extension_manager.trigger_hook('process_data', "test data")
    print("Hook results:", results)

if __name__ == '__main__':
    main()
