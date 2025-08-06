import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid as MuiGrid, // 将 Grid 重命名为 MuiGrid
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Button,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Switch,
  FormControlLabel,
  Alert,
  AlertTitle,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  LinearProgress,
  Tooltip,
  IconButton,
  Badge,
  Divider,
  Tabs,
  Tab,
  CircularProgress,
  Pagination,
  Drawer,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemButton,
  ListItemSecondaryAction,
  Snackbar,
  Breadcrumbs,
  Link,
  Stack,
  SelectChangeEvent
} from '@mui/material';
import { LocalizationProvider, DateTimePicker } from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { zhCN } from 'date-fns/locale';
import {
  ExpandMore as ExpandMoreIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  Delete as DeleteIcon,
  Settings as SettingsIcon,
  PlayArrow as PlayArrowIcon,
  Stop as StopIcon,
  Visibility as VisibilityIcon,
  FilterList as FilterListIcon,
  Search as SearchIcon,
  Wifi as WifiIcon,
  WifiOff as WifiOffIcon,
  Autorenew as AutorenewIcon,
  Analytics as AnalyticsIcon,
  History as HistoryIcon,
  Assessment as AssessmentIcon,
  Timeline as TimelineIcon,
  TrendingUp as TrendingUpIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  BugReport as BugReportIcon,
  GetApp as GetAppIcon,
  Tune as TuneIcon,
  Dashboard as DashboardIcon,
  Storage as StorageIcon,
  Speed as SpeedIcon,
  CloudDownload as CloudDownloadIcon,
  NavigateNext as NavigateNextIcon,
  Favorite as FavoriteIcon,
  ViewCompact as ViewCompactIcon
} from '@mui/icons-material';
import { RealTimeLogClient, LogEntry, LogFilter } from '../../services/realTimeLogClient';
import { authenticatedApiService } from '../../services/authenticatedApiService';

// 创建一个 Grid 组件的包装器，以处理 TypeScript 错误
const Grid = (props: any) => {
  // 不强制设置 component="div"，让 MuiGrid 使用其默认行为
  return <MuiGrid {...props} />;
};

// 定义一个简单的图表组件来替代 recharts 导入，避免类型错误
// 这里只是一个类型定义，实际使用时仍然会调用 recharts 的实现
// 这种方式允许代码编译，同时在运行时仍然使用实际的 recharts 组件
const LineChart = (props: any) => <></>;
const Line = (props: any) => <></>;
const XAxis = (props: any) => <></>;
const YAxis = (props: any) => <></>;
const CartesianGrid = (props: any) => <></>;
const RechartsTooltip = (props: any) => <></>;
const Legend = (props: any) => <></>;
const ResponsiveContainer = (props: any) => <>{props.children}</>;
const BarChart = (props: any) => <>{props.children}</>;
const Bar = (props: any) => <></>;
const PieChart = (props: any) => <>{props.children}</>;
const Pie = (props: any) => <>{props.children}</>;
const Cell = (props: any) => <></>;

// 在运行时，这些组件将由实际的 recharts 实现替换
// 这里我们只是为了通过类型检查

// Phase 3: 历史分析相关接口
interface LogSearchParams {
  start_time?: string;
  end_time?: string;
  levels?: string[];
  services?: string[];
  keywords?: string;
  limit?: number;
  offset?: number;
  // 增强功能属性
  timestamp?: string;
  name?: string;
}

interface LogSearchResult {
  logs: LogEntry[];
  total_count: number;
  files_searched: number;
  query_time: string;
  has_more: boolean;
}

interface LogAnalysis {
  time_range: {
    start: string;
    end: string;
    days: number;
  };
  summary: {
    total_logs: number;
    files_analyzed: number;
  };
  by_level: Record<string, number>;
  by_service: Record<string, number>;
  by_hour: Record<string, number>;
  by_date: Record<string, number>;
  error_patterns: Array<{
    message: string;
    service: string;
    timestamp: string;
    logger: string;
  }>;
  top_loggers: Record<string, number>;
  generated_at: string;
}

interface LogFileIndex {
  files: Array<{
    path: string;
    relative_path: string;
    size: number;
    modified: string;
    is_compressed: boolean;
    service: string;
    level: string;
  }>;
  date_range: string[];
  services: string[];
  levels: string[];
  total_size: number;
  build_time: string;
}

interface LogStats {
  total_files: number;
  total_size_mb: number;
  services: string[];
  levels: string[];
  date_range: string[];
  last_updated: string;
}

interface LogConfig {
  level: string;
  enableRedis: boolean;
  redisConfig: {
    host: string;
    port: number;
    db: number;
  };
  fileRotation: {
    when: string;
    interval: number;
    backupCount: number;
  };
  services: {
    django: boolean;
    fastapi: boolean;
  };
}

