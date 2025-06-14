import time
import json
import threading
from datetime import datetime
from queue import Queue
import logging

from src.models.user import db
from src.models.analysis_report import AnalysisReport
from src.models.domain import Domain
from src.models.llm_config import LLMConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnalysisWorker:
    """Background worker for processing analysis tasks"""
    
    def __init__(self, app):
        self.app = app
        self.task_queue = Queue()
        self.is_running = False
        self.worker_thread = None
    
    def start(self):
        """Start the background worker"""
        if not self.is_running:
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            logger.info("Analysis worker started")
    
    def stop(self):
        """Stop the background worker"""
        self.is_running = False
        if self.worker_thread:
            self.worker_thread.join()
        logger.info("Analysis worker stopped")
    
    def queue_analysis(self, report_id):
        """Queue an analysis task"""
        self.task_queue.put({
            'type': 'analysis',
            'report_id': report_id,
            'queued_at': datetime.utcnow().isoformat()
        })
        logger.info(f"Queued analysis task for report {report_id}")
    
    def _worker_loop(self):
        """Main worker loop"""
        logger.info("Worker loop started")
        
        while self.is_running:
            try:
                # Get task from queue (blocking with timeout)
                try:
                    task = self.task_queue.get(timeout=1.0)
                except:
                    continue
                
                if task['type'] == 'analysis':
                    self._process_analysis_task(task)
                
                self.task_queue.task_done()
                
            except Exception as e:
                logger.error(f"Worker error: {str(e)}")
                time.sleep(1)
    
    def _process_analysis_task(self, task):
        """Process an analysis task"""
        report_id = task['report_id']
        
        with self.app.app_context():
            try:
                logger.info(f"Processing analysis for report {report_id}")
                
                # Get the report
                report = AnalysisReport.query.filter_by(report_id=report_id).first()
                if not report:
                    logger.error(f"Report {report_id} not found")
                    return
                
                if report.status != 'pending':
                    logger.warning(f"Report {report_id} is not pending (status: {report.status})")
                    return
                
                # Get the domain
                domain = Domain.query.get(report.domain_id)
                if not domain:
                    logger.error(f"Domain not found for report {report_id}")
                    return
                
                # Update status to processing
                report.status = 'processing'
                db.session.commit()
                
                start_time = time.time()
                
                # Perform SEO analysis
                seo_data = self._perform_seo_analysis(domain.url)
                report.seo_score = seo_data['score']
                report.set_seo_analysis(seo_data)
                
                # Perform AEO analysis using LLM
                llm_config = LLMConfig.get_active_config()
                if llm_config and llm_config.is_available():
                    aeo_data = self._perform_aeo_analysis(domain.url, llm_config)
                    report.aeo_score = aeo_data['score']
                    report.set_aeo_analysis(aeo_data)
                    
                    # Combine recommendations
                    all_recommendations = seo_data.get('recommendations', []) + aeo_data.get('recommendations', [])
                    report.set_recommendations(all_recommendations)
                else:
                    # No LLM config available, use default AEO score
                    report.aeo_score = 60.0
                    report.set_aeo_analysis({'error': 'No LLM configuration available'})
                    report.set_recommendations(seo_data.get('recommendations', []))
                
                # Calculate overall score
                report.calculate_overall_score()
                
                # Generate LLMs.txt file
                llms_data = {
                    'description': f'Website analysis for {domain.url}',
                    'seo_score': report.seo_score,
                    'aeo_score': report.aeo_score,
                    'topics': ['SEO', 'AEO', 'Website Optimization'],
                    'contact': 'Available on website'
                }
                report.llms_file_content = self._generate_llms_txt(domain.url, llms_data)
                
                # Generate summary
                report.summary = f"Analysis completed for {domain.url}. SEO Score: {report.seo_score:.1f}, AEO Score: {report.aeo_score:.1f}, Overall Score: {report.overall_score:.1f}"
                
                # Mark as completed
                processing_time = time.time() - start_time
                report.mark_completed(processing_time)
                
                # Update domain scores
                domain.update_scores(report.seo_score, report.aeo_score)
                domain.set_status('active')
                
                db.session.commit()
                
                logger.info(f"Analysis completed for report {report_id} in {processing_time:.2f}s")
                
            except Exception as e:
                logger.error(f"Analysis failed for report {report_id}: {str(e)}")
                
                # Mark as failed
                try:
                    report.mark_failed(str(e))
                    domain.set_status('error')
                    db.session.commit()
                except:
                    pass
    
    def _perform_seo_analysis(self, domain_url):
        """Perform SEO analysis (mock implementation)"""
        # Simulate analysis time
        time.sleep(2)
        
        # Mock SEO analysis results
        seo_data = {
            'score': 75.5,
            'factors': {
                'title_tags': {'score': 85, 'status': 'good'},
                'meta_descriptions': {'score': 70, 'status': 'needs_improvement'},
                'headings': {'score': 80, 'status': 'good'},
                'internal_links': {'score': 65, 'status': 'needs_improvement'},
                'page_speed': {'score': 75, 'status': 'good'},
                'mobile_friendly': {'score': 90, 'status': 'excellent'}
            },
            'recommendations': [
                {
                    'category': 'Meta Descriptions',
                    'priority': 'high',
                    'description': 'Add compelling meta descriptions to improve click-through rates',
                    'impact': 'medium'
                },
                {
                    'category': 'Internal Linking',
                    'priority': 'medium',
                    'description': 'Improve internal link structure for better crawlability',
                    'impact': 'medium'
                }
            ]
        }
        
        return seo_data
    
    def _perform_aeo_analysis(self, domain_url, llm_config):
        """Perform AEO analysis using LLM"""
        try:
            from src.routes.analysis import call_llm_api
            
            prompt = f"""
            Analyze the website {domain_url} for Answer Engine Optimization (AEO). 
            Provide a comprehensive analysis including:
            
            1. AEO Score (0-100)
            2. Content structure analysis
            3. Schema markup assessment
            4. FAQ optimization
            5. Featured snippet potential
            6. Voice search readiness
            7. AI-friendly content formatting
            8. Recommendations for improvement
            
            Return the analysis in JSON format with the following structure:
            {{
                "score": <number>,
                "factors": {{
                    "content_structure": {{"score": <number>, "status": "<status>"}},
                    "schema_markup": {{"score": <number>, "status": "<status>"}},
                    "faq_optimization": {{"score": <number>, "status": "<status>"}},
                    "featured_snippets": {{"score": <number>, "status": "<status>"}},
                    "voice_search": {{"score": <number>, "status": "<status>"}},
                    "ai_formatting": {{"score": <number>, "status": "<status>"}}
                }},
                "recommendations": [
                    {{
                        "category": "<category>",
                        "priority": "<high|medium|low>",
                        "description": "<description>",
                        "impact": "<high|medium|low>"
                    }}
                ]
            }}
            """
            
            content, tokens_used = call_llm_api(prompt, llm_config)
            
            # Record usage
            llm_config.record_usage(tokens_used)
            db.session.commit()
            
            # Parse JSON response
            try:
                aeo_data = json.loads(content)
                return aeo_data
            except json.JSONDecodeError:
                # Fallback if LLM doesn't return valid JSON
                return self._get_default_aeo_data()
        
        except Exception as e:
            logger.error(f"AEO analysis failed: {str(e)}")
            return self._get_default_aeo_data()
    
    def _get_default_aeo_data(self):
        """Get default AEO analysis data"""
        return {
            'score': 70.0,
            'factors': {
                'content_structure': {'score': 75, 'status': 'good'},
                'schema_markup': {'score': 60, 'status': 'needs_improvement'},
                'faq_optimization': {'score': 65, 'status': 'needs_improvement'},
                'featured_snippets': {'score': 70, 'status': 'good'},
                'voice_search': {'score': 75, 'status': 'good'},
                'ai_formatting': {'score': 80, 'status': 'good'}
            },
            'recommendations': [
                {
                    'category': 'Schema Markup',
                    'priority': 'high',
                    'description': 'Implement structured data markup for better AI understanding',
                    'impact': 'high'
                }
            ]
        }
    
    def _generate_llms_txt(self, domain_url, analysis_data):
        """Generate LLMs.txt file content"""
        llms_content = f"""# LLMs.txt for {domain_url}
# Generated by TrafficTuner.site

# Site Information
Site: {domain_url}
Description: {analysis_data.get('description', 'Website optimized for AI search engines')}
Generated: {datetime.utcnow().isoformat()}

# Content Guidelines
- This site provides accurate and up-to-date information
- Content is regularly reviewed and updated
- All claims are backed by reliable sources

# SEO Optimization
SEO Score: {analysis_data.get('seo_score', 'N/A')}
AEO Score: {analysis_data.get('aeo_score', 'N/A')}

# Key Topics
{chr(10).join([f"- {topic}" for topic in analysis_data.get('topics', [])])}

# Contact Information
Contact: {analysis_data.get('contact', 'Available on website')}

# Last Updated
{datetime.utcnow().strftime('%Y-%m-%d')}
"""
        return llms_content

# Global worker instance
analysis_worker = None

def init_worker(app):
    """Initialize the analysis worker"""
    global analysis_worker
    analysis_worker = AnalysisWorker(app)
    analysis_worker.start()
    return analysis_worker

def get_worker():
    """Get the global worker instance"""
    return analysis_worker

