import streamlit as st
from faster_whisper import WhisperModel

@st.cache_resource(show_spinner=False)
def _load_model_internal(model_name, device, compute_type):
    """التحميل الفعلي للنموذج (مخزن مؤقتاً)"""
    model = WhisperModel(
        model_name,
        device=device,
        compute_type=compute_type,
        download_root="./models"
    )
    return model

def load_whisper_model(model_name, device_info):
    """تحميل النموذج مع عرض الرسائل المناسبة"""
    
    # إنشاء مفتاح فريد للنموذج
    cache_key = f"{model_name}_{device_info['device']}_{device_info['compute_type']}"
    
    # التحقق من وجود النموذج في session_state
    if 'loaded_models' not in st.session_state:
        st.session_state.loaded_models = {}
    
    # إذا كان النموذج محملاً بالفعل في هذه الجلسة
    if cache_key in st.session_state.loaded_models:
        return st.session_state.loaded_models[cache_key]
    
    # النموذج غير محمل - نعرض رسالة التحميل
    try:
        # ترجمة أسماء النماذج للعربية
        model_names_ar = {
            'tiny': 'الصغير جداً',
            'base': 'الأساسي',
            'small': 'الصغير',
            'medium': 'المتوسط',
            'large': 'الكبير'
        }
        model_name_ar = model_names_ar.get(model_name, model_name)
        device_ar = 'وحدة المعالجة المركزية (CPU)' if device_info['device'] == 'cpu' else 'كرت الشاشة (GPU)'
        
        with st.spinner(f"🔄 جاري تحميل النموذج {model_name_ar} على {device_ar}..."):
            model = _load_model_internal(
                model_name,
                device_info["device"],
                device_info["compute_type"]
            )
        
        # حفظ النموذج في session_state
        st.session_state.loaded_models[cache_key] = model
        
        st.success(f"✅ تم تحميل النموذج {model_name_ar} بنجاح!")
        return model
        
    except Exception as e:
        st.error(f"❌ فشل تحميل النموذج: {str(e)}")
        # Fallback إلى CPU
        try:
            st.warning("🔄 جاري المحاولة على CPU كبديل...")
            model = _load_model_internal(
                model_name,
                "cpu",
                "int8"
            )
            # حفظ النموذج البديل
            fallback_key = f"{model_name}_cpu_int8"
            st.session_state.loaded_models[fallback_key] = model
            
            st.success(f"✅ تم تحميل النموذج على CPU بنجاح")
            return model
        except Exception as fallback_error:
            st.error(f"❌ فشل تحميل النموذج على CPU أيضاً: {str(fallback_error)}")
            return None

def clear_model_cache():
    """مسح ذاكرة التخزين المؤقت للنماذج"""
    st.cache_resource.clear()
    if 'loaded_models' in st.session_state:
        st.session_state.loaded_models = {}
    st.success("✅ تم مسح ذاكرة التخزين المؤقت للنماذج")