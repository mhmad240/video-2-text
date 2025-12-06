import streamlit as st
from faster_whisper import WhisperModel

@st.cache_resource(show_spinner=False)
def load_whisper_model(model_name, device_info):
    """تحميل النموذج مرة واحدة مع الإعدادات المثلى"""
    try:
        st.info(f"🔄 جاري تحميل النموذج {model_name} على {device_info['device'].upper()}...")
        
        model = WhisperModel(
            model_name,
            device=device_info["device"],
            compute_type=device_info["compute_type"],
            download_root="./models"  # ✅ مجلد مخصص للنماذج
        )
        
        st.success(f"✅ تم تحميل النموذج {model_name} بنجاح على {device_info['device'].upper()}")
        return model
        
    except Exception as e:
        st.error(f"❌ فشل تحميل النموذج: {str(e)}")
        # ✅ Fallback إلى CPU في حالة الخطأ
        try:
            st.warning("🔄 جاري المحاولة على CPU كبديل...")
            model = WhisperModel(
                model_name,
                device="cpu",
                compute_type="int8",
                download_root="./models"
            )
            st.success(f"✅ تم تحميل النموذج {model_name} على CPU بنجاح")
            return model
        except Exception as fallback_error:
            st.error(f"❌ فشل تحميل النموذج على CPU أيضاً: {str(fallback_error)}")
            return None

def clear_model_cache():
    """مسح ذاكرة التخزين المؤقت للنماذج"""
    st.cache_resource.clear()
    st.success("✅ تم مسح ذاكرة التخزين المؤقت للنماذج")