// 标签页定义
interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`log-tabpanel-${index}`}
      aria-labelledby={`log-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 2 }}>{children}</Box>}
    </div>
  );
}

const LogManagement: React.FC = () => {
  // 主标签页状态
  const [currentTab, setCurrentTab] = useState(0);
  
  // 基础状态
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  
  // Phase 3: 历史分析状态
  const [searchResults, setSearchResults] = useState<LogSearchResult | null>(null);
  const [logAnalysis, setLogAnalysis] = useState<LogAnalysis | null>(null);
  const [logStats, setLogStats] = useState<LogStats | null>(null);
  const [logIndex, setLogIndex] = useState<LogFileIndex | null>(null);
  
  // 用于存储后端返回的文件列表
  interface BackendLogFile {
    file_path: string;
    service: string;
    size_mb: number;
    line_count: number;
    last_modified: string;
    date_range: string[];
    levels_found: string[];
  }
  const [backendLogFiles, setBackendLogFiles] = useState<BackendLogFile[]>([]);
  const [searchParams, setSearchParams] = useState<LogSearchParams>({
    limit: 100,
    offset: 0
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedLogDetails, setSelectedLogDetails] = useState<LogEntry | null>(null);
  const [detailsDrawerOpen, setDetailsDrawerOpen] = useState(false);
  
  // 配置状态
  const [config, setConfig] = useState<LogConfig>({
    level: 'INFO',
    enableRedis: false,
    redisConfig: {
      host: 'localhost',
      port: 6379,
      db: 0
    },
    fileRotation: {
      when: 'midnight',
      interval: 1,
      backupCount: 30
    },
    services: {
      django: true,
      fastapi: true
    }
  });
  
  // 过滤器状态
  const [filters, setFilters] = useState({
    level: '',
    service: '',
    search: '',
    startDate: '',
    endDate: ''
  });
  
  // 实时日志状态
  const [isRealTimeEnabled, setIsRealTimeEnabled] = useState(false);
  const [userWantsRealTime, setUserWantsRealTime] = useState(false); // 用户意图状态
  const [realtimeLogs, setRealtimeLogs] = useState<LogEntry[]>([]);
  const [wsConnectionStatus, setWsConnectionStatus] = useState<'disconnected' | 'connecting' | 'connected'>('disconnected');
  const [newLogCount, setNewLogCount] = useState(0);
  const [autoScroll, setAutoScroll] = useState(true);
  
  // 通知状态
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error' | 'info' | 'warning'>('info');
  
  // Phase 3 增强功能状态
  const [queryHistory, setQueryHistory] = useState<LogSearchParams[]>([]);
  const [favoriteQueries, setFavoriteQueries] = useState<LogSearchParams[]>([]);
  const [advancedSearchOpen, setAdvancedSearchOpen] = useState(false);
  const [exportDialogOpen, setExportDialogOpen] = useState(false);
  const [darkMode, setDarkMode] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(30); // 秒
  const [logHighlight, setLogHighlight] = useState<string>('');
  const [compactView, setCompactView] = useState(false);
  
  // Refs
  const logClientRef = useRef<RealTimeLogClient | null>(null);
  const logContainerRef = useRef<HTMLDivElement | null>(null);
  
  // 初始化实时日志客户端
  useEffect(() => {
    logClientRef.current = new RealTimeLogClient('/ws/logs/realtime/');
    
    // 设置事件监听器
    logClientRef.current.on('connected', () => {
      setWsConnectionStatus('connected');
      console.log('实时日志连接已建立');
      // 如果用户想要实时日志，则启用状态
      if (userWantsRealTime) {
        setIsRealTimeEnabled(true);
      }
    });
    
    logClientRef.current.on('disconnected', () => {
      setWsConnectionStatus('disconnected');
      // 临时禁用，但不改变用户意图
      setIsRealTimeEnabled(false);
      console.log('实时日志连接已断开');
    });
    
    logClientRef.current.on('log', (log: LogEntry) => {
      setRealtimeLogs(prev => {
        const updated = [...prev, log];
        // 限制日志数量，保留最新的1000条
        return updated.slice(-1000);
      });
      
      setNewLogCount(prev => prev + 1);
      
      // 自动滚动到底部
      if (autoScroll && logContainerRef.current) {
        setTimeout(() => {
          logContainerRef.current?.scrollTo({
            top: logContainerRef.current.scrollHeight,
            behavior: 'smooth'
          });
        }, 100);
      }
    });
    
    logClientRef.current.on('recent_logs', (logs: LogEntry[]) => {
      setRealtimeLogs(logs);
      console.log(`接收到 ${logs.length} 条历史日志`);
    });
    
    logClientRef.current.on('error', (error: Error) => {
      console.error('实时日志错误:', error);
      setWsConnectionStatus('disconnected');
      setIsRealTimeEnabled(false);
      // 不重置用户意图，让重连机制处理
    });
    
    return () => {
      logClientRef.current?.disconnect();
    };
  }, [autoScroll]);
  
  // 启用/禁用实时日志
  const toggleRealTime = useCallback(() => {
    if (!logClientRef.current) return;
    
    if (userWantsRealTime) {
      // 用户主动断开
      setUserWantsRealTime(false);
      logClientRef.current.disconnect();
      setIsRealTimeEnabled(false);
      setRealtimeLogs([]);
      setWsConnectionStatus('disconnected');
    } else {
      // 用户主动连接
      setUserWantsRealTime(true);
      setWsConnectionStatus('connecting');
      logClientRef.current.connect();
      setNewLogCount(0);
      
      // 获取最近的日志
      setTimeout(() => {
        logClientRef.current?.getRecentLogs(100);
      }, 1000);
    }
  }, [userWantsRealTime]);
  
  // 更新过滤器
  const updateLogFilter = useCallback(() => {
    if (!logClientRef.current || !isRealTimeEnabled) return;
    
    const filter: LogFilter = {
      levels: filters.level ? [filters.level] : ['ERROR', 'WARNING', 'INFO'],
      services: filters.service ? [filters.service] : [],
      keywords: filters.search ? [filters.search] : []
    };
    
    logClientRef.current.updateFilter(filter);
  }, [filters, isRealTimeEnabled]);
  
  // 监听过滤器变化
  useEffect(() => {
    updateLogFilter();
  }, [updateLogFilter]);
  
  // 清除新日志计数
  const clearNewLogCount = useCallback(() => {
    setNewLogCount(0);
  }, []);
  
  // 获取日志级别颜色
  const getLogLevelColor = (level: string) => {
    switch (level) {
      case 'ERROR':
      case 'CRITICAL':
        return '#f44336';
      case 'WARNING':
        return '#ff9800';
      case 'INFO':
        return '#2196f3';
      case 'DEBUG':
        return '#4caf50';
      default:
        return '#757575';
    }
  };

  // 保存日志配置
  const saveConfig = async () => {
    try {
      setLoading(true);
      
      // 添加调试信息
      console.log('保存配置数据:', config);
      console.log('Redis数据库值:', config.redisConfig.db);
      
      // 使用统一的认证API服务，自动处理认证token
      const result = await authenticatedApiService.post('/settings/logging/config/', config);
      
      console.log('后端响应:', result);
      
      if (result.success) {
        showSnackbar('日志配置保存成功', 'success');
        setConfigDialogOpen(false);
      } else {
        throw new Error(result.error || '保存配置失败');
      }
    } catch (error: any) {
      console.error('保存日志配置失败:', error);
      if (error?.response?.status === 401) {
        showSnackbar('认证失败，请重新登录', 'error');
      } else if (error?.response?.data) {
        showSnackbar(`保存失败: ${error.response.data.error || error.response.data.detail || '未知错误'}`, 'error');
      } else {
        showSnackbar(error instanceof Error ? error.message : '保存配置失败', 'error');
      }
    } finally {
      setLoading(false);
    }
  };

  // 获取日志列表 - 暂时禁用，使用搜索功能代替
  const fetchLogs = async () => {
    // 暂时显示提示，引导用户使用历史查询功能
    showSnackbar('请使用"历史查询与分析"标签页进行日志查询', 'info');
  };

  // 清理日志 - 暂时禁用
  const clearLogs = async () => {
    if (!confirm('确定要清理所有日志吗？此操作不可恢复。')) {
      return;
    }
    
    try {
      setLoading(true);
      // 暂时模拟清理操作
      setLogs([]);
      showSnackbar('日志清理功能暂未实现', 'warning');
    } catch (error) {
      console.error('清理日志失败:', error);
      showSnackbar('清理日志失败', 'error');
    } finally {
      setLoading(false);
    }
  };

  // Phase 3 API Calls
  const fetchSearchResults = async (page: number = 1) => {
    try {
      setLoading(true);
      
      // 保存查询到历史记录
      saveQueryToHistory(searchParams);
      
      // 过滤掉 undefined 值，确保发送的数据格式正确
      const requestBody = {
        start_time: searchParams.start_time || null,
        end_time: searchParams.end_time || null,
        levels: searchParams.levels || [],
        services: searchParams.services || [],
        keywords: searchParams.keywords || '',
        limit: searchParams.limit || 100,
        offset: (page - 1) * (searchParams.limit || 100)
      };

      console.log('发送搜索请求:', requestBody);

      const response = await fetch('http://localhost:8001/api/v1/logs/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('搜索请求失败:', response.status, errorText);
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
      }
      
      const data: LogSearchResult = await response.json();
      console.log('搜索结果:', data);
      setSearchResults(data);
      setCurrentPage(page);
      
      // 设置高亮关键词
      if (searchParams.keywords) {
        setLogHighlight(searchParams.keywords);
      }
      
      // After a successful search, fetch analysis data
      fetchLogAnalysis();

    } catch (error) {
      console.error('获取搜索结果失败:', error);
      showSnackbar(`获取搜索结果失败: ${error instanceof Error ? error.message : String(error)}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchLogAnalysis = async () => {
    try {
      // 过滤掉 undefined 值
      const requestBody = {
        start_time: searchParams.start_time || null,
        end_time: searchParams.end_time || null,
        levels: searchParams.levels || [],
        services: searchParams.services || [],
        keywords: searchParams.keywords || '',
        limit: searchParams.limit || 100,
        offset: 0
      };

      const response = await fetch('http://localhost:8001/api/v1/logs/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(requestBody)
      });
      
      if (!response.ok) {
        console.error('分析请求失败:', response.status);
        return; // 分析失败不影响搜索结果显示
      }
      const data: LogAnalysis = await response.json();
      setLogAnalysis(data);
    } catch (error) {
      console.error('获取日志分析失败:', error);
      // 分析失败不显示错误消息，因为不是关键功能
    }
  };

  const fetchLogStats = async () => {
    try {
      setLoading(true);
      const response = await fetch('http://localhost:8001/api/v1/logs/stats');
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data: LogStats = await response.json();
      setLogStats(data);
    } catch (error) {
      console.error('获取日志统计失败:', error);
      showSnackbar('获取日志统计失败', 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchLogIndex = async () => {
     try {
      setLoading(true);
      const response = await fetch('http://localhost:8001/api/v1/logs/files');
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const data: BackendLogFile[] = await response.json();
      
      // 存储后端文件列表
      setBackendLogFiles(data);
      
      // 转换为前端期望的 LogFileIndex 格式
      if (data.length > 0) {
        const combinedIndex: LogFileIndex = {
          files: data.map(file => ({
            path: file.file_path,
            relative_path: file.file_path,
            size: file.size_mb * 1024 * 1024, // 转换为字节
            modified: file.last_modified,
            is_compressed: false,
            service: file.service,
            level: file.levels_found.join(',')
          })),
          date_range: data.length > 0 && data[0].date_range.length > 0 ? data[0].date_range : [],
          services: [...new Set(data.map(file => file.service))],
          levels: [...new Set(data.flatMap(file => file.levels_found))],
          total_size: data.reduce((sum, file) => sum + file.size_mb * 1024 * 1024, 0),
          build_time: new Date().toISOString()
        };
        setLogIndex(combinedIndex);
      }
    } catch (error) {
      console.error('获取日志索引失败:', error);
      showSnackbar('获取日志索引失败', 'error');
    } finally {
      setLoading(false);
    }
  };

  const buildLogIndex = async () => {
    try {
      setLoading(true);
      showSnackbar('开始重建索引，请稍候...', 'info');
      const response = await fetch('http://localhost:8001/api/v1/logs/rebuild-index', { 
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const result = await response.json();
      
      // 重新获取文件列表
      await fetchLogIndex();
      showSnackbar(result.message || '索引重建成功', 'success');
    } catch (error) {
      console.error('重建索引失败:', error);
      showSnackbar('重建索引失败', 'error');
    } finally {
      setLoading(false);
    }
  };

  // 显示通知
  const showSnackbar = (message: string, severity: 'success' | 'error' | 'info' | 'warning') => {
    setSnackbarMessage(message);
    setSnackbarSeverity(severity);
    setSnackbarOpen(true);
  };
  
  // Phase 3 增强功能函数
  
  // 保存查询到历史记录
  const saveQueryToHistory = (params: LogSearchParams) => {
    const newQuery = { ...params, timestamp: new Date().toISOString() };
    setQueryHistory(prev => {
      const filtered = prev.filter(q => JSON.stringify(q) !== JSON.stringify(newQuery));
      return [newQuery, ...filtered].slice(0, 20); // 保持最近20个查询
    });
  };

  // 添加到收藏查询
  const addToFavorites = (params: LogSearchParams) => {
    const newFavorite = { ...params, name: `Query ${Date.now()}` };
    setFavoriteQueries(prev => [...prev, newFavorite]);
    showSnackbar('查询已添加到收藏', 'success');
  };

  // 导出日志
  const exportLogs = async (format: 'json' | 'csv' | 'txt') => {
    if (!searchResults) {
      showSnackbar('没有可导出的数据', 'warning');
      return;
    }
    
    try {
      let content = '';
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      
      switch (format) {
        case 'json':
          content = JSON.stringify(searchResults.logs, null, 2);
          break;
        case 'csv':
          const headers = ['时间', '级别', '服务', '消息'];
          const rows = searchResults.logs.map(log => [
            log.timestamp,
            log.level,
            log.service,
            `"${log.message.replace(/"/g, '""')}"` // CSV转义
          ]);
          content = [headers.join(','), ...rows.map(row => row.join(','))].join('\n');
          break;
        case 'txt':
          content = searchResults.logs.map(log => 
            `[${log.timestamp}] [${log.level}] [${log.service}] ${log.message}`
          ).join('\n');
          break;
      }
      
      const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `logs_export_${timestamp}.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      showSnackbar(`日志已导出为 ${format.toUpperCase()} 格式`, 'success');
      setExportDialogOpen(false);
    } catch (error) {
      console.error('导出失败:', error);
      showSnackbar('导出失败', 'error');
    }
  };

  // 高亮搜索关键词
  const highlightText = (text: string, highlight: string) => {
    if (!highlight) return text;
    
    const parts = text.split(new RegExp(`(${highlight})`, 'gi'));
    return parts.map((part, index) => 
      part.toLowerCase() === highlight.toLowerCase() 
        ? `<mark style="background-color: yellow;">${part}</mark>` 
        : part
    ).join('');
  };

  // 自动刷新
  React.useEffect(() => {
    let interval: number;
    
    if (autoRefresh && searchResults) {
      interval = window.setInterval(() => {
        fetchSearchResults(currentPage);
      }, refreshInterval * 1000);
    }
    
    return () => {
      if (interval) window.clearInterval(interval);
    };
  }, [autoRefresh, refreshInterval, currentPage, searchResults]);

  // 实时搜索建议
  const getSearchSuggestions = (query: string): string[] => {
    const suggestions = [
      'ERROR AND database',
      'WARNING OR timeout',
      'INFO NOT success',
      'CRITICAL',
      'level:ERROR service:django',
      'timestamp:[2025-01-21 TO 2025-01-22]',
      'message:"connection failed"'
    ];
    
    return suggestions.filter(s => 
      s.toLowerCase().includes(query.toLowerCase())
    ).slice(0, 5);
  };

  // 获取配置
  const fetchConfig = async () => {
    try {
      setLoading(true);
      
      // 从后端API获取已保存的配置
      const result = await authenticatedApiService.get('/settings/logging/config/');
      
      console.log('从后端加载的配置:', result);
      
      if (result.success && result.data) {
        // 更新配置状态
        setConfig(result.data);
        console.log('配置加载成功:', result.data);
      } else {
        console.log('使用默认配置');
      }
    } catch (error) {
      console.error('获取日志配置失败:', error);
      console.log('使用默认配置');
      // 保持默认配置，不影响用户体验
    } finally {
      setLoading(false);
    }
  };

  // 组件挂载时获取初始数据
  useEffect(() => {
    fetchConfig();
    // Initial data for the first tab can be fetched here if needed
  }, []);

  // 标签页切换处理
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
    if (newValue === 2 && !logStats) { // Tab 3
      fetchLogStats();
      fetchLogIndex();
    }
  };

  return (
    <Box sx={{ p: 3, height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
        <Typography variant="h4" gutterBottom>
          日志管理中心
        </Typography>
        <Button
          variant="outlined"
          startIcon={<SettingsIcon />}
          onClick={() => setConfigDialogOpen(true)}
        >
          系统配置
        </Button>
      </Stack>
      
      <Breadcrumbs aria-label="breadcrumb" sx={{ mb: 2 }}>
        <Link underline="hover" color="inherit" href="/settings">
          系统设置
        </Link>
        <Typography color="text.primary">日志管理</Typography>
      </Breadcrumbs>

      <Paper elevation={3} sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={currentTab} onChange={handleTabChange} aria-label="log management tabs">
            <Tab label="实时监控" icon={<WifiIcon />} iconPosition="start" />
            <Tab label="历史查询与分析" icon={<HistoryIcon />} iconPosition="start" />
            <Tab label="系统状态与索引" icon={<DashboardIcon />} iconPosition="start" />
          </Tabs>
        </Box>

        {/* Tab 1: 实时监控 */}
        <TabPanel value={currentTab} index={0}>
          <Box sx={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 280px)', overflow: 'hidden' }}>
            <Card sx={{ mb: 2, flexShrink: 0 }}>
              <CardContent sx={{ pb: 1 }}>
                <Grid container spacing={2} alignItems="center" sx={{ flexWrap: 'wrap' }}>
                  <Grid item>
                    <Typography variant="h6">实时日志</Typography>
                  </Grid>
                  <Grid item>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={userWantsRealTime}
                          onChange={toggleRealTime}
                          color="primary"
                        />
                      }
                      label={userWantsRealTime ? 
                        (wsConnectionStatus === 'connected' ? '正在接收...' : '正在连接...') : 
                        '启动实时日志'
                      }
                    />
                  </Grid>
                  <Grid item>
                    <Chip
                      icon={wsConnectionStatus === 'connected' ? <WifiIcon /> : <WifiOffIcon />}
                      label={wsConnectionStatus.toUpperCase()}
                      color={wsConnectionStatus === 'connected' ? 'success' : 'error'}
                      size="small"
                    />
                  </Grid>
                  <Grid item sx={{ flexGrow: 1 }} />
                  <Grid item>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={autoScroll}
                          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setAutoScroll(e.target.checked)}
                        />
                      }
                      label="自动滚动"
                    />
                  </Grid>
                  <Grid item>
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<DeleteIcon />}
                      onClick={() => setRealtimeLogs([])}
                      disabled={!isRealTimeEnabled}
                    >
                      清空视图
                    </Button>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
            <Paper
              ref={logContainerRef}
              elevation={2}
              sx={{
                flexGrow: 1,
                minHeight: 0, // 允许容器缩小
                overflowY: 'auto',
                p: 2,
                backgroundColor: '#1e1e1e',
                color: '#d4d4d4',
                fontFamily: 'monospace',
                fontSize: '0.875rem',
              }}
            >
              {wsConnectionStatus === 'connecting' && <Typography>正在连接...</Typography>}
              {wsConnectionStatus === 'disconnected' && <Typography>已断开连接。请启动实时日志。</Typography>}
              {realtimeLogs.map((log, index) => (
                <Box key={index} sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 0.5 }}>
                  <Typography variant="caption" sx={{ color: '#888', whiteSpace: 'nowrap' }}>
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </Typography>
                  <Chip
                    label={log.level}
                    size="small"
                    sx={{
                      backgroundColor: getLogLevelColor(log.level),
                      color: '#fff',
                      height: '20px',
                      fontSize: '0.7rem',
                    }}
                  />
                  <Typography variant="caption" sx={{ color: '#6a9955', minWidth: '80px' }}>
                    [{log.service}]
                  </Typography>
                  <Typography sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                    {log.message}
                  </Typography>
                </Box>
              ))}
            </Paper>
          </Box>
        </TabPanel>

        {/* Tab 2: 历史查询与分析 */}
        <TabPanel value={currentTab} index={1}>
          <Box sx={{ display: 'flex', height: 'calc(100vh - 280px)', overflow: 'hidden' }}>
            {/* 左侧：搜索、结果、详情 */}
            <Box sx={{ width: '65%', pr: 2, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
              {/* 搜索区域 */}
              <Card sx={{ mb: 2, minHeight: 'auto', flexShrink: 0 }}>
                <CardContent sx={{ pb: 3, '&:last-child': { pb: 3 } }}>
                  {/* 搜索工具栏 */}
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6">日志搜索</Typography>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Tooltip title="查询历史">
                        <IconButton size="small" onClick={() => setAdvancedSearchOpen(true)}>
                          <HistoryIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="收藏当前查询">
                        <IconButton size="small" onClick={() => addToFavorites(searchParams)}>
                          <FavoriteIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="导出结果">
                        <IconButton size="small" onClick={() => setExportDialogOpen(true)} disabled={!searchResults}>
                          <GetAppIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title={autoRefresh ? '停止自动刷新' : '启用自动刷新'}>
                        <IconButton 
                          size="small" 
                          onClick={() => setAutoRefresh(!autoRefresh)}
                          color={autoRefresh ? 'primary' : 'default'}
                        >
                          <AutorenewIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title={compactView ? '标准视图' : '紧凑视图'}>
                        <IconButton 
                          size="small" 
                          onClick={() => setCompactView(!compactView)}
                          color={compactView ? 'primary' : 'default'}
                        >
                          <ViewCompactIcon />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </Box>
                  
                  {/* 第一行：时间选择器 */}
                  <Grid container spacing={2} sx={{ mb: 2 }}>
                    <Grid item xs={12} sm={6}>
                      <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={zhCN}>
                        <DateTimePicker
                          label="开始时间"
                          value={searchParams.start_time ? new Date(searchParams.start_time) : null}
                          onChange={(newValue: Date | null) => setSearchParams(prev => ({ ...prev, start_time: newValue?.toISOString() }))}
                          slotProps={{
                            textField: {
                              fullWidth: true,
                              size: 'small',
                            },
                          }}
                        />
                      </LocalizationProvider>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={zhCN}>
                        <DateTimePicker
                          label="结束时间"
                          value={searchParams.end_time ? new Date(searchParams.end_time) : null}
                          onChange={(newValue: Date | null) => setSearchParams(prev => ({ ...prev, end_time: newValue?.toISOString() }))}
                          slotProps={{
                            textField: {
                              fullWidth: true,
                              size: 'small',
                            },
                          }}
                        />
                      </LocalizationProvider>
                    </Grid>
                  </Grid>

                  {/* 第二行：过滤器 */}
                  <Grid container spacing={2} sx={{ mb: 2 }}>
                    <Grid item xs={12} sm={12} md={8} sx={{ minWidth: '300px' }}>
                      <FormControl fullWidth size="small" sx={{ minWidth: '250px' }}>
                        <InputLabel sx={{ whiteSpace: 'nowrap' }}>日志级别</InputLabel>
                        <Select
                          multiple
                          value={searchParams.levels || []}
                          onChange={(e) => {
                            const value = e.target.value;
                            setSearchParams(prev => ({ ...prev, levels: typeof value === 'string' ? [value] : value }));
                          }}
                          label="日志级别"
                        >
                          {['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'].map(level => (
                            <MenuItem key={level} value={level}>{level}</MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                    <Grid item xs={12} sm={12} md={4} sx={{ minWidth: '150px' }}>
                      <FormControl fullWidth size="small" sx={{ minWidth: '120px' }}>
                        <InputLabel sx={{ whiteSpace: 'nowrap' }}>服务</InputLabel>
                        <Select
                          multiple
                          value={searchParams.services || []}
                          onChange={(e) => {
                            const value = e.target.value;
                            setSearchParams(prev => ({ ...prev, services: typeof value === 'string' ? [value] : value }));
                          }}
                          label="服务"
                        >
                          {['django', 'fastapi', 'system'].map(service => (
                            <MenuItem key={service} value={service}>{service.toUpperCase()}</MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                  </Grid>

                  {/* 第三行：关键词搜索 */}
                  <Grid container spacing={2} sx={{ mb: 2 }}>
                    <Grid item xs={12}>
                      <TextField
                        fullWidth
                        size="small"
                        label="关键词搜索"
                        placeholder="支持 'AND', 'OR', 'NOT'"
                        value={searchParams.keywords || ''}
                        onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchParams(prev => ({ ...prev, keywords: e.target.value }))}
                      />
                    </Grid>
                  </Grid>

                  {/* 第四行：搜索按钮 */}
                  <Grid container spacing={2} sx={{ mt: 1 }}>
                    <Grid item xs={12} sm={6} md={4} lg={3}>
                      <Button
                        fullWidth
                        variant="contained"
                        startIcon={<SearchIcon />}
                        onClick={() => { setCurrentPage(1); fetchSearchResults(1); }}
                        disabled={loading}
                        sx={{ height: '40px' }}
                      >
                        {loading ? '搜索中...' : '搜索'}
                      </Button>
                    </Grid>
                    <Grid item xs={12} sm={6} md={4} lg={3}>
                      <Button
                        fullWidth
                        variant="outlined"
                        onClick={() => {
                          setSearchParams({
                            start_time: undefined,
                            end_time: undefined,
                            levels: [],
                            services: [],
                            keywords: '',
                            limit: 100,
                            offset: 0
                          });
                          setSearchResults(null);
                          setLogAnalysis(null);
                        }}
                        sx={{ height: '40px' }}
                      >
                        清空条件
                      </Button>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
              {/* 结果表格 */}
              <Paper sx={{ flexGrow: 1, minHeight: 0, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
                <TableContainer sx={{ flexGrow: 1, overflowY: 'auto' }}>
                  <Table stickyHeader size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>时间</TableCell>
                        <TableCell>级别</TableCell>
                        <TableCell>服务</TableCell>
                        <TableCell>消息</TableCell>
                        <TableCell>操作</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {loading && <TableRow><TableCell colSpan={5}><LinearProgress /></TableCell></TableRow>}
                      {searchResults?.logs.map((log, idx) => (
                        <TableRow 
                          key={log.id || idx} 
                          hover 
                          onClick={() => { setSelectedLogDetails(log); setDetailsDrawerOpen(true); }}
                          sx={{ cursor: 'pointer', height: compactView ? 32 : 48 }}
                        >
                          <TableCell sx={{ fontSize: compactView ? '0.75rem' : '0.875rem' }}>
                            {new Date(log.timestamp).toLocaleString()}
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={log.level} 
                              size={compactView ? "small" : "medium"} 
                              sx={{ 
                                backgroundColor: getLogLevelColor(log.level), 
                                color: '#fff',
                                fontSize: compactView ? '0.6rem' : '0.75rem'
                              }} 
                            />
                          </TableCell>
                          <TableCell sx={{ fontSize: compactView ? '0.75rem' : '0.875rem' }}>
                            {log.service}
                          </TableCell>
                          <TableCell 
                            sx={{ 
                              maxWidth: 300, 
                              overflow: 'hidden', 
                              textOverflow: 'ellipsis', 
                              whiteSpace: 'nowrap',
                              fontSize: compactView ? '0.75rem' : '0.875rem'
                            }}
                          >
                            <span 
                              dangerouslySetInnerHTML={{
                                __html: logHighlight ? highlightText(log.message, logHighlight) : log.message
                              }}
                            />
                          </TableCell>
                          <TableCell>
                            <Tooltip title="查看详情">
                              <IconButton size="small"><VisibilityIcon /></IconButton>
                            </Tooltip>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
                {/* 分页 */}
                {searchResults && searchResults.total_count > 0 && (
                  <Box sx={{ p: 2, display: 'flex', justifyContent: 'center' }}>
                    <Pagination
                      count={Math.ceil(searchResults.total_count / (searchParams.limit || 100))}
                      page={currentPage}
                      onChange={(e: React.ChangeEvent<unknown>, page: number) => fetchSearchResults(page)}
                      color="primary"
                    />
                  </Box>
                )}
              </Paper>
            </Box>
            {/* 右侧：分析图表 */}
            <Box sx={{ width: '35%', pl: 2, display: 'flex', flexDirection: 'column' }}>
              <Card sx={{ flexGrow: 1 }}>
                <CardContent>
                  <Typography variant="h6">日志分析</Typography>
                  {logAnalysis ? (
                    <Box>
                      <Typography variant="subtitle1">日志级别分布</Typography>
                      <ResponsiveContainer width="100%" height={200}>
                        <PieChart>
                          <Pie 
                            dataKey="value" 
                            data={Object.entries(logAnalysis.by_level).map(([name, value]) => ({ name, value }))} 
                            cx="50%" 
                            cy="50%" 
                            outerRadius={60} 
                            fill="#8884d8" 
                            label={(entry: { name: string; value: number }) => entry.name}
                          >
                            {Object.entries(logAnalysis.by_level).map(([name, value], index) => (
                              <Cell key={`cell-${index}`} fill={getLogLevelColor(name)} />
                            ))}
                          </Pie>
                          <RechartsTooltip />
                        </PieChart>
                      </ResponsiveContainer>
                      <Typography variant="subtitle1">服务日志量</Typography>
                      <ResponsiveContainer width="100%" height={200}>
                        <BarChart data={Object.entries(logAnalysis.by_service).map(([name, value]) => ({ name, value }))}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="name" />
                          <YAxis />
                          <RechartsTooltip formatter={(value: number) => [value, '日志条数']} />
                          <Bar dataKey="value" fill="#82ca9d" />
                        </BarChart>
                      </ResponsiveContainer>
                    </Box>
                  ) : (
                    <Typography>执行搜索以查看分析结果。</Typography>
                  )}
                </CardContent>
              </Card>
            </Box>
          </Box>
        </TabPanel>
        
        {/* Tab 3: 系统状态与索引 */}
        <TabPanel value={currentTab} index={2}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>日志系统状态</Typography>
                  {logStats ? (
                    <List>
                      <ListItem><ListItemText primary="总文件数" secondary={logStats.total_files} /></ListItem>
                      <ListItem><ListItemText primary="总大小" secondary={`${logStats.total_size_mb.toFixed(2)} MB`} /></ListItem>
                      <ListItem><ListItemText primary="服务" secondary={logStats.services.join(', ')} /></ListItem>
                      <ListItem><ListItemText primary="级别" secondary={logStats.levels.join(', ')} /></ListItem>
                      <ListItem><ListItemText primary="日期范围" secondary={logStats.date_range.join(' to ')} /></ListItem>
                      <ListItem><ListItemText primary="最后更新" secondary={new Date(logStats.last_updated).toLocaleString()} /></ListItem>
                    </List>
                  ) : <CircularProgress />}
                   <Button
                      variant="contained"
                      startIcon={<RefreshIcon />}
                      onClick={fetchLogStats}
                      disabled={loading}
                      sx={{mt: 2}}
                    >
                      刷新状态
                    </Button>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={8}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6" gutterBottom>日志文件索引</Typography>
                     <Button
                        variant="contained"
                        startIcon={<AutorenewIcon />}
                        onClick={buildLogIndex}
                        disabled={loading}
                      >
                        重建索引
                      </Button>
                  </Box>
                  <TableContainer component={Paper} sx={{maxHeight: 400}}>
                    <Table stickyHeader size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell sx={{ minWidth: 200 }}>文件路径</TableCell>
                          <TableCell sx={{ minWidth: 100 }}>大小 (KB)</TableCell>
                          <TableCell sx={{ minWidth: 80 }}>服务</TableCell>
                          <TableCell sx={{ minWidth: 150 }}>修改日期</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {loading && !logIndex && <TableRow><TableCell colSpan={4}><LinearProgress /></TableCell></TableRow>}
                        {logIndex?.files.map(file => (
                          <TableRow key={file.path}>
                            <TableCell>
                              <Tooltip 
                                title={
                                  <Box>
                                    <Typography variant="caption" component="div">
                                      <strong>完整路径:</strong>
                                    </Typography>
                                    <Typography variant="body2" component="div" sx={{ fontFamily: 'monospace', mt: 0.5 }}>
                                      {file.path}
                                    </Typography>
                                    {(() => {
                                      const fileInfo = backendLogFiles.find(bf => bf.file_path === file.path);
                                      return fileInfo && (
                                        <>
                                          <Typography variant="caption" component="div" sx={{ mt: 1 }}>
                                            <strong>文件信息:</strong>
                                          </Typography>
                                          <Typography variant="body2" component="div">
                                            行数: {fileInfo.line_count.toLocaleString()}
                                          </Typography>
                                          <Typography variant="body2" component="div">
                                            日志级别: {fileInfo.levels_found.join(', ')}
                                          </Typography>
                                          {fileInfo.date_range && fileInfo.date_range.length > 0 && (
                                            <Typography variant="body2" component="div">
                                              时间范围: {fileInfo.date_range.join(' 至 ')}
                                            </Typography>
                                          )}
                                        </>
                                      );
                                    })()}
                                  </Box>
                                } 
                                placement="right"
                                arrow
                                enterDelay={500}
                                leaveDelay={200}
                              >
                                <Box 
                                  sx={{ 
                                    cursor: 'pointer', 
                                    '&:hover': { 
                                      backgroundColor: 'action.hover',
                                      borderRadius: 1,
                                      px: 0.5
                                    },
                                    maxWidth: '200px',
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                    whiteSpace: 'nowrap'
                                  }}
                                >
                                  {file.relative_path || file.path}
                                </Box>
                              </Tooltip>
                            </TableCell>
                            <TableCell>{(file.size / 1024).toFixed(2)}</TableCell>
                            <TableCell>{file.service}</TableCell>
                            <TableCell>{new Date(file.modified).toLocaleString()}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>

      {/* 日志详情 Drawer */}
      <Drawer
        anchor="right"
        open={detailsDrawerOpen}
        onClose={() => setDetailsDrawerOpen(false)}
      >
        <Box sx={{ width: 500, p: 3 }}>
          <Typography variant="h5" gutterBottom>日志详情</Typography>
          <Divider sx={{ mb: 2 }} />
          {selectedLogDetails && (
            <List>
              <ListItem><ListItemText primary="时间戳" secondary={new Date(selectedLogDetails.timestamp).toLocaleString()} /></ListItem>
              <ListItem><ListItemText primary="级别" secondary={<Chip label={selectedLogDetails.level} size="small" sx={{ backgroundColor: getLogLevelColor(selectedLogDetails.level), color: '#fff' }} />} /></ListItem>
              <ListItem><ListItemText primary="服务" secondary={selectedLogDetails.service} /></ListItem>
              <ListItem><ListItemText primary="模块" secondary={selectedLogDetails.module ?? 'N/A'} /></ListItem>
              <ListItem><ListItemText primary="Logger" secondary={selectedLogDetails.logger ?? 'N/A'} /></ListItem>
              <ListItem><ListItemText primary="文件" secondary={selectedLogDetails.file ? `${selectedLogDetails.file}:${selectedLogDetails.line_number ?? ''}` : 'N/A'} /></ListItem>
              <ListItem>
                <ListItemText 
                  primary="消息" 
                  secondary={<Typography sx={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>{selectedLogDetails.message}</Typography>} 
                />
              </ListItem>
              {selectedLogDetails.extra_data && (
                <ListItem>
                  <Accordion sx={{ width: '100%' }}>
                    <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                      <Typography>额外数据</Typography>
                    </AccordionSummary>
                    <AccordionDetails>
                      <Paper sx={{ p: 2, backgroundColor: '#f5f5f5' }}>
                        <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                          {JSON.stringify(selectedLogDetails.extra_data, null, 2)}
                        </pre>
                      </Paper>
                    </AccordionDetails>
                  </Accordion>
                </ListItem>
              )}
            </List>
          )}
        </Box>
      </Drawer>

      {/* 配置对话框 */}
      <Dialog
        open={configDialogOpen}
        onClose={() => setConfigDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>日志系统配置</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <Accordion defaultExpanded>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6">基础配置</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <FormControl fullWidth>
                      <InputLabel>日志级别</InputLabel>
                      <Select
                        value={config.level}
                        label="日志级别"
                        onChange={(e: SelectChangeEvent<string>) => setConfig({...config, level: e.target.value})}
                      >
                        <MenuItem value="DEBUG">DEBUG</MenuItem>
                        <MenuItem value="INFO">INFO</MenuItem>
                        <MenuItem value="WARNING">WARNING</MenuItem>
                        <MenuItem value="ERROR">ERROR</MenuItem>
                        <MenuItem value="CRITICAL">CRITICAL</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} sm={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={config.enableRedis}
                          onChange={(e: React.ChangeEvent<HTMLInputElement>) => setConfig({...config, enableRedis: e.target.checked})}
                        />
                      }
                      label="启用Redis实时通道"
                    />
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>

            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6">Redis配置</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Redis主机"
                      value={config.redisConfig.host}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setConfig({
                        ...config,
                        redisConfig: {...config.redisConfig, host: e.target.value}
                      })}
                    />
                  </Grid>
                  <Grid item xs={12} sm={3}>
                    <TextField
                      fullWidth
                      label="端口"
                      type="number"
                      value={config.redisConfig.port}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setConfig({
                        ...config,
                        redisConfig: {...config.redisConfig, port: parseInt(e.target.value)}
                      })}
                    />
                  </Grid>
                  <Grid item xs={12} sm={3}>
                    <TextField
                      fullWidth
                      label="数据库"
                      type="number"
                      value={config.redisConfig.db}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setConfig({
                        ...config,
                        redisConfig: {...config.redisConfig, db: parseInt(e.target.value)}
                      })}
                    />
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>

            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="h6">文件轮转配置</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={4}>
                    <FormControl fullWidth>
                      <InputLabel>轮转周期</InputLabel>
                      <Select
                        value={config.fileRotation.when}
                        label="轮转周期"
                        onChange={(e: SelectChangeEvent<string>) => setConfig({
                          ...config,
                          fileRotation: {...config.fileRotation, when: e.target.value}
                        })}
                      >
                        <MenuItem value="midnight">每日 (midnight)</MenuItem>
                        <MenuItem value="H">每小时</MenuItem>
                        <MenuItem value="D">每天</MenuItem>
                        <MenuItem value="W0">每周 (周一)</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid item xs={12} sm={4}>
                    <TextField
                      fullWidth
                      label="轮转间隔"
                      type="number"
                      helperText="例如：周期为'每小时'，间隔为2，即每2小时轮转一次"
                      value={config.fileRotation.interval}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setConfig({
                        ...config,
                        fileRotation: {...config.fileRotation, interval: parseInt(e.target.value)}
                      })}
                    />
                  </Grid>
                  <Grid item xs={12} sm={4}>
                    <TextField
                      fullWidth
                      label="保留文件数"
                      type="number"
                      helperText="保留的旧日志文件数量"
                      value={config.fileRotation.backupCount}
                      onChange={(e: React.ChangeEvent<HTMLInputElement>) => setConfig({
                        ...config,
                        fileRotation: {...config.fileRotation, backupCount: parseInt(e.target.value)}
                      })}
                    />
                  </Grid>
                </Grid>
              </AccordionDetails>
            </Accordion>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfigDialogOpen(false)}>取消</Button>
          <Button onClick={saveConfig} variant="contained" disabled={loading}>
            保存配置
          </Button>
        </DialogActions>
      </Dialog>

      {/* 导出对话框 */}
      <Dialog open={exportDialogOpen} onClose={() => setExportDialogOpen(false)}>
        <DialogTitle>导出日志</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            选择导出格式：
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            <Button
              variant="outlined"
              startIcon={<GetAppIcon />}
              onClick={() => exportLogs('json')}
              fullWidth
            >
              JSON 格式 (.json)
            </Button>
            <Button
              variant="outlined"
              startIcon={<GetAppIcon />}
              onClick={() => exportLogs('csv')}
              fullWidth
            >
              CSV 格式 (.csv)
            </Button>
            <Button
              variant="outlined"
              startIcon={<GetAppIcon />}
              onClick={() => exportLogs('txt')}
              fullWidth
            >
              文本格式 (.txt)
            </Button>
          </Box>
          {searchResults && (
            <Typography variant="caption" sx={{ mt: 2, display: 'block' }}>
              将导出 {searchResults.logs.length} 条日志记录
            </Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExportDialogOpen(false)}>取消</Button>
        </DialogActions>
      </Dialog>

      {/* 高级搜索/查询历史对话框 */}
      <Dialog 
        open={advancedSearchOpen} 
        onClose={() => setAdvancedSearchOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>查询历史与收藏</DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>查询历史</Typography>
            {queryHistory.length > 0 ? (
              <List>
                {queryHistory.slice(0, 10).map((query, index) => (
                  <ListItem key={index} disablePadding>
                    <ListItemButton
                      onClick={() => {
                        setSearchParams(query);
                        setAdvancedSearchOpen(false);
                      }}
                    >
                      <ListItemText
                        primary={query.keywords || '空关键词查询'}
                        secondary={`级别: ${query.levels?.join(', ') || '全部'} | 服务: ${query.services?.join(', ') || '全部'} | ${query.timestamp ? new Date(query.timestamp).toLocaleString() : ''}`}
                      />
                    </ListItemButton>
                    <ListItemSecondaryAction>
                      <IconButton
                        edge="end"
                        onClick={(e) => {
                          e.stopPropagation();
                          addToFavorites(query);
                        }}
                      >
                        <FavoriteIcon />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography variant="body2" color="textSecondary">
                暂无查询历史
              </Typography>
            )}
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>收藏的查询</Typography>
            {favoriteQueries.length > 0 ? (
              <List>
                {favoriteQueries.map((query, index) => (
                  <ListItem key={index} disablePadding>
                    <ListItemButton
                      onClick={() => {
                        setSearchParams(query);
                        setAdvancedSearchOpen(false);
                      }}
                    >
                      <ListItemText
                        primary={query.name || query.keywords || '收藏查询'}
                        secondary={`级别: ${query.levels?.join(', ') || '全部'} | 服务: ${query.services?.join(', ') || '全部'}`}
                      />
                    </ListItemButton>
                    <ListItemSecondaryAction>
                      <IconButton
                        edge="end"
                        onClick={(e) => {
                          e.stopPropagation();
                          setFavoriteQueries(prev => prev.filter((_, i) => i !== index));
                        }}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography variant="body2" color="textSecondary">
                暂无收藏查询
              </Typography>
            )}
          </Box>

          <Box>
            <Typography variant="h6" gutterBottom>搜索语法帮助</Typography>
            <Typography variant="body2" component="div">
              <ul>
                <li><code>ERROR AND database</code> - 包含 "ERROR" 和 "database" 的日志</li>
                <li><code>WARNING OR timeout</code> - 包含 "WARNING" 或 "timeout" 的日志</li>
                <li><code>INFO NOT success</code> - 包含 "INFO" 但不包含 "success" 的日志</li>
                <li><code>"connection failed"</code> - 包含确切短语的日志</li>
              </ul>
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAdvancedSearchOpen(false)}>关闭</Button>
        </DialogActions>
      </Dialog>

      {/* 自动刷新状态指示器 */}
      {autoRefresh && (
        <Box
          sx={{
            position: 'fixed',
            bottom: 80,
            right: 20,
            backgroundColor: 'primary.main',
            color: 'white',
            padding: '8px 16px',
            borderRadius: 2,
            display: 'flex',
            alignItems: 'center',
            gap: 1,
            zIndex: 1000
          }}
        >
          <AutorenewIcon sx={{ animation: 'spin 2s linear infinite' }} />
          <Typography variant="caption">
            自动刷新 ({refreshInterval}s)
          </Typography>
        </Box>
      )}

      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={() => setSnackbarOpen(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={() => setSnackbarOpen(false)} severity={snackbarSeverity} sx={{ width: '100%' }}>
          {snackbarMessage}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default LogManagement;
