# هذا الملف يجعل مجلد modules حزمة Python صالحة
from .device_manager import setup_compute_device, get_device_info
from .model_loader import load_whisper_model
from .file_processor import ProcessController, process_uploaded_file, process_youtube_url, translate_to_arabic
from .ui_components import (
    display_progress_indicator, display_results, render_about_tab,
    render_file_upload_section, render_youtube_section, 
    render_model_selection, render_control_buttons
)

__all__ = [
    'setup_compute_device',
    'get_device_info', 
    'load_whisper_model',
    'ProcessController',
    'process_uploaded_file',
    'process_youtube_url',
    'translate_to_arabic',
    'display_progress_indicator',
    'display_results',
    'render_about_tab',
    'render_file_upload_section',
    'render_youtube_section',
    'render_model_selection',
    'render_control_buttons'
]