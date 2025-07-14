#!/usr/bin/env python3
"""
AnsFlow 告警处理 Webhook 服务
接收 Prometheus AlertManager 的告警通知并进行处理
"""

import json
import time
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AnsFlow Alert Webhook Service",
    description="处理 Prometheus AlertManager 告警通知",
    version="1.0.0"
)

# 告警历史存储（生产环境应使用数据库）
alert_history: List[Dict[str, Any]] = []
alert_stats = {
    "total_alerts": 0,
    "critical_alerts": 0,
    "warning_alerts": 0,
    "resolved_alerts": 0,
    "services": {}
}


class AlertProcessor:
    """告警处理器"""
    
    def __init__(self):
        self.notification_channels = {
            "email": self._send_email_notification,
            "slack": self._send_slack_notification,
            "webhook": self._send_webhook_notification,
        }
    
    async def process_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理单个告警"""
        try:
            # 提取告警信息
            alert_info = {
                "fingerprint": alert_data.get("fingerprint", ""),
                "status": alert_data.get("status", ""),
                "labels": alert_data.get("labels", {}),
                "annotations": alert_data.get("annotations", {}),
                "starts_at": alert_data.get("startsAt", ""),
                "ends_at": alert_data.get("endsAt", ""),
                "generator_url": alert_data.get("generatorURL", ""),
                "processed_at": datetime.utcnow().isoformat()
            }
            
            # 判断告警级别
            severity = alert_info["labels"].get("severity", "unknown")
            service = alert_info["labels"].get("service", "unknown")
            alertname = alert_info["labels"].get("alertname", "unknown")
            
            # 更新统计信息
            self._update_stats(severity, service, alert_info["status"])
            
            # 记录告警历史
            alert_history.append(alert_info)
            
            # 限制历史记录数量
            if len(alert_history) > 1000:
                alert_history[:] = alert_history[-500:]
            
            # 根据告警级别进行不同处理
            if severity == "critical":
                await self._handle_critical_alert(alert_info)
            elif severity == "warning":
                await self._handle_warning_alert(alert_info)
            else:
                await self._handle_info_alert(alert_info)
            
            logger.info(f"Processed alert: {alertname} ({severity}) for service {service}")
            
            return {
                "status": "processed",
                "alert": alertname,
                "severity": severity,
                "service": service,
                "action_taken": "notification_sent"
            }
            
        except Exception as e:
            logger.error(f"Failed to process alert: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _update_stats(self, severity: str, service: str, status: str):
        """更新告警统计"""
        alert_stats["total_alerts"] += 1
        
        if status == "resolved":
            alert_stats["resolved_alerts"] += 1
        elif severity == "critical":
            alert_stats["critical_alerts"] += 1
        elif severity == "warning":
            alert_stats["warning_alerts"] += 1
        
        if service not in alert_stats["services"]:
            alert_stats["services"][service] = {
                "total": 0,
                "critical": 0,
                "warning": 0,
                "resolved": 0
            }
        
        alert_stats["services"][service]["total"] += 1
        if status == "resolved":
            alert_stats["services"][service]["resolved"] += 1
        elif severity == "critical":
            alert_stats["services"][service]["critical"] += 1
        elif severity == "warning":
            alert_stats["services"][service]["warning"] += 1
    
    async def _handle_critical_alert(self, alert_info: Dict[str, Any]):
        """处理严重告警"""
        logger.critical(f"CRITICAL ALERT: {alert_info['labels'].get('alertname')} - {alert_info['annotations'].get('summary')}")
        
        # 发送紧急通知
        await self._send_notification(
            channel="email",
            alert_info=alert_info,
            priority="high"
        )
        
        # 可以添加自动化响应逻辑
        # 例如：自动重启服务、扩容等
    
    async def _handle_warning_alert(self, alert_info: Dict[str, Any]):
        """处理警告告警"""
        logger.warning(f"WARNING ALERT: {alert_info['labels'].get('alertname')} - {alert_info['annotations'].get('summary')}")
        
        # 发送通知
        await self._send_notification(
            channel="email",
            alert_info=alert_info,
            priority="medium"
        )
    
    async def _handle_info_alert(self, alert_info: Dict[str, Any]):
        """处理信息告警"""
        logger.info(f"INFO ALERT: {alert_info['labels'].get('alertname')} - {alert_info['annotations'].get('summary')}")
        
        # 记录日志即可，不发送通知
    
    async def _send_notification(self, channel: str, alert_info: Dict[str, Any], priority: str = "low"):
        """发送通知"""
        if channel in self.notification_channels:
            try:
                await self.notification_channels[channel](alert_info, priority)
            except Exception as e:
                logger.error(f"Failed to send {channel} notification: {e}")
    
    async def _send_email_notification(self, alert_info: Dict[str, Any], priority: str):
        """发送邮件通知（模拟）"""
        # 生产环境中实现真实的邮件发送
        logger.info(f"EMAIL NOTIFICATION ({priority}): {alert_info['labels'].get('alertname')}")
    
    async def _send_slack_notification(self, alert_info: Dict[str, Any], priority: str):
        """发送 Slack 通知（模拟）"""
        # 生产环境中实现真实的 Slack 通知
        logger.info(f"SLACK NOTIFICATION ({priority}): {alert_info['labels'].get('alertname')}")
    
    async def _send_webhook_notification(self, alert_info: Dict[str, Any], priority: str):
        """发送 Webhook 通知（模拟）"""
        # 生产环境中实现真实的 Webhook 调用
        logger.info(f"WEBHOOK NOTIFICATION ({priority}): {alert_info['labels'].get('alertname')}")


# 全局告警处理器
alert_processor = AlertProcessor()


@app.post("/alerts")
async def receive_alerts(request: Request):
    """接收 AlertManager 告警"""
    try:
        # 解析请求体
        payload = await request.json()
        
        logger.info(f"Received alerts payload with {len(payload.get('alerts', []))} alerts")
        
        # 处理每个告警
        results = []
        for alert in payload.get("alerts", []):
            result = await alert_processor.process_alert(alert)
            results.append(result)
        
        return JSONResponse({
            "status": "success",
            "message": f"Processed {len(results)} alerts",
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to process alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/alerts/{service}")
async def receive_service_alerts(service: str, request: Request):
    """接收特定服务的告警"""
    try:
        payload = await request.json()
        
        logger.info(f"Received {service} alerts: {len(payload.get('alerts', []))} alerts")
        
        # 为特定服务添加额外处理逻辑
        results = []
        for alert in payload.get("alerts", []):
            # 添加服务标签
            alert.setdefault("labels", {})["service"] = service
            
            result = await alert_processor.process_alert(alert)
            results.append(result)
        
        return JSONResponse({
            "status": "success",
            "service": service,
            "message": f"Processed {len(results)} {service} alerts",
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Failed to process {service} alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/alerts/history")
async def get_alert_history(limit: int = 50):
    """获取告警历史"""
    return JSONResponse({
        "total_alerts": len(alert_history),
        "alerts": alert_history[-limit:],
        "timestamp": datetime.utcnow().isoformat()
    })


@app.get("/alerts/stats")
async def get_alert_stats():
    """获取告警统计"""
    return JSONResponse({
        "stats": alert_stats,
        "timestamp": datetime.utcnow().isoformat()
    })


@app.get("/health")
async def health_check():
    """健康检查"""
    return JSONResponse({
        "status": "healthy",
        "service": "AnsFlow Alert Webhook",
        "uptime": time.time(),
        "alerts_processed": alert_stats["total_alerts"],
        "timestamp": datetime.utcnow().isoformat()
    })


@app.get("/")
async def root():
    """根路径"""
    return JSONResponse({
        "service": "AnsFlow Alert Webhook Service",
        "version": "1.0.0",
        "endpoints": {
            "alerts": "/alerts",
            "service_alerts": "/alerts/{service}",
            "history": "/alerts/history",
            "stats": "/alerts/stats",
            "health": "/health"
        },
        "timestamp": datetime.utcnow().isoformat()
    })


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=5001,
        log_level="info"
    )
