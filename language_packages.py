"""
Agricultural Language Packages Module
Provides multilingual dictionaries, localized agricultural terms,
UI translations, and downloadable language packs for the Automated Site-Specific Pesticide Application.
"""

LANGUAGE_META = {
    'ta': {'name': 'Tamil', 'native': 'தமிழ்', 'flag': '🇮🇳'},
    'en': {'name': 'English', 'native': 'English', 'flag': '🇬🇧'},
    'hi': {'name': 'Hindi', 'native': 'हिन्दी', 'flag': '🇮🇳'},
    'te': {'name': 'Telugu', 'native': 'తెలుగు', 'flag': '🇮🇳'},
    'kn': {'name': 'Kannada', 'native': 'ಕನ್ನಡ', 'flag': '🇮🇳'},
    'ml': {'name': 'Malayalam', 'native': 'മലയാളം', 'flag': '🇮🇳'},
    'mr': {'name': 'Marathi', 'native': 'मराठी', 'flag': '🇮🇳'},
    'bn': {'name': 'Bengali', 'native': 'বাংলা', 'flag': '🇮🇳'},
    'gu': {'name': 'Gujarati', 'native': 'ગુજરાતી', 'flag': '🇮🇳'},
    'pa': {'name': 'Punjabi', 'native': 'ਪੰਜਾਬੀ', 'flag': '🇮🇳'},
    'or': {'name': 'Odia', 'native': 'ଓଡ଼ିଆ', 'flag': '🇮🇳'},
    'as': {'name': 'Assamese', 'native': 'অসমীয়া', 'flag': '🇮🇳'},
    'ur': {'name': 'Urdu', 'native': 'اردو', 'flag': '🇮🇳'},
    'sa': {'name': 'Sanskrit', 'native': 'संस्कृतम्', 'flag': '🇮🇳'},
    'ne': {'name': 'Nepali', 'native': 'नेपाली', 'flag': '🇮🇳'},
    'sd': {'name': 'Sindhi', 'native': 'سنڌي / सिन्धी', 'flag': '🇮🇳'},
    'gom': {'name': 'Konkani', 'native': 'कोंकणी', 'flag': '🇮🇳'},
    'mai': {'name': 'Maithili', 'native': 'मैथिली', 'flag': '🇮🇳'},
    'bho': {'name': 'Bhojpuri', 'native': 'भोजपुरी', 'flag': '🇮🇳'},
    'doi': {'name': 'Dogri', 'native': 'डोगरी', 'flag': '🇮🇳'},
    'mni-Mtei': {'name': 'Manipuri', 'native': 'মৈতৈলোন্', 'flag': '🇮🇳'},
    'ks': {'name': 'Kashmiri', 'native': 'كٲشُر', 'flag': '🇮🇳'},
    'sat': {'name': 'Santali', 'native': 'ᱥᱟᱱᱛᱟᱲᱤ', 'flag': '🇮🇳'},
    'es': {'name': 'Spanish', 'native': 'Español', 'flag': '🇪🇸'},
    'fr': {'name': 'French', 'native': 'Français', 'flag': '🇫🇷'},
    'de': {'name': 'German', 'native': 'Deutsch', 'flag': '🇩🇪'},
    'ar': {'name': 'Arabic', 'native': 'العربية', 'flag': '🇸🇦'},
    'zh-CN': {'name': 'Chinese', 'native': '中文', 'flag': '🇨🇳'},
    'ru': {'name': 'Russian', 'native': 'Русский', 'flag': '🇷🇺'},
    'pt': {'name': 'Portuguese', 'native': 'Português', 'flag': '🇵🇹'},
    'ja': {'name': 'Japanese', 'native': '日本語', 'flag': '🇯🇵'}
}

