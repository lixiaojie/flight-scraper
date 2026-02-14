import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { 
  Database, 
  Server, 
  Smartphone,
  Activity,
  BarChart3,
  Plane,
  CheckCircle,
  Clock,
  DollarSign,
  TrendingUp
} from 'lucide-react';
import { apiFetch } from '../lib/api';

interface TaskStatistics {
  total_tasks: number;
  successful_tasks: number;
  failed_tasks: number;
  running_tasks: number;
  success_rate: number;
  avg_duration: number;
  total_flights: number;
}

interface FlightStatistics {
  total_flights: number;
  min_price: number;
  max_price: number;
  avg_price: number;
}

const Dashboard: React.FC = () => {
  const [taskStats, setTaskStats] = useState<TaskStatistics | null>(null);
  const [flightStats, setFlightStats] = useState<FlightStatistics | null>(null);
  const [loading, setLoading] = useState(true);

  // 获取任务统计信息
  const fetchTaskStatistics = async () => {
    try {
      const response = await apiFetch('/api/tasks/stats');
      if (response.ok) {
        const data = await response.json();
        setTaskStats(data);
      }
    } catch (error) {
      console.error('获取任务统计信息失败:', error);
    }
  };

  // 获取航班统计信息
  const fetchFlightStatistics = async () => {
    try {
      const response = await apiFetch('/api/flights/statistics');
      if (response.ok) {
        const data = await response.json();
        setFlightStats(data);
      }
    } catch (error) {
      console.error('获取航班统计信息失败:', error);
    }
  };

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchTaskStatistics(), fetchFlightStatistics()]);
      setLoading(false);
    };
    loadData();
    
    // 设置自动刷新：每10秒刷新一次统计数据
    const refreshInterval = setInterval(() => {
      fetchTaskStatistics();
      fetchFlightStatistics();
    }, 10000);
    
    return () => clearInterval(refreshInterval);
  }, []);

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '-';
    const totalSeconds = Math.round(seconds);
    const minutes = Math.floor(totalSeconds / 60);
    const remainingSeconds = totalSeconds % 60;
    return `${minutes}分${remainingSeconds}秒`;
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(price);
  };

  return (
    <div>
      {/* 主要内容 */}
      <div>
        <div>
          <div className="mb-4">
            <h1 className="text-2xl font-bold text-gray-900">仪表板</h1>
            <p className="mt-1 text-sm text-gray-600">
              管理和监控航班信息抓取系统
            </p>
          </div>

          {/* 任务统计卡片 */}
          {loading ? (
            <div className="mb-4 text-center py-4">
              <p className="text-sm text-gray-600">加载统计数据...</p>
            </div>
          ) : taskStats ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2 mb-4">
              <Card>
                <CardContent className="p-3">
                  <div className="flex items-center">
                    <BarChart3 className="h-5 w-5 text-blue-600 flex-shrink-0" />
                    <div className="ml-2 min-w-0">
                      <p className="text-xs font-medium text-gray-600">总任务数</p>
                      <p className="text-xl font-bold text-gray-900">{taskStats.total_tasks}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-3">
                  <div className="flex items-center">
                    <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0" />
                    <div className="ml-2 min-w-0">
                      <p className="text-xs font-medium text-gray-600">成功率</p>
                      <p className="text-xl font-bold text-gray-900">{taskStats.success_rate}%</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-3">
                  <div className="flex items-center">
                    <Clock className="h-5 w-5 text-orange-600 flex-shrink-0" />
                    <div className="ml-2 min-w-0">
                      <p className="text-xs font-medium text-gray-600">平均时长</p>
                      <p className="text-xl font-bold text-gray-900">{formatDuration(taskStats.avg_duration)}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-3">
                  <div className="flex items-center">
                    <Plane className="h-5 w-5 text-purple-600 flex-shrink-0" />
                    <div className="ml-2 min-w-0">
                      <p className="text-xs font-medium text-gray-600">总航班数</p>
                      <p className="text-xl font-bold text-gray-900">{taskStats.total_flights}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : null}

          {/* 航班统计卡片 */}
          {flightStats ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2 mb-4">
              <Card>
                <CardContent className="p-3">
                  <div className="flex items-center">
                    <Plane className="h-5 w-5 text-blue-600 flex-shrink-0" />
                    <div className="ml-2 min-w-0">
                      <p className="text-xs font-medium text-gray-600">总航班数</p>
                      <p className="text-xl font-bold text-gray-900">{flightStats.total_flights}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-3">
                  <div className="flex items-center">
                    <TrendingUp className="h-5 w-5 text-green-600 flex-shrink-0" />
                    <div className="ml-2 min-w-0">
                      <p className="text-xs font-medium text-gray-600">最低价格</p>
                      <p className="text-xl font-bold text-gray-900">{formatPrice(flightStats.min_price)}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-3">
                  <div className="flex items-center">
                    <TrendingUp className="h-5 w-5 text-red-600 flex-shrink-0" />
                    <div className="ml-2 min-w-0">
                      <p className="text-xs font-medium text-gray-600">最高价格</p>
                      <p className="text-xl font-bold text-gray-900">{formatPrice(flightStats.max_price)}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="p-3">
                  <div className="flex items-center">
                    <DollarSign className="h-5 w-5 text-purple-600 flex-shrink-0" />
                    <div className="ml-2 min-w-0">
                      <p className="text-xs font-medium text-gray-600">平均价格</p>
                      <p className="text-xl font-bold text-gray-900">{formatPrice(flightStats.avg_price)}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : null}

          {/* 系统状态 */}
          <div className="grid grid-cols-1 lg:grid-cols-1 gap-3 mb-4">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">系统状态</CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Server className="h-4 w-4 mr-1.5 text-blue-600" />
                      <span className="text-sm">后端API</span>
                    </div>
                    <span className="text-green-600 font-medium text-sm">运行中</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Database className="h-4 w-4 mr-1.5 text-green-600" />
                      <span className="text-sm">数据库</span>
                    </div>
                    <span className="text-green-600 font-medium text-sm">正常</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Smartphone className="h-4 w-4 mr-1.5 text-purple-600" />
                      <span className="text-sm">Appium服务</span>
                    </div>
                    <span className="text-green-600 font-medium text-sm">运行中</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <Activity className="h-4 w-4 mr-1.5 text-orange-600" />
                      <span className="text-sm">Android模拟器</span>
                    </div>
                    <span className="text-green-600 font-medium text-sm">运行中</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* 快速操作 */}
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">快速操作</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="grid grid-cols-1 md:grid-cols-1 gap-3">
                <div className="space-y-1.5">
                  <h3 className="font-semibold text-sm">Docker Compose 操作</h3>
                  <div className="space-y-1.5">
                    <Button 
                      variant="outline" 
                      className="w-full justify-start text-xs h-7"
                      size="sm"
                      onClick={() => window.open('http://localhost:8000/docs', '_blank')}
                    >
                      📚 API文档
                    </Button>
                    <Button 
                      variant="outline" 
                      className="w-full justify-start text-xs h-7"
                      size="sm"
                      onClick={() => window.open('http://localhost:4723/inspector', '_blank')}
                    >
                      🔍 Appium Inspector
                    </Button>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
