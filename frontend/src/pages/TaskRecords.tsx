import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { RefreshCw, CheckCircle, XCircle, Clock, BarChart3, ExternalLink } from 'lucide-react';
import { Link } from 'react-router-dom';
import { apiFetch } from '@/lib/api';

interface TaskRecord {
  id: number;
  task_name: string;
  task_type: string;
  status: string;
  current_step?: string;
  start_time: string;
  end_time?: string;
  duration?: number;
  success: boolean;
  flights_count: number;
  error_message?: string;
  source: string;
  config?: string;
  notes?: string;
  created_at: string;
}

interface TaskStatistics {
  total_tasks: number;
  successful_tasks: number;
  failed_tasks: number;
  running_tasks: number;
  success_rate: number;
  avg_duration: number;
  total_flights: number;
}

const TaskRecords: React.FC = () => {
  const [tasks, setTasks] = useState<TaskRecord[]>([]);
  const [statistics, setStatistics] = useState<TaskStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [showDialog, setShowDialog] = useState(false);
  const [fromCity, setFromCity] = useState('北京');
  const [toCity, setToCity] = useState('上海');
  const [departDate, setDepartDate] = useState<string>(() => new Date().toISOString().slice(0,10));
  const [platform, setPlatform] = useState('12306');
  const [airline, setAirline] = useState('深圳航空');
  const [errorMsg, setErrorMsg] = useState('');
  const [progressMsg, setProgressMsg] = useState('');
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  // 获取任务记录
  const fetchTasks = async () => {
    try {
      setLoading(true);
      const response = await apiFetch('/api/tasks');
      if (response.ok) {
        const data = await response.json();
        setTasks(data);
      }
    } catch (error) {
      console.error('获取任务记录失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const pollTaskUntilDone = (taskId: number) => {
    setProgressMsg('任务已创建，正在执行...');
    const timer = setInterval(async () => {
      try {
        const res = await apiFetch('/api/tasks/');
        if (res.ok) {
          const list: TaskRecord[] = await res.json();
          const t = list.find(x => x.id === taskId);
          if (t && t.status !== 'running') {
            clearInterval(timer);
            setProgressMsg(t.success ? '任务完成' : '任务失败');
          }
        }
      } catch {}
    }, 2000);
  };

  const createTask = async () => {
    try {
      setErrorMsg('');
      setCreating(true);
      console.log('Creating task with config:', { fromCity, toCity, departDate, platform, airline });
      const response = await apiFetch('/api/tasks/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          source: platform || '12306', 
          task_type: 'flight_scraper',
          config: { fromCity, toCity, departDate },
          airline: airline
        })
      });
      if (!response.ok) {
        // 尝试获取详细错误信息
        let errorDetail = `创建失败：${response.status}`;
        try {
          const errorData = await response.json();
          if (errorData.detail) {
            errorDetail = `创建失败：${errorData.detail}`;
          }
        } catch (e) {
          // 如果响应不是JSON，使用默认错误信息
        }
        setErrorMsg(errorDetail);
        return;
      }
      const created: TaskRecord = await response.json();
      setShowDialog(false);
      await fetchTasks();
      pollTaskUntilDone(created.id);
    } catch (error) {
      console.error('新建任务失败:', error);
      setErrorMsg('网络或服务错误');
    } finally {
      setCreating(false);
    }
  };

  // 获取统计信息
  const fetchStatistics = async () => {
    try {
      const response = await apiFetch('/api/tasks/stats');
      if (response.ok) {
        const data = await response.json();
        setStatistics(data);
      }
    } catch (error) {
      console.error('获取统计信息失败:', error);
    }
  };

  useEffect(() => {
    fetchTasks();
    fetchStatistics();
    
    // 设置自动刷新：每5秒刷新一次任务状态
    const refreshInterval = setInterval(() => {
      fetchTasks();
      fetchStatistics();
      setLastRefresh(new Date());
    }, 5000);
    
    // 清理定时器
    return () => clearInterval(refreshInterval);
  }, []);

  const getStatusBadge = (status: string, success: boolean) => {
    if (status === 'running') {
      return <Badge className="bg-blue-100 text-blue-800"><Clock className="h-3 w-3 mr-1" />运行中</Badge>;
    } else if (success) {
      return <Badge className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />成功</Badge>;
    } else {
      return <Badge className="bg-red-100 text-red-800"><XCircle className="h-3 w-3 mr-1" />失败</Badge>;
    }
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '-';
    const totalSeconds = Math.round(seconds);  // 四舍五入到秒
    const minutes = Math.floor(totalSeconds / 60);
    const remainingSeconds = totalSeconds % 60;
    return `${minutes}分${remainingSeconds}秒`;
  };

  const formatDateTime = (dateTime?: string) => {
    if (!dateTime) return '-';
    // 确保正确处理UTC时间，转换为本地时间显示
    const date = new Date(dateTime);
    return date.toLocaleString('zh-CN', {
      timeZone: 'Asia/Shanghai',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">抓取任务记录</h1>
        <p className="text-gray-600">查看和管理航班信息抓取任务</p>
      </div>

      {progressMsg && (
        <div className="mb-4 p-3 rounded border bg-blue-50 text-blue-700 text-sm">{progressMsg}</div>
      )}

      {/* 统计信息 */}
      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <BarChart3 className="h-8 w-8 text-blue-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">总任务数</p>
                  <p className="text-2xl font-bold text-gray-900">{statistics.total_tasks}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <CheckCircle className="h-8 w-8 text-green-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">成功率</p>
                  <p className="text-2xl font-bold text-gray-900">{statistics.success_rate}%</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <Clock className="h-8 w-8 text-orange-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">平均时长</p>
                  <p className="text-2xl font-bold text-gray-900">{formatDuration(statistics.avg_duration)}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center">
                <RefreshCw className="h-8 w-8 text-purple-600" />
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">总航班数</p>
                  <p className="text-2xl font-bold text-gray-900">{statistics.total_flights}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 自动刷新状态指示器 */}
      <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <RefreshCw className="h-4 w-4 text-blue-600 mr-2 animate-spin" />
            <span className="text-sm text-blue-800">自动刷新已启用（每5秒）</span>
          </div>
          <span className="text-xs text-blue-600">
            最后更新: {lastRefresh.toLocaleTimeString()}
          </span>
        </div>
      </div>

      {/* 操作按钮 */}
      <div className="mb-6 flex gap-4">
        <Button onClick={() => setShowDialog(true)} className="flex items-center">
          新建任务（配置）
        </Button>
        <Button onClick={fetchTasks} className="flex items-center">
          <RefreshCw className="h-4 w-4 mr-2" />
          手动刷新
        </Button>
        <Button variant="outline" asChild>
          <Link to="/flight-results" className="flex items-center">
            <ExternalLink className="h-4 w-4 mr-2" />
            查看航班结果
          </Link>
        </Button>
      </div>

      {/* 任务设置弹窗 */}
      {showDialog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-lg shadow-lg w-full max-w-md p-6">
            <h2 className="text-xl font-semibold mb-4">新建抓取任务</h2>
            {errorMsg && (
              <div className="mb-3 text-sm text-red-600">{errorMsg}</div>
            )}
            <div className="space-y-4">
              <div>
                <label className="block text-sm text-gray-700 mb-1">出发城市</label>
                <input value={fromCity} onChange={e=>setFromCity(e.target.value)} className="w-full border rounded px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-sm text-gray-700 mb-1">到达城市</label>
                <input value={toCity} onChange={e=>setToCity(e.target.value)} className="w-full border rounded px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-sm text-gray-700 mb-1">出发日期</label>
                <input type="date" value={departDate} onChange={e=>setDepartDate(e.target.value)} className="w-full border rounded px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-sm text-gray-700 mb-1">查询平台</label>
                <select value={platform} onChange={e=>setPlatform(e.target.value)} className="w-full border rounded px-3 py-2 text-sm">
                  <option value="12306">12306</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-700 mb-1">指定航空公司</label>
                <select value={airline} onChange={e=>setAirline(e.target.value)} className="w-full border rounded px-3 py-2 text-sm">
                  <option value="全部">全部</option>
                  <option value="深圳航空">深圳航空</option>
                  <option value="中国国际航空">中国国际航空</option>
                  <option value="中国东方航空">中国东方航空</option>
                  <option value="中国南方航空">中国南方航空</option>
                  <option value="海南航空">海南航空</option>
                  <option value="四川航空">四川航空</option>
                  <option value="春秋航空">春秋航空</option>
                  <option value="首都航空">首都航空</option>
                  <option value="吉祥航空">吉祥航空</option>
                  <option value="山东航空">山东航空</option>
                  <option value="厦门航空">厦门航空</option>
                  <option value="华夏航空">华夏航空</option>
                  <option value="长龙航空">长龙航空</option>
                  <option value="成都航空">成都航空</option>
                  <option value="瑞丽航空">瑞丽航空</option>
                  <option value="北部湾航空">北部湾航空</option>
                  <option value="福州航空">福州航空</option>
                  <option value="昆明航空">昆明航空</option>
                  <option value="龙江航空">龙江航空</option>
                  <option value="重庆航空">重庆航空</option>
                </select>
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-3">
              <Button variant="outline" onClick={()=>setShowDialog(false)}>取消</Button>
              <Button onClick={createTask} disabled={creating}>{creating ? '创建中...' : '创建'}</Button>
            </div>
          </div>
        </div>
      )}

      {/* 任务列表 */}
      <div className="space-y-4">
        {loading ? (
          <div className="text-center py-8">
            <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
            <p className="text-gray-600">加载中...</p>
          </div>
        ) : tasks.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center">
              <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-600">暂无任务记录</p>
            </CardContent>
          </Card>
        ) : (
          tasks.map((task) => (
            <Card key={task.id} className="hover:shadow-lg transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-4 mb-2">
                      <div>
                        <h3 className="text-lg font-semibold">{task.task_name}</h3>
                        <span className="text-sm text-gray-500">任务编号: #{task.id}</span>
                      </div>
                      {getStatusBadge(task.status, task.success)}
                    </div>
                    
                    {task.current_step && task.status === 'running' && (
                      <div className="mb-3 p-2 bg-blue-50 border border-blue-200 rounded">
                        <p className="text-sm text-blue-600">
                          <span className="font-medium">当前步骤:</span> {task.current_step}
                        </p>
                      </div>
                    )}
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600">
                      <div>
                        <span className="font-medium">开始时间:</span>
                        <p>{formatDateTime(task.start_time)}</p>
                      </div>
                      
                      <div>
                        <span className="font-medium">结束时间:</span>
                        <p>{formatDateTime(task.end_time)}</p>
                      </div>
                      
                      <div>
                        <span className="font-medium">执行时长:</span>
                        <p>{formatDuration(task.duration)}</p>
                      </div>
                      
                      <div>
                        <span className="font-medium">航班数量:</span>
                        <p className="text-green-600 font-semibold">{task.flights_count}</p>
                      </div>
                    </div>
                    
                    {task.error_message && (
                      <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded">
                        <p className="text-sm text-red-600">
                          <span className="font-medium">错误信息:</span> {task.error_message}
                        </p>
                      </div>
                    )}
                  </div>
                  
                  <div className="ml-4 flex flex-col gap-2">
                    {task.success && task.flights_count > 0 && (
                      <Button asChild size="sm" className="flex items-center">
                        <Link to="/flight-results">
                          <ExternalLink className="h-4 w-4 mr-1" />
                          查看结果
                        </Link>
                      </Button>
                    )}
                    
                    <Button variant="outline" size="sm" asChild>
                      <Link to={`/tasks/${task.id}`}>
                        查看详情
                      </Link>
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};

export default TaskRecords;