# Core translation dictionary for UI and Agriculture
BASE_TRANSLATIONS = {
    'en': {
        'app_title': 'Automated Site-Specific Pesticide Application',
        'app_subtitle': 'Smart Plant Pathology & Analytics Platform',
        'nav_home': 'Home',
        'nav_about': 'About',
        'nav_services': 'Services',
        'nav_features': 'Features',
        'nav_contact': 'Contact',
        'nav_login_reg': 'Login / Register',
        'nav_diagnostics': 'Plant Diagnosis',
        'nav_analytics': 'Field Analytics',
        'nav_archive': 'Scan Archive',
        'nav_admin': 'Admin Panel',
        'nav_logout': 'Logout',
        
        # Camera & Capture
        'title_foliage_capture': '2. Foliage Image Capture',
        'tab_upload_file': 'Upload Image',
        'tab_live_camera': 'Live Camera (Phone / Web)',
        'dropzone_title': 'Click or Drag & Drop Leaf Image',
        'dropzone_sub': 'Supports JPG, PNG, WebP or direct Camera photo',
        'btn_flip_camera': 'Flip Camera',
        'btn_close_camera': 'Close Camera',
        'reticle_hint': 'Align leaf / infected plant part inside frame',
        'reticle_sub': 'Hold steady for sharp focus',
        'btn_capture_instant': 'Take Picture Instantly',
        'btn_retake': 'Retake Photo',
        'btn_take_another': 'Capture Again',
        'msg_snapshot_ready': 'Snapshot Ready! Specimen captured from live camera.',
        'btn_run_diagnostics': 'Run Full 5-Model Pathology Diagnostics',
        'status_live_camera': 'LIVE CAMERA ACTIVE',
        'status_camera_error': 'Camera inaccessible. Please allow camera permissions or upload an image.',
        
        # Form Parameters
        'title_field_params': '1. Field & Crop Parameters',
        'label_crop_type': 'Target Crop Type',
        'placeholder_crop_type': 'e.g. Tomato, Potato, Apple, Grape, Rice',
        'label_state': 'State (India)',
        'select_state': 'Select Indian State',
        'label_district': 'District / Field Area',
        'select_district': 'Select District',
        
        # Diagnostic Results
        'results_placeholder_title': 'No Leaf Sample Analyzed Yet',
        'results_placeholder_desc': 'Upload a leaf image or snap a live camera photo to execute multi-model inference, physiological disease staging, and 4-tier action plans tailored to your state and district.',
        'lbl_confidence': 'Confidence',
        'lbl_severity': 'Severity',
        'lbl_damage': 'Damage',
        'lbl_urgency': 'Action Urgency',
        'lbl_cwsi': 'Water Stress Index (CWSI)',
        'lbl_chlorophyll': 'Chlorophyll Index',
        'lbl_necrosis': 'Necrosis Ratio',
        'lbl_canopy_temp': 'Canopy Δ Temp',
        'tier1_immediate': 'Tier 1 — Immediate Remediation Protocols',
        'tier2_organic': 'Tier 2 — Bio-Fungicides & Organic Remediation',
        'tier3_chemical': 'Tier 3 — Precision Chemical Formulations (CIB&RC Compliant)',
        'tier4_nutrition': 'Tier 4 — Soil Nutrition & Foliar Micro-Nutrients',
        'lbl_multi_model': 'Multi-Model Algorithm Ensemble Predictions',
        'lbl_consensus': 'Ensemble Consensus Score',
        'lbl_climate_specs': 'Regional Climate Alert & Growth Specs',
        
        # Language Options
        'btn_download_lang_package': 'Download Language Package (.JSON)',
        'btn_dl_lang': 'Download Pack',
        'lbl_select_language': 'Choose Interface Language',
        'msg_lang_downloaded': 'Language package downloaded successfully for offline use.',
        'msg_lang_switched': 'Whole page language converted successfully.',

        # Auth
        'btn_signin': 'Sign In to Dashboard',
        'btn_register': 'Register Account (Pending Admin Approval)',
        'lbl_username': 'Username',
        'lbl_password': 'Password',
        'lbl_forgot_password': 'Forgot Password?'
    },
    'ta': {
        'app_title': 'தானியங்கி குறிப்பிட்ட இடத்திற்கான பூச்சிக்கொல்லி பயன்பாடு',
        'app_subtitle': 'துல்லிய தாவர நோயியல் மற்றும் வேளாண் பகுப்பாய்வு தளம்',
        'nav_home': 'முகப்பு',
        'nav_about': 'பற்றி',
        'nav_services': 'சேவைகள்',
        'nav_features': 'அம்சங்கள்',
        'nav_contact': 'தொடர்பு கொள்ள',
        'nav_login_reg': 'உள்நுழைவு / பதிவுசெய்க',
        'nav_diagnostics': 'தாவர நோய் கண்டறிதல்',
        'nav_analytics': 'வயல் பகுப்பாய்வு',
        'nav_archive': 'ஆய்வு காப்பகம்',
        'nav_admin': 'நிர்வாக குழு',
        'nav_logout': 'வெளியேறு',
        
        # Camera & Capture
        'title_foliage_capture': '2. இலை படம் எடுத்தல் (நேரடி கேமரா)',
        'tab_upload_file': 'படத்தை பதிவேற்று',
        'tab_live_camera': 'நேரடி கேமரா (மொபைல் / கணினி)',
        'dropzone_title': 'இலை படத்தை கிளிக் செய்து தேர்ந்தெடுக்கவும் அல்லது இழுத்துப் போடவும்',
        'dropzone_sub': 'JPG, PNG, WebP அல்லது நேரடி கேமரா புகைப்படத்தை ஏற்கிறது',
        'btn_flip_camera': 'கேமரா திருப்புக (முன்/பின்)',
        'btn_close_camera': 'கேமராவை மூடு',
        'reticle_hint': 'இலை அல்லது பாதிக்கப்பட்ட பகுதியை சட்டகத்திற்குள் பொருத்தவும்',
        'reticle_sub': 'தெளிவான புகைப்படத்திற்கு கேமராவை அசையாமல் பிடிக்கவும்',
        'btn_capture_instant': 'உடனடியாக படம் எடுக்கவும்',
        'btn_retake': 'மீண்டும் படம் எடுக்கவும்',
        'btn_take_another': 'மீண்டும் எடுக்கவும்',
        'msg_snapshot_ready': 'படம் தயார்! நேரடி கேமராவிலிருந்து இலை படம் எடுக்கப்பட்டது.',
        'btn_run_diagnostics': 'முழு 5-மாதிரி தாவர நோய் கண்டறிதலைத் தொடங்கு',
        'status_live_camera': 'நேரடி கேமரா இயங்குகிறது',
        'status_camera_error': 'கேமராவை இயக்க முடியவில்லை. தயவுசெய்து கேமரா அனுமதியை வழங்கவும் அல்லது படத்தை பதிவேற்றவும்.',
        
        # Form Parameters
        'title_field_params': '1. வயல் மற்றும் பயிர் விவரங்கள்',
        'label_crop_type': 'பயிர் வகை',
        'placeholder_crop_type': 'எ.கா: தக்காளி, உருளைக்கிழங்கு, ஆப்பிள், திராட்சை, நெல்',
        'label_state': 'மாநிலம் (இந்தியா)',
        'select_state': 'மாநிலத்தைத் தேர்ந்தெடுக்கவும்',
        'label_district': 'மாவட்டம் / பயிர் பகுதி',
        'select_district': 'மாவட்டத்தைத் தேர்ந்தெடுக்கவும்',
        
        # Diagnostic Results
        'results_placeholder_title': 'இன்னும் இலை மாதிரி ஆய்வு செய்யப்படவில்லை',
        'results_placeholder_desc': 'உங்கள் மாநிலம் மற்றும் மாவட்டத்திற்கு ஏற்ற 4-அடுக்கு சிகிச்சை திட்டங்களை உடனடியாகப் பெற நேரடி கேமராவில் படம் எடுக்கவும் அல்லது பதிவேற்றவும்.',
        'lbl_confidence': 'துல்லியம்',
        'lbl_severity': 'தீவிரம்',
        'lbl_damage': 'சேத வீதம்',
        'lbl_urgency': 'நடவடிக்கை அவசரம்',
        'lbl_cwsi': 'நீர் அழுத்தக் குறியீடு (CWSI)',
        'lbl_chlorophyll': 'பச்சைய குறியீடு',
        'lbl_necrosis': 'திசு அழுகல் வீதம்',
        'lbl_canopy_temp': 'இலை வெப்பநிலை வேறுபாடு',
        'tier1_immediate': 'அடுக்கு 1 — உடனடி தீர்வு வழிகாட்டுதல்கள்',
        'tier2_organic': 'அடுக்கு 2 — இயற்கை பூஞ்சாணக் கொல்லிகள் & இயற்கை முறைகள்',
        'tier3_chemical': 'அடுக்கு 3 — துல்லியமான ரசாயன பரிந்துரைகள் (CIB&RC அங்கீகாரம்)',
        'tier4_nutrition': 'அடுக்கு 4 — மண் சத்து மற்றும் இலை நுண்ணூட்டச்சத்து மேலாண்மை',
        'lbl_multi_model': '5-மாதிரி செயற்கை நுண்ணறிவு கணிப்புகள்',
        'lbl_consensus': 'மாதிரி ஒருமித்த கருத்து',
        'lbl_climate_specs': 'மண்டல காலநிலை எச்சரிக்கை & பயிர் வளர்ச்சி வழிகாட்டல்',
        
        # Language Options
        'btn_download_lang_package': 'தமிழ் மொழி தொகுப்பை பதிவிறக்குக (.JSON)',
        'btn_dl_lang': 'மொழி தொகுப்பு பதிவிறக்கம்',
        'lbl_select_language': 'மொழியினைத் தேர்ந்தெடுக்கவும்',
        'msg_lang_downloaded': 'தமிழ் மொழித் தொகுப்பு ஆஃப்லைன் பயன்பாட்டிற்கு வெற்றிகரமாக பதிவிறக்கம் செய்யப்பட்டது.',
        'msg_lang_switched': 'முழு பக்கமும் வெற்றிகரமாக தமிழில் மாற்றப்பட்டது.',

        # Auth
        'btn_signin': 'டாஷ்போர்டில் உள்நுழையவும்',
        'btn_register': 'விவசாயி கணக்கு பதிவு (நிர்வாக அனுமதிக்கு உட்பட்டது)',
        'lbl_username': 'பயனர் பெயர்',
        'lbl_password': 'கடவுச்சொல்',
        'lbl_forgot_password': 'கடவுச்சொல் மறந்துவிட்டதா?'
    },
    'hi': {
        'app_title': 'स्वचालित स्थान-विशिष्ट कीटनाशक अनुप्रयोग',
        'app_subtitle': 'सटीक पादप विकृति विज्ञान एवं कृषि विश्लेषण मंच',
        'nav_home': 'होम',
        'nav_about': 'परिचय',
        'nav_services': 'सेवाएं',
        'nav_features': 'विशेषताएं',
        'nav_contact': 'संपर्क करें',
        'nav_login_reg': 'लॉग इन / पंजीकरण',
        'nav_diagnostics': 'पौध रोग निदान',
        'nav_analytics': 'खेत विश्लेषण',
        'nav_archive': 'स्कैन संग्रह',
        'nav_admin': 'व्यवस्थापक पैनल',
        'nav_logout': 'लॉग आउट',
        
        # Camera & Capture
        'title_foliage_capture': '2. पत्ती की छवि कैप्चर (लाइव कैमरा)',
        'tab_upload_file': 'छवि अपलोड करें',
        'tab_live_camera': 'लाइव कैमरा (फ़ोन / लैपटॉप / वेबकैम)',
        'dropzone_title': 'पत्ती की तस्वीर चुनें या खींचकर यहां लाएं',
        'dropzone_sub': 'JPG, PNG, WebP या सीधे कैमरा फोटो समर्थित',
        'btn_flip_camera': 'कैमरा बदलें (आगे / पीछे)',
        'btn_close_camera': 'कैमरा बंद करें',
        'reticle_hint': 'पत्ती या संक्रमित भाग को फ्रेम में संरेखित करें',
        'reticle_sub': 'स्पष्ट फोकस के लिए कैमरा स्थिर रखें',
        'btn_capture_instant': 'तुरंत तस्वीर लें (Instant Capture)',
        'btn_retake': 'पुनः तस्वीर लें',
        'btn_take_another': 'दुबारा लें',
        'msg_snapshot_ready': 'तस्वीर तैयार! लाइव कैमरे से पत्ती का नमूना सफलतापूर्वक लिया गया।',
        'btn_run_diagnostics': 'संपूर्ण 5-मॉडल पौध रोग निदान शुरू करें',
        'status_live_camera': 'लाइव कैमरा सक्रिय',
        'status_camera_error': 'कैमरा अनुपलब्ध है। कृपया अनुमति दें या फोटो अपलोड करें।',
        
        # Form Parameters
        'title_field_params': '1. खेत एवं फसल पैरामीटर',
        'label_crop_type': 'लक्षित फसल प्रकार',
        'placeholder_crop_type': 'उदा. टमाटर, आलू, सेब, अंगूर, धान/चावल',
        'label_state': 'राज्य (भारत)',
        'select_state': 'भारतीय राज्य चुनें',
        'label_district': 'जिला / खेत क्षेत्र',
        'select_district': 'जिला चुनें',
        
        # Diagnostic Results
        'results_placeholder_title': 'अभी तक किसी पत्ती के नमूने का विश्लेषण नहीं हुआ',
        'results_placeholder_desc': 'अपने राज्य और जिले के अनुकूल 4-स्तरीय उपचार योजना तुरंत पाने के लिए लाइव कैमरे से फोटो लें या पत्ती अपलोड करें।',
        'lbl_confidence': 'सटीकता / विश्वास',
        'lbl_severity': 'गंभीरता',
        'lbl_damage': 'क्षति प्रतिशत',
        'lbl_urgency': 'कार्रवाई की तात्कालिकता',
        'lbl_cwsi': 'जल तनाव सूचकांक (CWSI)',
        'lbl_chlorophyll': 'क्लोरोफिल सूचकांक',
        'lbl_necrosis': 'ऊतक क्षय अनुपात',
        'lbl_canopy_temp': 'चंदवा तापमान अंतर',
        'tier1_immediate': 'स्तर 1 — त्वरित निवारक उपाय',
        'tier2_organic': 'स्तर 2 — जैविक कवकनाशी एवं प्राकृतिक उपचार',
        'tier3_chemical': 'स्तर 3 — सटीक रासायनिक कीटनाशक (CIB&RC अनुशंसित)',
        'tier4_nutrition': 'स्तर 4 — मृदा पोषण एवं पर्ण सूक्ष्म पोषक तत्व',
        'lbl_multi_model': '5-मॉडल AI एल्गोरिदम भविष्यवाणी',
        'lbl_consensus': 'एन्सेम्बल सहमति स्कोर',
        'lbl_climate_specs': 'क्षेत्रीय मौसम चेतावनी एवं विकास आवश्यकताएं',
        
        # Language Options
        'btn_download_lang_package': 'हिन्दी भाषा पैकेज डाउनलोड करें (.JSON)',
        'btn_dl_lang': 'भाषा पैकेज डाउनलोड',
        'lbl_select_language': 'भाषा चुनें',
        'msg_lang_downloaded': 'हिन्दी भाषा पैकेज ऑफ़लाइन उपयोग हेतु सफलतापूर्वक डाउनलोड हो गया।',
        'msg_lang_switched': 'पूरा पृष्ठ सफलतापूर्वक हिन्दी में परिवर्तित कर दिया गया है।',

        # Auth
        'btn_signin': 'डैशबोर्ड में प्रवेश करें',
        'btn_register': 'किसान खाता पंजीकृत करें',
        'lbl_username': 'उपयोगकर्ता नाम',
        'lbl_password': 'पासवर्ड',
        'lbl_forgot_password': 'पासवर्ड भूल गए?'
    },
    'te': {
        'app_title': 'స్వయంచాలక సైట్-నిర్దిష్ట పురుగుమందుల అప్లికేషన్',
        'app_subtitle': 'స్మార్ట్ ప్లాంట్ పాథాలజీ మరియు వ్యవసాయ విశ్లేషణల వేదిక',
        'nav_home': 'హోమ్',
        'nav_about': 'గురించి',
        'nav_services': 'సేవలు',
        'nav_features': 'ఫీచర్లు',
        'nav_contact': 'సంప్రదించండి',
        'nav_login_reg': 'లాగిన్ / రిజిస్టర్',
        'nav_diagnostics': 'మొక్కల వ్యాధి నిర్ధారణ',
        'nav_analytics': 'ఫీల్డ్ విశ్లేషణలు',
        'nav_archive': 'స్కాన్ ఆర్కైవ్',
        'nav_admin': 'అడ్మిన్ ప్యానెల్',
        'nav_logout': 'లాగౌట్',
        'title_foliage_capture': '2. ఆకు చిత్రం క్యాప్చర్ (లైవ్ కెమెరా)',
        'tab_upload_file': 'చిత్రం అప్‌లోడ్ చేయండి',
        'tab_live_camera': 'లైవ్ కెమెరా (ఫోన్ / ల్యాప్‌టాప్)',
        'btn_capture_instant': 'తక్షణమే ఫోటో తీయండి',
        'btn_flip_camera': 'కెమెరా మార్చండి',
        'btn_retake': 'మళ్ళీ తీయండి',
        'btn_download_lang_package': 'తెలుగు భాష ప్యాకేజీని డౌన్‌లోడ్ చేయండి (.JSON)',
        'btn_dl_lang': 'డౌన్‌లోడ్ ప్యాకేజీ',
        'msg_lang_switched': 'మొత్తం పేజీ తెలుగులోకి విజయవంతంగా మార్చబడింది.'
    },
    'kn': {
        'app_title': 'ಸ್ವಯಂಚಾಲಿತ ಸೈಟ್-ನಿರ್ದಿಷ್ಟ ಕೀಟನಾಶಕ ಬಳಕೆ',
        'app_subtitle': 'ನಿಖರ ಸಸ್ಯ ರೋಗಶಾಸ್ತ್ರ ಮತ್ತು ಕೃಷಿ ವಿಶ್ಲೇಷಣೆ ವೇದಿಕೆ',
        'nav_home': 'ಮುಖಪುಟ',
        'nav_diagnostics': 'ಸಸ್ಯ ರೋಗ ಪತ್ತೆ',
        'nav_analytics': 'ಕ್ಷೇತ್ರ ವಿಶ್ಲೇಷಣೆ',
        'title_foliage_capture': '2. ಎಲೆಯ ಚಿತ್ರ ಸೆರೆಹಿಡಿಯುವಿಕೆ (ಲೈವ್ ಕ್ಯಾಮೆರಾ)',
        'tab_upload_file': 'ಚಿತ್ರ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ',
        'tab_live_camera': 'ಲೈವ್ ಕ್ಯಾಮೆರಾ (ಫೋನ್ / ಲ್ಯಾಪ್‌ಟಾಪ್)',
        'btn_capture_instant': 'ತಕ್ಷಣ ಫೋಟೋ ತೆಗೆಯಿರಿ',
        'btn_download_lang_package': 'ಕನ್ನಡ ಭಾಷಾ ಪ್ಯಾಕೇಜ್ ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ (.JSON)',
        'btn_dl_lang': 'ಡೌನ್‌ಲೋಡ್ ಪ್ಯಾಕ್',
        'msg_lang_switched': 'ಸಂಪೂರ್ಣ ಪುಟವನ್ನು ಕನ್ನಡಕ್ಕೆ ಯಶಸ್ವಿಯಾಗಿ ಬದಲಾಯಿಸಲಾಗಿದೆ.'
    },
    'ml': {
        'app_title': 'ഓട്ടോമേറ്റഡ് സൈറ്റ്-നിർദ്ദിഷ്ട കീടനാശിനി പ്രയോഗം',
        'app_subtitle': 'കൃത്യമായ സസ്യ രോഗനിർണ്ണയ പ്ലാറ്റ്ഫോം',
        'nav_home': 'ഹോം',
        'nav_diagnostics': 'സസ്യ രോഗനിർണ്ണയം',
        'nav_analytics': 'ഫീൽഡ് അനലിറ്റിക്സ്',
        'title_foliage_capture': '2. ഇല ചിത്രം പകർത്തൽ (തത്സമയ ക്യാമറ)',
        'tab_upload_file': 'ചിത്രം അപ്‌ലോഡ് ചെയ്യുക',
        'tab_live_camera': 'തത്സമയ ക്യാമറ (ഫോൺ / വെബ്)',
        'btn_capture_instant': 'തൽക്ഷണം ഫോട്ടോ എടുക്കുക',
        'btn_download_lang_package': 'മലയാളം ഭാഷാ പാക്കേജ് ഡൗൺലോഡ് ചെയ്യുക (.JSON)',
        'btn_dl_lang': 'പാക്കേജ് ഡൗൺലോഡ്',
        'msg_lang_switched': 'മുഴുവൻ പേജും വിജയകരമായി മലയാളത്തിലേക്ക് മാറ്റി.'
    },
    'mr': {
        'app_title': 'स्वयंचलित साइट-विशिष्ट कीटकनाशक वापर',
        'app_subtitle': 'अचूक वनस्पती रोगनिदान व शेती विश्लेषण मंच',
        'nav_home': 'मुख्यपृष्ठ',
        'nav_diagnostics': 'पीक रोग निदान',
        'nav_analytics': 'शेती विश्लेषण',
        'title_foliage_capture': '२. पानांचे छायाचित्र घ्या (थेट कॅमेरा)',
        'tab_upload_file': 'छायाचित्र अपलोड करा',
        'tab_live_camera': 'थेट कॅमेरा (फोन / लॅपटॉप)',
        'btn_capture_instant': 'त्वरित फोटो काढा',
        'btn_download_lang_package': 'मराठी भाषा पॅकेज डाउनलोड करा (.JSON)',
        'btn_dl_lang': 'पॅकेज डाउनलोड',
        'msg_lang_switched': 'संपूर्ण पृष्ठ यशस्वीरित्या मराठीत रूपांतरित केले आहे.'
    },
    'bn': {
        'app_title': 'স্বয়ংক্রিয় স্থান-নির্দিষ্ট কীটনাশক প্রয়োগ',
        'app_subtitle': 'স্মার্ট উদ্ভিদ রোগতত্ত্ব ও কৃষি বিশ্লেষণ প্ল্যাটফর্ম',
        'nav_home': 'হোম',
        'nav_diagnostics': 'উদ্ভিদ রোগ নির্ণয়',
        'nav_analytics': 'মাঠের বিশ্লেষণ',
        'title_foliage_capture': '২. পাতার ছবি তুলুন (লাইভ ক্যামেরা)',
        'tab_upload_file': 'ছবি আপলোড করুন',
        'tab_live_camera': 'লাইভ ক্যামেরা (ফোন / ল্যাপটপ)',
        'btn_capture_instant': 'তাত্ক্ষণিক ছবি তুলুন',
        'btn_download_lang_package': 'বাংলা ভাষা প্যাকেজ ডাউনলোড করুন (.JSON)',
        'btn_dl_lang': 'প্যাকেজ ডাউনলোড',
        'msg_lang_switched': 'সম্পূর্ণ পৃষ্ঠাটি সফলভাবে বাংলায় রূপান্তরিত হয়েছে।'
    },
    'es': {
        'app_title': 'Aplicación Automatizada de Pesticidas Específica del Sitio',
        'app_subtitle': 'Plataforma Inteligente de Patología Vegetal',
        'nav_home': 'Inicio',
        'nav_about': 'Acerca de',
        'nav_services': 'Servicios',
        'nav_features': 'Características',
        'nav_contact': 'Contacto',
        'nav_login_reg': 'Iniciar Sesión / Registro',
        'nav_diagnostics': 'Diagnóstico de Plantas',
        'nav_analytics': 'Analítica de Campo',
        'title_foliage_capture': '2. Captura de Imagen Foliar (Cámara en Vivo)',
        'tab_upload_file': 'Subir Imagen',
        'tab_live_camera': 'Cámara en Vivo (Teléfono / Laptop)',
        'btn_capture_instant': 'Tomar Foto Instantáneamente',
        'btn_flip_camera': 'Girar Cámara',
        'btn_retake': 'Tomar de Nuevo',
        'btn_download_lang_package': 'Descargar Paquete de Idioma Español (.JSON)',
        'btn_dl_lang': 'Descargar Paquete',
        'msg_lang_switched': 'Toda la página ha sido traducida al español exitosamente.'
    }
}

