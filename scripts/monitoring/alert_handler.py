#!/usr/bin/env python3
"""
AnsFlow 告警处理 Webhook 服务
接收来自 AlertManager 的告警通知并处理
"""

from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import logging
import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import uvicorn

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="AnsFlow Alert Handler", version="1.0.0")

# 告警数据模型
class Alert(BaseModel):
    status: str
    labels: Dict[str, str]
    annotations: Dict[str, str]
    startsAt: str
    endsAt: Optional[str] = None
    generatorURL: str
    fingerprint: str

class AlertManagerWebhook(BaseModel):
    receiver: str
    status: str
    alerts: List[Alert]
    groupLabels: Dict[str, str]
    commonLabels: Dict[str, str]
    commonAnnotations: Dict[str, str]
    externalURL: str
    version: str
    groupKey: str
    truncatedAlerts: int = 0

# 告警处理器类
class AlertHandler:
    def __init__(self):
        self.alert_history = []
        self.alert_stats = {
            "total_alerts": 0,
            "critical_alerts": 0,
            "warning_alerts": 0,
            "resolved_alerts": 0
        }
        
    async def process_alerts(self, webhook_data: AlertManagerWebhook):
        """处理告警数据"""
        logger.info(f"Received {len(webhook_data.alerts)} alerts from {webhook_data.receiver}")
        
        for alert in webhook_data.alerts:
            await self.handle_single_alert(alert, webhook_data)
            
    async def handle_single_alert(self, alert: Alert, webhook_data: AlertManagerWebhook):
        """处理单个告警"""
        # 更新统计
        self.alert_stats["total_alerts"] += 1
        
        severity = alert.labels.get("severity", "unknown")
        service = alert.labels.get("service", "unknown")
        alertname = alert.labels.get("alertname", "unknown")
        
        if alert.status == "resolved":
            self.alert_stats["resolved_alerts"] += 1
            logger.info(f"🟢 Alert RESOLVED: {alertname} for {service}")
        else:
            if severity == "critical":
                self.alert_stats["critical_alerts"] += 1
                logger.error(f"🔴 CRITICAL Alert: {alertname} for {service}")
                await self.handle_critical_alert(alert)
            elif severity == "warning":
                self.alert_stats["warning_alerts"] += 1
                logger.warning(f"🟡 WARNING Alert: {alertname} for {service}")
                await self.handle_warning_alert(alert)
        
        # 记录告警历史
        alert_record = {
            "timestamp": datetime.now().isoformat(),
            "alert_name": alertname,
            "service": service,
            "severity": severity,
            "status": alert.status,
            "description": alert.annotations.get("description", ""),
            "summary": alert.annotations.get("summary", ""),
            "labels": alert.labels
        }
        
        self.alert_history.append(alert_record)
        
        # 限制历史记录数量
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-500:]
    
    async def handle_critical_alert(self, alert: Alert):
        """处理严重告警"""
        # 严重告警需要立即处理
        logger.critical(f"CRITICAL ALERT TRIGGERED: {alert.labels.get('alertname')}")
        
        # 可以在这里添加自动化恢复逻辑
        service = alert.labels.get("service")
        if service == "ansflow-fastapi":
            await self.attempt_service_recovery("fastapi")
        elif service == "ansflow-django":
            await self.attempt_service_recovery("django")
        
        # 发送紧急通知
        await self.send_urgent_notification(alert)
    
    async def handle_warning_alert(self, alert: Alert):
        """处理警告告警"""
        logger.warning(f"Warning alert: {alert.labels.get('alertname')}")
        
        # 警告级别的告警记录和通知
        await self.send_warning_notification(alert)
    
    async def attempt_service_recovery(self, service: str):
        """尝试服务自动恢复"""
        logger.info(f"Attempting automatic recovery for {service} service")
        
        # 这里可以添加实际的恢复逻辑
        # 例如：重启服务、清理资源、重置连接等
        
        # 模拟恢复操作
        await asyncio.sleep(1)
        logger.info(f"Recovery attempt completed for {service}")
    
    async def send_urgent_notification(self, alert: Alert):
        """发送紧急通知"""
        # 这里可以集成实际的通知服务
        # 例如：邮件、Slack、钉钉、企业微信等
        
        message = f"""
🚨 URGENT ALERT 🚨
Alert: {alert.labels.get('alertname')}
Service: {alert.labels.get('service')}
Severity: {alert.labels.get('severity')}
Description: {alert.annotations.get('description')}
Time: {alert.startsAt}
"""
        logger.critical(f"URGENT NOTIFICATION: {message}")
    
    async def send_warning_notification(self, alert: Alert):
        """发送警告通知"""
        message = f"""
⚠️ Warning Alert
Alert: {alert.labels.get('alertname')}
Service: {alert.labels.get('service')}
Description: {alert.annotations.get('description')}
Time: {alert.startsAt}
"""
        logger.warning(f"WARNING NOTIFICATION: {message}")

# 全局告警处理器
alert_handler = AlertHandler()

@app.post("/alerts")
async def receive_alerts(webhook_data: AlertManagerWebhook):
    """接收 AlertManager 的 Webhook 通知"""
    try:
        await alert_handler.process_alerts(webhook_data)
        return {"status": "success", "message": f"Processed {len(webhook_data.alerts)} alerts"}
    except Exception as e:
        logger.error(f"Error processing alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/alerts/{service}")
async def receive_service_alerts(service: str, webhook_data: AlertManagerWebhook):
    """接收特定服务的告警"""
    logger.info(f"Received alerts for service: {service}")
    await alert_handler.process_alerts(webhook_data)
    return {"status": "success", "service": service, "alerts_count": len(webhook_data.alerts)}

@app.get("/alerts/history")
async def get_alert_history(limit: int = 100):
    """获取告警历史"""
    return {
        "alerts": alert_handler.alert_history[-limit:],
        "total_count": len(alert_handler.alert_history)
    }

@app.get("/alerts/stats")
async def get_alert_stats():
    """获取告警统计"""
    return {
        "stats": alert_handler.alert_stats,
        "recent_alerts_count": len(alert_handler.alert_history),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "AnsFlow Alert Handler",
        "uptime": datetime.now().isoformat(),
        "alerts_processed": alert_handler.alert_stats["total_alerts"]
    }

@app.get("/")
async def root():
    """根端点"""
    return {
        "service": "AnsFlow Alert Handler",
        "version": "1.0.0",
        "endpoints": [
            "/alerts",
            "/alerts/{service}",
            "/alerts/history",
            "/alerts/stats",
            "/health"
        ]
    }

if __name__ == "__main__":
    logger.info("Starting AnsFlow Alert Handler service...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5001,
        log_level="info"
    )
