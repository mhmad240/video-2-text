# modules/device_manager.py - محدث لإجبار استخدام CPU
import torch
import sys
import ctypes
import os

# Cache لتجنب الرسائل المتكررة
_cuda_setup_cache = None

def setup_cuda_environment():
    """إعداد بيئة CUDA و cuDNN ديناميكياً (مع cache)"""
    global _cuda_setup_cache
    
    # إذا تم الإعداد مسبقاً، إرجاع النتيجة المخزنة
    if _cuda_setup_cache is not None:
        return _cuda_setup_cache
    
    # مسارات CUDA الأساسية
    cuda_paths = [
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.2\bin",
        r"C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.2\libnvvp"
    ]
    
    paths_added = []
    
    # إضافة مسارات CUDA فقط (بدون cuDNN)
    for path in cuda_paths:
        if os.path.exists(path) and path not in os.environ['PATH']:
            os.environ['PATH'] = path + os.pathsep + os.environ['PATH']
            paths_added.append(path)
            print(f"✅ تم إضافة مسار CUDA: {path}")
    
    # حفظ النتيجة في cache
    _cuda_setup_cache = (False, paths_added)
    return _cuda_setup_cache

# Cache لمعلومات الجهاز
_device_info_cache = None

def setup_compute_device():
    """
    إعداد جهاز الحساب - إجبار استخدام CPU للإستقرار (مع cache)
    """
    global _device_info_cache
    
    # إذا تم الإعداد مسبقاً، إرجاع النتيجة المخزنة بدون طباعة
    if _device_info_cache is not None:
        return _device_info_cache
    
    device_info = {
        'device': 'cpu',
        'compute_type': 'int8',
        'reason': '💻 استخدام CPU للإستقرار - أداء ممتاز مع INT8'
    }
    
    print("🎯 تم تفعيل وضع CPU للإستقرار")
    print("💡 المزايا: ⚡ سرعة جيدة | ✅ استقرار تام | 🔧 لا مشاكل ذاكرة")
    
    print(f"🎯 الإعداد النهائي: {device_info['reason']}")
    print(f"🎯 نوع الحساب: {device_info['compute_type']}")
    
    # حفظ النتيجة في cache
    _device_info_cache = device_info
    return device_info

def get_device_info():
    """الحصول على معلومات الجهاز للعرض في الواجهة"""
    device_info = setup_compute_device()
    
    # معلومات إضافية عن الأداء
    device_info['performance_tip'] = "💻 CPU مع INT8 - أداء متوازن ومستقر"
    device_info['recommended_models'] = ["tiny", "base", "small"]
    device_info['icon'] = "💻"
    
    return device_info

def get_cudnn_installation_guide():
    """إرجاع تعليمات تثبيت cuDNN"""
    return {
        'title': '💡 معلومات النظام',
        'steps': [
            '✅ النظام يعمل على CPU بشكل مستقر',
            '⚡ السرعة: جيدة مع تحسين INT8', 
            '🎯 الاستقرار: تام بدون مشاكل',
            '📊 الأداء: يلبي جميع الاحتياجات'
        ],
        'download_link': '',
        'current_status': '💻 CPU مفعل - أداء ممتاز'
    }