def generate_language_package(lang_code):
    """
    Constructs a complete language package JSON structure for export or client-side consumption.
    """
    code = lang_code.lower() if lang_code else 'en'
    meta = LANGUAGE_META.get(code, {'name': code.upper(), 'native': code.upper(), 'flag': '🌐'})
    
    # Merge with English defaults for any missing keys
    en_dict = BASE_TRANSLATIONS['en']
    lang_dict = BASE_TRANSLATIONS.get(code, {})
    merged_dict = dict(en_dict)
    merged_dict.update(lang_dict)
    
    package = {
        "package_info": {
            "application": "Automated Site-Specific Pesticide Application",
            "language_code": code,
            "language_name": meta['name'],
            "native_name": meta['native'],
            "flag": meta['flag'],
            "version": "2.4.0",
            "format": "ASSPA_I18N_BUNDLE_V2",
            "total_keys": len(merged_dict)
        },
        "dictionary": merged_dict,
        "agronomic_terms": {
            "crops": ["Tomato", "Potato", "Apple", "Grape", "Rice", "Wheat", "Cotton", "Sugarcane", "Banana"],
            "pathogens": ["Fungal", "Bacterial", "Viral", "Pest Defect", "Healthy Specimen"],
            "severity_levels": ["Mild (1-15%)", "Moderate (15-40%)", "Severe (>40%)", "Healthy (Optimal Vigor)"]
        }
    }
    return package
