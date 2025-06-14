"""
Tracking Configuration Model
Handles Meta Pixel, GA4, GTM, and Microsoft Clarity tracking codes
"""

from src.models.user import db
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

class TrackingConfig(db.Model):
    __tablename__ = 'tracking_configs'
    
    config_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    domain_id = Column(Integer, ForeignKey('domains.domain_id'), nullable=True)
    
    # Tracking Platform Types
    platform = Column(String(50), nullable=False)  # 'meta_pixel', 'ga4', 'gtm', 'clarity'
    
    # Configuration Data
    tracking_id = Column(String(255), nullable=False)  # Pixel ID, GA4 ID, GTM ID, Clarity ID
    name = Column(String(255), nullable=False)  # User-friendly name
    
    # Additional Settings (JSON-like text field)
    settings = Column(Text, nullable=True)  # JSON string for additional settings
    
    # Status and Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", backref="tracking_configs")
    domain = relationship("Domain", backref="tracking_configs")
    
    def to_dict(self):
        return {
            'config_id': self.config_id,
            'user_id': self.user_id,
            'domain_id': self.domain_id,
            'platform': self.platform,
            'tracking_id': self.tracking_id,
            'name': self.name,
            'settings': self.settings,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_platform_info():
        """Get information about supported tracking platforms"""
        return {
            'meta_pixel': {
                'name': 'Meta Pixel (Facebook)',
                'description': 'Track conversions, optimize ads, and build audiences for Facebook and Instagram campaigns',
                'id_format': 'Pixel ID (e.g., 1234567890123456)',
                'setup_url': 'https://business.facebook.com/events_manager',
                'docs_url': 'https://developers.facebook.com/docs/facebook-pixel'
            },
            'ga4': {
                'name': 'Google Analytics 4',
                'description': 'Advanced analytics and insights for your website traffic and user behavior',
                'id_format': 'Measurement ID (e.g., G-XXXXXXXXXX)',
                'setup_url': 'https://analytics.google.com/',
                'docs_url': 'https://developers.google.com/analytics/devguides/collection/ga4'
            },
            'gtm': {
                'name': 'Google Tag Manager',
                'description': 'Manage all your tracking tags from one central location without code changes',
                'id_format': 'Container ID (e.g., GTM-XXXXXXX)',
                'setup_url': 'https://tagmanager.google.com/',
                'docs_url': 'https://developers.google.com/tag-manager'
            },
            'clarity': {
                'name': 'Microsoft Clarity',
                'description': 'Free heatmaps and session recordings to understand user behavior',
                'id_format': 'Project ID (e.g., abcdefghij)',
                'setup_url': 'https://clarity.microsoft.com/',
                'docs_url': 'https://docs.microsoft.com/en-us/clarity/'
            }
        }
    
    @staticmethod
    def generate_tracking_code(platform, tracking_id, settings=None):
        """Generate the tracking code for different platforms"""
        
        if platform == 'meta_pixel':
            return f"""
<!-- Meta Pixel Code -->
<script>
!function(f,b,e,v,n,t,s)
{{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)}};
if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];
s.parentNode.insertBefore(t,s)}}(window, document,'script',
'https://connect.facebook.net/en_US/fbevents.js');
fbq('init', '{tracking_id}');
fbq('track', 'PageView');
</script>
<noscript><img height="1" width="1" style="display:none"
src="https://www.facebook.com/tr?id={tracking_id}&ev=PageView&noscript=1"
/></noscript>
<!-- End Meta Pixel Code -->
"""
        
        elif platform == 'ga4':
            return f"""
<!-- Google Analytics 4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id={tracking_id}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{tracking_id}');
</script>
<!-- End Google Analytics 4 -->
"""
        
        elif platform == 'gtm':
            return f"""
<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
}})(window,document,'script','dataLayer','{tracking_id}');</script>
<!-- End Google Tag Manager -->

<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={tracking_id}"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->
"""
        
        elif platform == 'clarity':
            return f"""
<!-- Microsoft Clarity -->
<script type="text/javascript">
    (function(c,l,a,r,i,t,y){{
        c[a]=c[a]||function(){{(c[a].q=c[a].q||[]).push(arguments)}};
        t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
        y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
    }})(window, document, "clarity", "script", "{tracking_id}");
</script>
<!-- End Microsoft Clarity -->
"""
        
        else:
            return f"<!-- Unknown tracking platform: {platform} -->"

