import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { RefreshCw, CheckCircle, XCircle, Clock, BarChart3, ExternalLink, XOctagon } from 'lucide-react';
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
  airline?: string;
  run_mode?: string;
  schedule_time?: string;
  recurrence_interval_hours?: number;
  recurrence_end_type?: string;
  recurrence_max_runs?: number;
  recurrence_end_at?: string;
  recurrence_run_index?: number;
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
  const [runMode, setRunMode] = useState<'immediate' | 'scheduled' | 'recurring'>('immediate');
  const [scheduleTime, setScheduleTime] = useState('');
  const [recurrenceIntervalHours, setRecurrenceIntervalHours] = useState(24);
  const [recurrenceEndType, setRecurrenceEndType] = useState<'count' | 'end_time'>('count');
  const [recurrenceMaxRuns, setRecurrenceMaxRuns] = useState(10);
  const [recurrenceEndAt, setRecurrenceEndAt] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [progressMsg, setProgressMsg] = useState('');
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());
  const [cancellingId, setCancellingId] = useState<number | null>(null);
  const [cancellingAll, setCancellingAll] = useState(false);
  const isInitialLoad = useRef(true);

  // 获取任务记录（静默刷新，不重置loading状态）
  const fetchTasks = async (silent = false) => {
    try {
      if (!silent) {
        setLoading(true);
      }
      const response = await apiFetch('/api/tasks');
      if (response.ok) {
        const data = await response.json();
        // 直接更新任务列表，React 会智能地只更新变化的字段
        setTasks(data);
      }
    } catch (error) {
      console.error('获取任务记录失败:', error);
    } finally {
      if (!silent) {
        setLoading(false);
      }
      isInitialLoad.current = false;
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
      if (runMode === 'scheduled' && !scheduleTime) {
        setErrorMsg('请选择计划运行时间');
        return;
      }
      setCreating(true);
      console.log('Creating task with config:', { fromCity, toCity, departDate, platform, airline, runMode, scheduleTime });
      const body: Record<string, unknown> = {
        source: platform || '12306',
        task_type: 'flight_scraper',
        config: { fromCity, toCity, departDate },
        airline: airline,
        run_mode: runMode,
      };
      if (runMode === 'scheduled' && scheduleTime) {
        body.schedule_time = new Date(scheduleTime).toISOString();
      }
      if (runMode === 'recurring') {
        body.recurrence_interval_hours = recurrenceIntervalHours;
        body.recurrence_end_type = recurrenceEndType;
        if (recurrenceEndType === 'count') body.recurrence_max_runs = recurrenceMaxRuns;
        if (recurrenceEndType === 'end_time' && recurrenceEndAt) {
          body.recurrence_end_at = new Date(recurrenceEndAt).toISOString();
        }
      }
      const response = await apiFetch('/api/tasks/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
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
    
    // 设置自动刷新：每5秒静默刷新一次任务状态（不显示loading）
    const refreshInterval = setInterval(() => {
      fetchTasks(true); // 静默刷新
      fetchStatistics();
      setLastRefresh(new Date());
    }, 5000);
    
    // 清理定时器
    return () => clearInterval(refreshInterval);
  }, []);

  const getStatusBadge = (status: string, success: boolean) => {
    if (status === 'waiting') {
      return <Badge className="bg-amber-100 text-amber-800"><Clock className="h-3 w-3 mr-1" />排队中</Badge>;
    }
    if (status === 'running') {
      return <Badge className="bg-blue-100 text-blue-800"><Clock className="h-3 w-3 mr-1" />运行中</Badge>;
    }
    if (status === 'cancelled') {
      return <Badge className="bg-gray-100 text-gray-700"><XOctagon className="h-3 w-3 mr-1" />已取消</Badge>;
    }
    if (status === 'completed' && success) {
      return <Badge className="bg-green-100 text-green-800"><CheckCircle className="h-3 w-3 mr-1" />成功</Badge>;
    }
    if (status === 'failed' || (status === 'completed' && !success)) {
      return <Badge className="bg-red-100 text-red-800"><XCircle className="h-3 w-3 mr-1" />失败</Badge>;
    }
    return <Badge variant="secondary">{status || '未知'}</Badge>;
  };

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '-';
    const totalSeconds = Math.round(seconds);  // 四舍五入到秒
    const minutes = Math.floor(totalSeconds / 60);
    const remainingSeconds = totalSeconds % 60;
    return `${minutes}分${remainingSeconds}秒`;
  };

  const cancelAllTasks = async () => {
    if (cancellingAll) return;
    setCancellingAll(true);
    setErrorMsg('');
    try {
      const res = await apiFetch('/api/tasks/cancel-all', { method: 'PUT' });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        const n = data?.cancelled_count ?? 0;
        setProgressMsg(n > 0 ? `已取消 ${n} 个任务` : '没有可取消的任务');
        await fetchTasks();
      } else {
        setErrorMsg(typeof data?.detail === 'string' ? data.detail : `请求失败 ${res.status}`);
      }
    } catch (e) {
      console.error(e);
      setErrorMsg('全部取消失败');
    } finally {
      setCancellingAll(false);
    }
  };

  const cancelTask = async (taskId: number) => {
    if (cancellingId !== null) return;
    setCancellingId(taskId);
    try {
      const res = await apiFetch(`/api/tasks/${taskId}/cancel`, { method: 'PUT' });
      if (res.ok) {
        await fetchTasks();
      } else {
        const data = await res.json().catch(() => ({}));
        setErrorMsg(data?.detail || '取消失败');
      }
    } catch (e) {
      console.error(e);
      setErrorMsg('取消失败');
    } finally {
      setCancellingId(null);
    }
  };

  const formatRunMode = (mode?: string) => {
    if (!mode || mode === 'immediate') return '立即执行';
    if (mode === 'scheduled') return '定时任务';
    if (mode === 'recurring') return '循环任务';
    return mode;
  };

  const formatRecurrenceEnd = (task: TaskRecord) => {
    if (task.run_mode !== 'recurring') return null;
    if (task.recurrence_end_type === 'count' && task.recurrence_max_runs != null) {
      return `共 ${task.recurrence_max_runs} 次`;
    }
    if (task.recurrence_end_type === 'end_time' && task.recurrence_end_at) {
      return `截止 ${formatDateTime(task.recurrence_end_at)}`;
    }
    return null;
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
    <div className="container mx-auto px-4 py-2">
      <div className="mb-3">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">抓取任务记录</h1>
        <p className="text-sm text-gray-600">查看和管理航班信息抓取任务</p>
      </div>

      {progressMsg && (
        <div className="mb-3 p-2 rounded border bg-blue-50 text-blue-700 text-xs">{progressMsg}</div>
      )}

      {/* 统计信息 */}
      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-2 mb-4">
          <Card>
            <CardContent className="p-3">
              <div className="flex items-center">
                <BarChart3 className="h-5 w-5 text-blue-600 flex-shrink-0" />
                <div className="ml-2 min-w-0">
                  <p className="text-xs font-medium text-gray-600">总任务数</p>
                  <p className="text-xl font-bold text-gray-900">{statistics.total_tasks}</p>
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
                  <p className="text-xl font-bold text-gray-900">{statistics.success_rate}%</p>
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
                  <p className="text-xl font-bold text-gray-900">{formatDuration(statistics.avg_duration)}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-3">
              <div className="flex items-center">
                <RefreshCw className="h-5 w-5 text-purple-600 flex-shrink-0" />
                <div className="ml-2 min-w-0">
                  <p className="text-xs font-medium text-gray-600">总航班数</p>
                  <p className="text-xl font-bold text-gray-900">{statistics.total_flights}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 自动刷新状态指示器 */}
      <div className="mb-3 p-2 bg-blue-50 border border-blue-200 rounded">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <RefreshCw className="h-3 w-3 text-blue-600 mr-1.5 animate-spin" />
            <span className="text-xs text-blue-800">自动刷新已启用（每5秒）</span>
          </div>
          <span className="text-xs text-blue-600">
            最后更新: {lastRefresh.toLocaleTimeString()}
          </span>
        </div>
      </div>

      {/* 操作按钮 */}
      <div className="mb-4 flex gap-2 flex-wrap">
        <Button
          onClick={() => {
            setRunMode('immediate');
            setScheduleTime('');
            setRecurrenceEndAt('');
            setRecurrenceEndType('count');
            setRecurrenceMaxRuns(10);
            setRecurrenceIntervalHours(24);
            setShowDialog(true);
          }}
          className="flex items-center text-sm"
          size="sm"
        >
          新建任务（配置）
        </Button>
        <Button onClick={() => fetchTasks(false)} className="flex items-center text-sm" size="sm">
          <RefreshCw className="h-3 w-3 mr-1.5" />
          手动刷新
        </Button>
        <Button
          variant="outline"
          className="text-red-600 border-red-200 hover:bg-red-50 text-sm"
          size="sm"
          disabled={cancellingAll}
          onClick={cancelAllTasks}
        >
          {cancellingAll ? '取消中...' : '全部取消'}
        </Button>
        <Button variant="outline" asChild size="sm" className="text-sm">
          <Link to="/flight-results" className="flex items-center">
            <ExternalLink className="h-3 w-3 mr-1.5" />
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
              <div>
                <label className="block text-sm text-gray-700 mb-1">运行模式</label>
                <select value={runMode} onChange={e=>setRunMode(e.target.value as 'immediate'|'scheduled'|'recurring')} className="w-full border rounded px-3 py-2 text-sm">
                  <option value="immediate">立即执行</option>
                  <option value="scheduled">定时任务</option>
                  <option value="recurring">循环任务</option>
                </select>
              </div>
              {runMode === 'scheduled' && (
                <div>
                  <label className="block text-sm text-gray-700 mb-1">计划运行时间</label>
                  <input type="datetime-local" value={scheduleTime} onChange={e=>setScheduleTime(e.target.value)} className="w-full border rounded px-3 py-2 text-sm" />
                </div>
              )}
              {runMode === 'recurring' && (
                <>
                  <div>
                    <label className="block text-sm text-gray-700 mb-1">间隔（小时）</label>
                    <input type="number" min={1} value={recurrenceIntervalHours} onChange={e=>setRecurrenceIntervalHours(Number(e.target.value)||24)} className="w-full border rounded px-3 py-2 text-sm" />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-700 mb-1">终止方式</label>
                    <select value={recurrenceEndType} onChange={e=>setRecurrenceEndType(e.target.value as 'count'|'end_time')} className="w-full border rounded px-3 py-2 text-sm">
                      <option value="count">按循环次数</option>
                      <option value="end_time">按截止时间</option>
                    </select>
                  </div>
                  {recurrenceEndType === 'count' && (
                    <div>
                      <label className="block text-sm text-gray-700 mb-1">最大执行次数</label>
                      <input type="number" min={1} value={recurrenceMaxRuns} onChange={e=>setRecurrenceMaxRuns(Number(e.target.value)||10)} className="w-full border rounded px-3 py-2 text-sm" />
                    </div>
                  )}
                  {recurrenceEndType === 'end_time' && (
                    <div>
                      <label className="block text-sm text-gray-700 mb-1">截止时间</label>
                      <input type="datetime-local" value={recurrenceEndAt} onChange={e=>setRecurrenceEndAt(e.target.value)} className="w-full border rounded px-3 py-2 text-sm" />
                    </div>
                  )}
                </>
              )}
            </div>
            <div className="mt-6 flex justify-end gap-3">
              <Button variant="outline" onClick={()=>setShowDialog(false)}>取消</Button>
              <Button onClick={createTask} disabled={creating}>{creating ? '创建中...' : '创建'}</Button>
            </div>
          </div>
        </div>
      )}

      {/* 任务列表 */}
      <div className="space-y-2">
        {loading && isInitialLoad.current ? (
          <div className="text-center py-6">
            <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2" />
            <p className="text-sm text-gray-600">加载中...</p>
          </div>
        ) : tasks.length === 0 ? (
          <Card>
            <CardContent className="p-6 text-center">
              <BarChart3 className="h-10 w-10 text-gray-400 mx-auto mb-2" />
              <p className="text-sm text-gray-600">暂无任务记录</p>
            </CardContent>
          </Card>
        ) : (
          tasks.map((task) => (
            <Card key={task.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                      <div className="min-w-0">
                        <h3 className="text-base font-semibold truncate">{task.task_name}</h3>
                        <span className="text-xs text-gray-500">任务编号: #{task.id}</span>
                      </div>
                      {getStatusBadge(task.status, task.success)}
                    </div>
                    
                    {(task.current_step && (task.status === 'running' || task.status === 'waiting')) && (
                      <div className={`mb-2 p-1.5 rounded border ${task.status === 'waiting' ? 'bg-amber-50 border-amber-200' : 'bg-blue-50 border-blue-200'}`}>
                        <p className={`text-xs ${task.status === 'waiting' ? 'text-amber-700' : 'text-blue-600'}`}>
                          <span className="font-medium">当前步骤:</span> {task.current_step}
                        </p>
                      </div>
                    )}

                    <div className="mb-2 grid grid-cols-2 md:grid-cols-4 gap-2 text-xs text-gray-600">
                      <div>
                        <span className="font-medium">运行模式:</span>
                        <p className="truncate">{formatRunMode(task.run_mode)}</p>
                      </div>
                      {(task.run_mode === 'scheduled' || task.run_mode === 'recurring') && task.schedule_time && (
                        <div>
                          <span className="font-medium">计划运行时间:</span>
                          <p className="truncate">{formatDateTime(task.schedule_time)}</p>
                        </div>
                      )}
                      {task.run_mode === 'recurring' && task.recurrence_interval_hours != null && (
                        <div>
                          <span className="font-medium">间隔时长:</span>
                          <p className="truncate">每 {task.recurrence_interval_hours} 小时</p>
                        </div>
                      )}
                      {task.run_mode === 'recurring' && formatRecurrenceEnd(task) && (
                        <div>
                          <span className="font-medium">终止方式:</span>
                          <p className="truncate">{formatRecurrenceEnd(task)}</p>
                        </div>
                      )}
                    </div>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs text-gray-600">
                      <div>
                        <span className="font-medium">开始时间:</span>
                        <p className="truncate">{formatDateTime(task.start_time)}</p>
                      </div>
                      
                      <div>
                        <span className="font-medium">结束时间:</span>
                        <p className="truncate">{formatDateTime(task.end_time)}</p>
                      </div>
                      
                      <div>
                        <span className="font-medium">执行时长:</span>
                        <p className="truncate">{formatDuration(task.duration)}</p>
                      </div>
                      
                      <div>
                        <span className="font-medium">航班数量:</span>
                        <p className="text-green-600 font-semibold truncate">{task.flights_count}</p>
                      </div>
                    </div>
                    
                    {task.error_message && (
                      <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded">
                        <p className="text-xs text-red-600 line-clamp-2">
                          <span className="font-medium">错误信息:</span> {task.error_message}
                        </p>
                      </div>
                    )}
                  </div>
                  
                  <div className="flex flex-col gap-1.5 flex-shrink-0">
                    {(task.status === 'running' || task.status === 'waiting') && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-red-600 border-red-200 hover:bg-red-50 text-xs px-2 py-1 h-auto"
                        disabled={cancellingId === task.id}
                        onClick={() => cancelTask(task.id)}
                      >
                        {cancellingId === task.id ? '取消中...' : '取消任务'}
                      </Button>
                    )}
                    {task.success && task.flights_count > 0 && (
                      <Button asChild size="sm" className="flex items-center text-xs px-2 py-1 h-auto">
                        <Link to="/flight-results">
                          <ExternalLink className="h-3 w-3 mr-1" />
                          查看结果
                        </Link>
                      </Button>
                    )}
                    <Button variant="outline" size="sm" asChild className="text-xs px-2 py-1 h-auto">
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
