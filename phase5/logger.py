"""
System Logger for Restaurant Recommendation System

Implements prompt/version logging and error tracking
for observability and debugging.
"""

import logging
import json
import time
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime

# Import from previous phases
try:
    from ..phase3.prompt_builder import UserPreferences, RestaurantCandidate
    from ..phase3.output_validator import RecommendationResponse, RestaurantRanking
except ImportError:
    from phase3.prompt_builder import UserPreferences, RestaurantCandidate
    from phase3.output_validator import RecommendationResponse, RestaurantRanking


@dataclass
class LogEntry:
    """Represents a single log entry"""
    timestamp: str
    level: str
    component: str
    message: str
    data: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None


@dataclass
class PromptLog:
    """Represents a prompt logging entry"""
    timestamp: str
    prompt_id: str
    prompt_version: str
    llm_provider: str
    model: str
    prompt_text: str
    token_count: int
    response_time_ms: int
    success: bool
    error_message: Optional[str] = None


class SystemLogger:
    """Centralized logging system for all components"""
    
    def __init__(self, log_level: str = "INFO", log_file: Optional[str] = None):
        self.log_level = log_level
        self.log_file = log_file or "phase5_system.log"
        self.prompt_logs: List[PromptLog] = []
        self.request_counter = 0
        
        # Setup logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Setup file handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setFormatter(formatter)
        
        # Setup console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.log_level.upper()))
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        # Create component-specific loggers
        self.component_loggers = {
            'retrieval': logging.getLogger('retrieval'),
            'llm': logging.getLogger('llm'),
            'validation': logging.getLogger('validation'),
            'api': logging.getLogger('api'),
            'ui': logging.getLogger('ui'),
            'evaluation': logging.getLogger('evaluation')
        }
    
    def log_component(self, component: str, level: str, message: str, 
                    data: Optional[Dict[str, Any]] = None, 
                    request_id: Optional[str] = None,
                    user_id: Optional[str] = None):
        """Log a component-specific message"""
        
        if component in self.component_loggers:
            logger = self.component_loggers[component]
            log_level = getattr(logging, level.upper())
            
            if logger.isEnabledFor(log_level):
                # Create log entry
                entry = LogEntry(
                    timestamp=datetime.now().isoformat(),
                    level=level,
                    component=component,
                    message=message,
                    data=data,
                    request_id=request_id,
                    user_id=user_id
                )
                
                # Log to file
                logger.log(log_level, f"{message} | Data: {json.dumps(data) if data else 'None'}")
                
                # Log structured data separately for analysis
                if data:
                    self._log_structured_data(entry)
    
    def _log_structured_data(self, entry: LogEntry):
        """Log structured data for analysis"""
        
        try:
            # Create structured log file
            structured_log_file = self.log_file.replace('.log', '_structured.jsonl')
            
            with open(structured_log_file, 'a') as f:
                structured_entry = {
                    'timestamp': entry.timestamp,
                    'level': entry.level,
                    'component': entry.component,
                    'message': entry.message,
                    'data': entry.data,
                    'request_id': entry.request_id,
                    'user_id': entry.user_id
                }
                f.write(json.dumps(structured_entry) + '\n')
        except Exception as e:
            print(f"Failed to write structured log: {e}")
    
    def log_prompt(self, prompt_id: str, prompt_text: str, prompt_version: str,
                 llm_provider: str, model: str, token_count: int,
                 response_time_ms: int, success: bool,
                 error_message: Optional[str] = None,
                 preferences: Optional[UserPreferences] = None,
                 candidates: Optional[List[RestaurantCandidate]] = None):
        """Log prompt execution details"""
        
        prompt_log = PromptLog(
            timestamp=datetime.now().isoformat(),
            prompt_id=prompt_id,
            prompt_version=prompt_version,
            llm_provider=llm_provider,
            model=model,
            prompt_text=prompt_text,
            token_count=token_count,
            response_time_ms=response_time_ms,
            success=success,
            error_message=error_message
        )
        
        self.prompt_logs.append(prompt_log)
        
        # Log to component logger
        log_data = {
            'prompt_id': prompt_id,
            'prompt_version': prompt_version,
            'llm_provider': llm_provider,
            'model': model,
            'token_count': token_count,
            'response_time_ms': response_time_ms,
            'success': success,
            'error_message': error_message
        }
        
        if preferences:
            log_data['preferences'] = asdict(preferences)
        
        if candidates:
            log_data['candidates_count'] = len(candidates)
            log_data['candidates'] = [asdict(c) for c in candidates[:3]]  # Log first 3
        
        status = "SUCCESS" if success else "FAILED"
        self.log_component(
            component='llm',
            level='INFO',
            message=f"Prompt {status} - {prompt_id}",
            data=log_data
        )
    
    def log_retrieval_step(self, step: str, preferences: UserPreferences,
                         candidates: List[RestaurantCandidate], 
                         filtered_candidates: List[RestaurantCandidate],
                         execution_time_ms: int):
        """Log retrieval pipeline steps"""
        
        self.log_component(
            component='retrieval',
            level='INFO',
            message=f"Retrieval step: {step}",
            data={
                'step': step,
                'preferences': asdict(preferences),
                'input_candidates_count': len(candidates),
                'filtered_candidates_count': len(filtered_candidates),
                'execution_time_ms': execution_time_ms
            }
        )
    
    def log_validation_result(self, validation_type: str, input_data: Any,
                           result: bool, error_message: Optional[str] = None):
        """Log validation results"""
        
        self.log_component(
            component='validation',
            level='INFO' if result else 'ERROR',
            message=f"Validation {validation_type}: {'PASS' if result else 'FAIL'}",
            data={
                'validation_type': validation_type,
                'input_data': str(input_data)[:100],  # Truncate for readability
                'result': result,
                'error_message': error_message
            }
        )
    
    def log_api_request(self, method: str, endpoint: str, request_data: Any,
                     response_status: int, response_time_ms: int,
                     user_id: Optional[str] = None):
        """Log API request details"""
        
        self.request_counter += 1
        request_id = f"req_{self.request_counter:06d}"
        
        self.log_component(
            component='api',
            level='INFO',
            message=f"API {method} {endpoint}: {response_status}",
            data={
                'request_id': request_id,
                'method': method,
                'endpoint': endpoint,
                'request_data': str(request_data)[:200],  # Truncate
                'response_status': response_status,
                'response_time_ms': response_time_ms,
                'user_id': user_id
            },
            request_id=request_id,
            user_id=user_id
        )
        
        return request_id
    
    def log_ui_interaction(self, action: str, component: str, 
                        data: Optional[Dict[str, Any]] = None,
                        user_id: Optional[str] = None):
        """Log UI interactions"""
        
        self.log_component(
            component='ui',
            level='INFO',
            message=f"UI {action} in {component}",
            data=data,
            user_id=user_id
        )
    
    def log_evaluation_result(self, test_name: str, test_type: str,
                           result: bool, score: float,
                           details: Optional[Dict[str, Any]] = None):
        """Log evaluation results"""
        
        self.log_component(
            component='evaluation',
            level='INFO',
            message=f"Evaluation {test_name} ({test_type}): {'PASS' if result else 'FAIL'}",
            data={
                'test_name': test_name,
                'test_type': test_type,
                'result': result,
                'score': score,
                'details': details
            }
        )
    
    def log_error(self, component: str, error_type: str, error_message: str,
                  context: Optional[Dict[str, Any]] = None,
                  severity: str = "ERROR"):
        """Log error with context"""
        
        self.log_component(
            component=component,
            level=severity,
            message=f"Error ({error_type}): {error_message}",
            data={
                'error_type': error_type,
                'context': context
            }
        )
    
    def log_performance_metrics(self, component: str, metrics: Dict[str, Any]):
        """Log performance metrics"""
        
        self.log_component(
            component=component,
            level='INFO',
            message=f"Performance metrics for {component}",
            data=metrics
        )
    
    def get_prompt_analytics(self) -> Dict[str, Any]:
        """Get analytics from prompt logs"""
        
        if not self.prompt_logs:
            return {}
        
        total_prompts = len(self.prompt_logs)
        successful_prompts = sum(1 for log in self.prompt_logs if log.success)
        failed_prompts = total_prompts - successful_prompts
        
        # Calculate average response time
        response_times = [log.response_time_ms for log in self.prompt_logs if log.success]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Calculate total tokens
        total_tokens = sum(log.token_count for log in self.prompt_logs)
        
        # Provider breakdown
        provider_counts = {}
        for log in self.prompt_logs:
            provider = log.llm_provider
            provider_counts[provider] = provider_counts.get(provider, 0) + 1
        
        return {
            'total_prompts': total_prompts,
            'successful_prompts': successful_prompts,
            'failed_prompts': failed_prompts,
            'success_rate': successful_prompts / total_prompts if total_prompts > 0 else 0,
            'avg_response_time_ms': avg_response_time,
            'total_tokens': total_tokens,
            'provider_breakdown': provider_counts,
            'prompt_version_distribution': self._get_prompt_version_distribution()
        }
    
    def _get_prompt_version_distribution(self) -> Dict[str, int]:
        """Get distribution of prompt versions"""
        
        version_counts = {}
        for log in self.prompt_logs:
            version = log.prompt_version
            version_counts[version] = version_counts.get(version, 0) + 1
        
        return version_counts
    
    def export_logs(self, output_dir: str):
        """Export logs to files for analysis"""
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Export prompt logs
        if self.prompt_logs:
            prompt_file = os.path.join(output_dir, 'prompt_logs.json')
            with open(prompt_file, 'w') as f:
                json.dump([asdict(log) for log in self.prompt_logs], f, indent=2)
            
            analytics = self.get_prompt_analytics()
            analytics_file = os.path.join(output_dir, 'prompt_analytics.json')
            with open(analytics_file, 'w') as f:
                json.dump(analytics, f, indent=2)
        
        print(f"📁 Logs exported to: {output_dir}")
    
    def get_recent_errors(self, limit: int = 10) -> List[LogEntry]:
        """Get recent error logs"""
        
        try:
            recent_errors = []
            structured_log_file = self.log_file.replace('.log', '_structured.jsonl')
            
            if os.path.exists(structured_log_file):
                with open(structured_log_file, 'r') as f:
                    lines = f.readlines()[-limit:]  # Get last 'limit' lines
                    
                    for line in lines:
                        try:
                            entry = json.loads(line.strip())
                            if entry.get('level') in ['ERROR', 'CRITICAL']:
                                recent_errors.append(LogEntry(**entry))
                        except json.JSONDecodeError:
                            continue
            
            return recent_errors
        except Exception as e:
            print(f"Error reading recent errors: {e}")
            return []
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get system health status"""
        
        analytics = self.get_prompt_analytics()
        recent_errors = self.get_recent_errors(5)
        
        return {
            'status': 'healthy' if len(recent_errors) == 0 else 'degraded',
            'recent_errors_count': len(recent_errors),
            'prompt_success_rate': analytics.get('success_rate', 0),
            'avg_response_time_ms': analytics.get('avg_response_time_ms', 0),
            'total_prompts': analytics.get('total_prompts', 0),
            'log_file_size': os.path.getsize(self.log_file) if os.path.exists(self.log_file) else 0
        }
