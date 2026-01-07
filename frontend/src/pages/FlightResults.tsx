import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { RefreshCw, Search, Plane, DollarSign } from 'lucide-react';
import { apiFetch } from '@/lib/api';

interface FlightResult {
  id: number;
  airline: string;
  flight_number: string;
  is_shared_flight?: string;
  aircraft_type?: string;
  departure_date?: string;
  departure_time: string;
  departure_airport: string;
  departure_city?: string;
  arrival_time: string;
  arrival_airport: string;
  arrival_city?: string;
  departure_terminal?: string;
  arrival_terminal?: string;
  flight_duration?: string;
  has_stopover?: string;
  stopover_city?: string;
  stopover_airport?: string;
  price: number;
  currency: string;
  cabin_class?: string;
  discount_rate?: string;
  original_price?: number;
  task_id?: number;
  scrape_time: string;
  source: string;
  status: string;
  notes?: string;
}

interface FlightStatistics {
  total_flights: number;
  min_price: number;
  max_price: number;
  avg_price: number;
}

const FlightResults: React.FC = () => {
  const [flights, setFlights] = useState<FlightResult[]>([]);
  const [statistics, setStatistics] = useState<FlightStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedFlights, setSelectedFlights] = useState<number[]>([]);
  const [viewMode, setViewMode] = useState<'list' | 'compare'>('list');
  const [searchParams, setSearchParams] = useState({
    minPrice: '',
    maxPrice: '',
    airline: '',
    flightNumber: '',
    departureCity: '',
    arrivalCity: '',
    taskId: '',
    limit: 50
  });
  const [hasTaskIdFilter, setHasTaskIdFilter] = useState(false);
  const [sortBy, setSortBy] = useState<'price' | 'time'>('price');

  // 获取航班数据
  const fetchFlights = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      
      if (searchParams.minPrice) params.append('min_price', searchParams.minPrice);
      if (searchParams.maxPrice) params.append('max_price', searchParams.maxPrice);
      if (searchParams.airline) params.append('airline', searchParams.airline);
      if (searchParams.flightNumber) params.append('flight_number', searchParams.flightNumber);
      if (searchParams.departureCity) params.append('departure_city', searchParams.departureCity);
      if (searchParams.arrivalCity) params.append('arrival_city', searchParams.arrivalCity);
      let hasValidTaskId = false;
      if (searchParams.taskId) {
        // 处理字符串或数字类型的 taskId
        const taskIdStr = String(searchParams.taskId).trim();
        if (taskIdStr !== '') {
          const taskIdNum = parseInt(taskIdStr, 10);
          if (!isNaN(taskIdNum) && taskIdNum > 0) {
            params.append('task_id', taskIdNum.toString());
            hasValidTaskId = true;
            console.log(`🔍 前端传递 task_id: ${taskIdNum}`);
          } else {
            console.log(`⚠️ 前端 taskId 无效: ${taskIdStr}`);
          }
        }
      } else {
        console.log('ℹ️ 前端未传递 taskId');
      }
      setHasTaskIdFilter(hasValidTaskId);
      params.append('limit', searchParams.limit.toString());
      params.append('sort_by', sortBy);

      const response = await apiFetch(`/api/flights/?${params.toString()}`);
      if (response.ok) {
        const data = await response.json();
        // 确保 data 是数组，如果是空结果，设置为空数组
        setFlights(Array.isArray(data) ? data : []);
      } else {
        // 如果请求失败，清空结果列表
        setFlights([]);
      }
    } catch (error) {
      console.error('获取航班数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  // 获取统计信息
  const fetchStatistics = async () => {
    try {
      const response = await apiFetch('/api/flights/statistics');
      if (response.ok) {
        const data = await response.json();
        setStatistics(data);
      }
    } catch (error) {
      console.error('获取统计信息失败:', error);
    }
  };

  useEffect(() => {
    fetchFlights();
    fetchStatistics();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSearch = () => {
    fetchFlights();
  };

  const handleReset = () => {
    setSearchParams({
      minPrice: '',
      maxPrice: '',
      airline: '',
      flightNumber: '',
      departureCity: '',
      arrivalCity: '',
      taskId: '',
      limit: 50
    });
    setHasTaskIdFilter(false);
    fetchFlights();
  };

  const toggleFlightSelection = (flightId: number) => {
    setSelectedFlights(prev => 
      prev.includes(flightId) 
        ? prev.filter(id => id !== flightId)
        : [...prev, flightId]
    );
  };

  const clearSelection = () => {
    setSelectedFlights([]);
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('zh-CN', {
      style: 'currency',
      currency: 'CNY'
    }).format(price);
  };

  const formatTime = (time: string) => {
    return time;
  };

  const formatDepartureDate = (date: string) => {
    if (!date) return '';
    // 处理不同格式的日期
    if (date.includes('月') && date.includes('日')) {
      // 格式：12月27日
      return date;
    } else if (date.includes('-')) {
      // 格式：2025-12-27
      const parts = date.split('-');
      if (parts.length === 3) {
        const [, month, day] = parts;
        return `${parseInt(month, 10)}月${parseInt(day, 10)}日`;
      }
    } else if (date.includes('/')) {
      // 格式：12/27
      const parts = date.split('/');
      if (parts.length === 2) {
        const [month, day] = parts;
        return `${parseInt(month, 10)}月${parseInt(day, 10)}日`;
      }
    }
    return date;
  };

  // 机场代号到名称的转换
  const getAirportName = (code: string) => {
    const airportMap: { [key: string]: string } = {
      // 常见三字码
      'PEK': '北京首都国际机场',
      'PKX': '北京大兴国际机场',
      'SHA': '上海虹桥国际机场',
      'PVG': '上海浦东国际机场',
      'CAN': '广州白云国际机场',
      'SZX': '深圳宝安国际机场',
      'CTU': '成都双流国际机场',
      'TFU': '成都天府国际机场',
      'XIY': '西安咸阳国际机场',
      'KMG': '昆明长水国际机场',
      'HGH': '杭州萧山国际机场',
      'NKG': '南京禄口国际机场',
      'TSN': '天津滨海国际机场',
      'DLC': '大连周水子国际机场',
      'URC': '乌鲁木齐地窝堡国际机场',
      'WUH': '武汉天河国际机场',
      'CSX': '长沙黄花国际机场',
      'XMN': '厦门高崎国际机场',
      'FOC': '福州长乐国际机场',
      'TAO': '青岛胶东国际机场',
      'CGO': '郑州新郑国际机场',
      // 页面中出现的别名/特殊代码映射
      'UTF': '乌鲁木齐地窝堡国际机场',
      'QAA': '北京首都国际机场',
      'AAB': '北京首都国际机场',
      'JRU': '上海虹桥国际机场',
      'CGJ': '上海浦东国际机场',
      'BKU': '广州白云国际机场',
      'DIR': '深圳宝安国际机场',
      'AAA': '成都双流国际机场',
      'AAS': '西安咸阳国际机场',
      'UVO': '昆明长水国际机场'
    };
    return airportMap[code] || `${code}机场`;
  };

  // 计算飞行时长
  const calculateFlightDuration = (departureTime: string, arrivalTime: string) => {
    if (!departureTime || !arrivalTime) return '';
    try {
      const depParts = departureTime.split(':');
      const arrParts = arrivalTime.split(':');
      if (depParts.length < 2 || arrParts.length < 2) return '';
      
      const depHour = parseInt(depParts[0], 10);
      const depMin = parseInt(depParts[1], 10);
      const arrHour = parseInt(arrParts[0], 10);
      const arrMin = parseInt(arrParts[1], 10);
      
      if (isNaN(depHour) || isNaN(depMin) || isNaN(arrHour) || isNaN(arrMin)) {
        return '';
      }
      
      let depMinutes = depHour * 60 + depMin;
      let arrMinutes = arrHour * 60 + arrMin;
      
      // 处理跨天情况
      if (arrMinutes < depMinutes) {
        arrMinutes += 24 * 60;
      }
      
      const durationMinutes = arrMinutes - depMinutes;
      const hours = Math.floor(durationMinutes / 60);
      const minutes = durationMinutes % 60;
      
      if (hours > 0) {
        return `${hours}小时${minutes}分钟`;
      } else {
        return `${minutes}分钟`;
      }
    } catch (error) {
      return '';
    }
  };

  const getAirlineColor = (airline: string) => {
    const colors = {
      '中国国际航空': 'bg-blue-100 text-blue-800',
      '中国东方航空': 'bg-red-100 text-red-800',
      '中国南方航空': 'bg-green-100 text-green-800',
      '海南航空': 'bg-purple-100 text-purple-800',
      '四川航空': 'bg-orange-100 text-orange-800',
      '春秋航空': 'bg-pink-100 text-pink-800',
      '首都航空': 'bg-indigo-100 text-indigo-800',
      '吉祥航空': 'bg-yellow-100 text-yellow-800'
    };
    return colors[airline as keyof typeof colors] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 紧凑的头部 */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="container mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-gray-900">航班查询结果</h1>
              <p className="text-sm text-gray-600">实时航班信息，按价格从低到高排列</p>
            </div>
            <div className="flex items-center space-x-4">
              {statistics && (
                <div className="flex items-center space-x-6 text-sm">
                  <div className="flex items-center space-x-1">
                    <Plane className="h-4 w-4 text-blue-600" />
                    <span className="text-gray-600">共</span>
                    <span className="font-semibold text-blue-600">{statistics.total_flights}</span>
                    <span className="text-gray-600">班</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <DollarSign className="h-4 w-4 text-green-600" />
                    <span className="text-gray-600">最低</span>
                    <span className="font-semibold text-green-600">{formatPrice(statistics.min_price)}</span>
                  </div>
                </div>
              )}
              <Button variant="outline" size="sm" onClick={fetchFlights} className="flex items-center">
                <RefreshCw className="h-4 w-4 mr-1" />
                刷新
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-4">
        {/* 紧凑的筛选器 */}
        <Card className="mb-4">
          <CardContent className="p-4">
            <div className="flex flex-wrap items-center gap-4">
              <div className="flex items-center space-x-2">
                <Label className="text-sm font-medium text-gray-700">价格范围:</Label>
                <Input
                  type="number"
                  placeholder="最低"
                  value={searchParams.minPrice}
                  onChange={(e) => setSearchParams({...searchParams, minPrice: e.target.value})}
                  className="w-20 h-8 text-sm"
                />
                <span className="text-gray-500">-</span>
                <Input
                  type="number"
                  placeholder="最高"
                  value={searchParams.maxPrice}
                  onChange={(e) => setSearchParams({...searchParams, maxPrice: e.target.value})}
                  className="w-20 h-8 text-sm"
                />
              </div>
              
              <div className="flex items-center space-x-2">
                <Label className="text-sm font-medium text-gray-700">航空公司:</Label>
                <Input
                  placeholder="输入航空公司"
                  value={searchParams.airline}
                  onChange={(e) => setSearchParams({...searchParams, airline: e.target.value})}
                  className="w-32 h-8 text-sm"
                />
              </div>
              
              <div className="flex items-center space-x-2">
                <Label className="text-sm font-medium text-gray-700">航班号:</Label>
                <Input
                  placeholder="如: CA1234"
                  value={searchParams.flightNumber}
                  onChange={(e) => setSearchParams({...searchParams, flightNumber: e.target.value})}
                  className="w-28 h-8 text-sm"
                />
              </div>
              
              <div className="flex items-center space-x-2">
                <Label className="text-sm font-medium text-gray-700">出发城市:</Label>
                <Input
                  placeholder="如: 上海"
                  value={searchParams.departureCity}
                  onChange={(e) => setSearchParams({...searchParams, departureCity: e.target.value})}
                  className="w-24 h-8 text-sm"
                />
              </div>
              
              <div className="flex items-center space-x-2">
                <Label className="text-sm font-medium text-gray-700">到达城市:</Label>
                <Input
                  placeholder="如: 北京"
                  value={searchParams.arrivalCity}
                  onChange={(e) => setSearchParams({...searchParams, arrivalCity: e.target.value})}
                  className="w-24 h-8 text-sm"
                />
              </div>
              
              <div className="flex items-center space-x-2">
                <Label className="text-sm font-medium text-gray-700">任务编号:</Label>
                <Input
                  type="number"
                  placeholder="如: 209"
                  value={searchParams.taskId}
                  onChange={(e) => setSearchParams({...searchParams, taskId: e.target.value})}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleSearch();
                    }
                  }}
                  className="w-24 h-8 text-sm"
                />
                {searchParams.taskId && (
                  <Button 
                    onClick={handleSearch} 
                    size="sm" 
                    className="h-8 px-3 bg-blue-600 hover:bg-blue-700"
                  >
                    查询
                  </Button>
                )}
              </div>
              
              <div className="flex items-center space-x-2">
                <Label className="text-sm font-medium text-gray-700">显示:</Label>
                <Select
                  value={searchParams.limit.toString()}
                  onValueChange={(value: string) => setSearchParams({...searchParams, limit: parseInt(value)})}
                >
                  <SelectTrigger className="w-20 h-8 text-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="20">20</SelectItem>
                    <SelectItem value="50">50</SelectItem>
                    <SelectItem value="100">100</SelectItem>
                    <SelectItem value="200">200</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="flex items-center space-x-2">
                <Label className="text-sm font-medium text-gray-700">排序:</Label>
                <Select
                  value={sortBy}
                  onValueChange={(value: 'price' | 'time') => setSortBy(value)}
                >
                  <SelectTrigger className="w-24 h-8 text-sm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="price">价格</SelectItem>
                    <SelectItem value="time">时间</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="flex items-center space-x-2">
                <Button onClick={handleSearch} size="sm" className="h-8">
                  <Search className="h-4 w-4 mr-1" />
                  搜索
                </Button>
                <Button variant="outline" onClick={handleReset} size="sm" className="h-8">
                  重置
                </Button>
              </div>
              
              {/* 视图模式切换 */}
              <div className="flex items-center space-x-2 ml-4">
                <Button
                  variant={viewMode === 'list' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewMode('list')}
                  className="h-8"
                >
                  列表
                </Button>
                <Button
                  variant={viewMode === 'compare' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewMode('compare')}
                  className="h-8"
                >
                  对比
                </Button>
              </div>
              
              {/* 选择状态 */}
              {selectedFlights.length > 0 && (
                <div className="flex items-center space-x-2 ml-4">
                  <span className="text-sm text-gray-600">
                    已选择 {selectedFlights.length} 个航班
                  </span>
                  <Button variant="outline" size="sm" onClick={clearSelection} className="h-8">
                    清除
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* 对比视图 */}
        {viewMode === 'compare' && selectedFlights.length > 0 && (
          <Card className="mb-4 bg-blue-50 border-blue-200">
            <CardContent className="p-4">
              <h3 className="text-lg font-semibold text-blue-900 mb-3">航班对比</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {selectedFlights.map(flightId => {
                  const flight = flights.find(f => f.id === flightId);
                  if (!flight) return null;
                  
                  return (
                    <div key={flightId} className="bg-white p-3 rounded-lg border">
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <Badge className={`${getAirlineColor(flight.airline)} text-xs`}>
                            {flight.airline}
                          </Badge>
                          <span className="ml-2 font-mono text-sm">{flight.flight_number}</span>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => toggleFlightSelection(flightId)}
                          className="h-6 w-6 p-0"
                        >
                          ×
                        </Button>
                      </div>
                      <div className="text-center">
                        <div className="text-lg font-bold text-green-600">
                          {formatPrice(flight.price)}
                        </div>
                        <div className="text-xs text-gray-600">
                          {flight.departure_time} - {flight.arrival_time}
                        </div>
                        <div className="text-xs text-gray-500">
                          {flight.flight_duration || calculateFlightDuration(flight.departure_time, flight.arrival_time)}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        )}

        {/* 航班列表 - 按任务分组显示 */}
        <div className="space-y-4">
          {loading ? (
            <div className="text-center py-12">
              <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-600" />
              <p className="text-gray-600">正在加载航班信息...</p>
            </div>
          ) : flights.length === 0 ? (
            <Card className="border-dashed">
              <CardContent className="p-12 text-center">
                <Plane className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">暂无航班数据</h3>
                <p className="text-gray-500">请尝试调整搜索条件或稍后再试</p>
              </CardContent>
            </Card>
          ) : (
            (() => {
              // 按任务分组航班
              // 如果指定了 task_id 过滤，则过滤掉没有 task_id 的航班（未分类航班）
              const groupedFlights = flights.reduce((groups, flight) => {
                const taskId = flight.task_id;
                // 如果指定了 task_id 过滤，跳过未分类的航班
                if (hasTaskIdFilter && (taskId === null || taskId === undefined)) {
                  console.log(`⚠️ 跳过未分类航班（指定了 task_id 过滤）`);
                  return groups;
                }
                // 检查：task_id 不能是 null 或 undefined（但允许 0，因为有些任务ID可能是0）
                if (taskId === null || taskId === undefined) {
                  // 如果没有task_id，使用'未分类'作为分组
                  const ungroupedKey = '未分类';
                  if (!groups[ungroupedKey]) {
                    groups[ungroupedKey] = [];
                  }
                  groups[ungroupedKey].push(flight);
                } else {
                  if (!groups[taskId]) {
                    groups[taskId] = [];
                  }
                  groups[taskId].push(flight);
                }
                return groups;
              }, {} as Record<string | number, FlightResult[]>);

              // 如果分组后没有结果，显示提示信息
              if (Object.keys(groupedFlights).length === 0) {
                return (
                  <Card className="border-dashed">
                    <CardContent className="p-12 text-center">
                      <Plane className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">暂无航班数据</h3>
                      <p className="text-gray-500">
                        {hasTaskIdFilter 
                          ? `未找到任务编号 ${searchParams.taskId} 的航班数据，请尝试调整搜索条件或稍后再试`
                          : '请尝试调整搜索条件或稍后再试'}
                      </p>
                    </CardContent>
                  </Card>
                );
              }

              return Object.entries(groupedFlights).map(([taskId, taskFlights]) => (
                <div key={taskId} className="space-y-2">
                  {/* 任务标题 */}
                  <div className="flex items-center justify-between bg-blue-50 border-2 border-blue-300 px-4 py-3 rounded-lg mb-2 shadow-sm">
                    <div className="flex items-center space-x-3">
                      <span className="text-lg font-bold text-blue-800 bg-blue-100 px-3 py-1 rounded-md border border-blue-300">
                        {taskId === '未分类' ? '未分类航班' : `任务 #${taskId}`}
                      </span>
                      <span className="text-sm text-blue-700 font-semibold">
                        {taskFlights.length} 个航班
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs text-gray-600 font-medium">抓取时间:</span>
                      <span className="text-xs text-gray-700 font-semibold">
                        {taskFlights[0]?.scrape_time && 
                          new Date(taskFlights[0].scrape_time).toLocaleString('zh-CN', {
                            timeZone: 'Asia/Shanghai',
                            year: 'numeric',
                            month: '2-digit',
                            day: '2-digit',
                            hour: '2-digit',
                            minute: '2-digit',
                            second: '2-digit'
                          })
                        }
                      </span>
                    </div>
                  </div>
                  
                  {/* 该任务的航班列表 */}
                  <div className="space-y-2">
                    {taskFlights.map((flight) => (
              <Card 
                key={flight.id} 
                className={`hover:shadow-md transition-all duration-200 border-l-4 ${
                  selectedFlights.includes(flight.id) 
                    ? 'border-l-green-500 bg-green-50' 
                    : 'border-l-blue-500'
                } ${viewMode === 'compare' ? 'cursor-pointer' : ''}`}
                onClick={() => viewMode === 'compare' && toggleFlightSelection(flight.id)}
              >
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    {/* 左侧：航班信息 */}
                    <div className="flex-1">
                      <div className="flex items-center space-x-4 mb-3">
                        {/* 任务编号 - 优先显示 */}
                        {flight.task_id != null && flight.task_id !== undefined && (
                          <Badge className="text-xs px-2 py-1 bg-blue-600 text-white font-bold border-2 border-blue-700">
                            任务 #{flight.task_id}
                          </Badge>
                        )}
                        
                        {/* 航空公司 */}
                        <Badge className={`${getAirlineColor(flight.airline)} text-xs px-2 py-1`}>
                          {flight.airline}
                        </Badge>
                        
                        {/* 航班号 */}
                        <span className="font-mono font-bold text-lg">{flight.flight_number}</span>
                        
                        {/* 机型 */}
                        {flight.aircraft_type && (
                          <span className="text-sm text-gray-600 bg-gray-100 px-2 py-1 rounded">
                            {flight.aircraft_type}
                          </span>
                        )}
                        
                        {/* 共享航班标识 */}
                        {flight.is_shared_flight === '是' && (
                          <Badge variant="outline" className="text-xs bg-blue-50 text-blue-700 border-blue-300">共享航班</Badge>
                        )}
                        {/* 经停标识 */}
                        {flight.has_stopover === '是' && (
                          <Badge variant="outline" className="text-xs bg-orange-50 text-orange-700 border-orange-300">
                            经停 {flight.stopover_city || flight.stopover_airport || ''}
                          </Badge>
                        )}
                      </div>
                      
                      {/* 航班路线 */}
                      <div className="flex items-center space-x-6">
                        {/* 出发信息 */}
                        <div className="text-center">
                          <div className="text-xs text-gray-600 mb-1">
                            {flight.departure_city || getAirportName(flight.departure_airport)}
                          </div>
                          <div className="text-2xl font-bold">{formatTime(flight.departure_time)}</div>
                          <div className="text-xs text-gray-500">
                            {flight.departure_airport}
                            {flight.departure_terminal && ` ${flight.departure_terminal}`}
                          </div>
                          {flight.departure_date && (
                            <div className="text-xs text-blue-600 font-medium mt-1">
                              {formatDepartureDate(flight.departure_date)}
                            </div>
                          )}
                        </div>
                        
                        {/* 中间：飞行时间和经停信息 */}
                        <div className="flex flex-col items-center">
                          <div className="flex items-center space-x-2">
                            <div className="w-16 h-px bg-gray-300"></div>
                            <Plane className="h-4 w-4 text-gray-400" />
                            <div className="w-16 h-px bg-gray-300"></div>
                          </div>
                          <div className="text-sm font-medium text-gray-700 mt-1">
                            {flight.flight_duration || (flight.departure_time && flight.arrival_time ? calculateFlightDuration(flight.departure_time, flight.arrival_time) : '')}
                          </div>
                          {flight.has_stopover === '是' && (
                            <div className="text-xs text-orange-600 mt-1 font-semibold">
                              ⚠️ 经停 {flight.stopover_city || flight.stopover_airport || '未知城市'}
                            </div>
                          )}
                        </div>
                        
                        {/* 到达信息 */}
                        <div className="text-center">
                          <div className="text-xs text-gray-600 mb-1">
                            {flight.arrival_city || getAirportName(flight.arrival_airport)}
                          </div>
                          <div className="text-2xl font-bold">{formatTime(flight.arrival_time)}</div>
                          <div className="text-xs text-gray-500">
                            {flight.arrival_airport}
                            {flight.arrival_terminal && ` ${flight.arrival_terminal}`}
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    {/* 右侧：价格和操作 */}
                    <div className="text-right ml-6">
                      <div className="mb-2">
                        <div className="text-3xl font-bold text-green-600">
                          {formatPrice(flight.price)}
                        </div>
                        {flight.discount_rate && (
                          <div className="text-xs text-orange-600 font-medium mt-1">
                            {flight.discount_rate}
                          </div>
                        )}
                        {flight.original_price && flight.original_price > flight.price && (
                          <div className="text-sm text-gray-500 line-through">
                            原价 {formatPrice(flight.original_price)}
                          </div>
                        )}
                        {flight.cabin_class && (
                          <div className="text-xs text-gray-500 mt-1">
                            {flight.cabin_class}
                          </div>
                        )}
                        {flight.discount_rate && (
                          <Badge variant="destructive" className="text-xs mt-1">
                            {flight.discount_rate}
                          </Badge>
                        )}
                      </div>
                      
                      {viewMode === 'compare' ? (
                        <Button 
                          className={`w-full ${
                            selectedFlights.includes(flight.id)
                              ? 'bg-green-600 hover:bg-green-700 text-white'
                              : 'bg-blue-600 hover:bg-blue-700 text-white'
                          }`}
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleFlightSelection(flight.id);
                          }}
                        >
                          {selectedFlights.includes(flight.id) ? '已选择' : '选择对比'}
                        </Button>
                      ) : (
                        <Button className="w-full bg-blue-600 hover:bg-blue-700 text-white">
                          选择
                        </Button>
                      )}
                    </div>
                  </div>
                  
                  {/* 底部：详细信息标签 */}
                  <div className="flex flex-wrap items-center gap-2 mt-3 pt-3 border-t border-gray-100">
                    <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                      {flight.cabin_class || '经济舱'}
                    </span>
                    {flight.discount_rate && (
                      <Badge variant="destructive" className="text-xs">
                        {flight.discount_rate}
                      </Badge>
                    )}
                    {flight.has_stopover === '是' && (
                      <span className="text-xs bg-orange-100 text-orange-800 font-semibold px-3 py-1.5 rounded-md border border-orange-300">
                        ⚠️ 经停: {flight.stopover_city || flight.stopover_airport || '未知城市'}
                      </span>
                    )}
                    {/* 任务编号 - 始终显示，可点击查询 */}
                    {flight.task_id != null && flight.task_id !== undefined ? (
                      <span 
                        className="text-sm bg-blue-600 text-white font-bold px-4 py-2 rounded-md border-2 border-blue-700 shadow-md cursor-pointer hover:bg-blue-700"
                        onClick={() => {
                          setSearchParams({...searchParams, taskId: String(flight.task_id)});
                          handleSearch();
                        }}
                        title="点击查询该任务的所有航班"
                      >
                        任务 #{flight.task_id}
                      </span>
                    ) : (
                      <span className="text-xs bg-gray-200 text-gray-700 font-medium px-3 py-1.5 rounded-md border border-gray-400">
                        未分类
                      </span>
                    )}
                    <span className="text-xs text-gray-600 font-medium">
                      抓取时间: {new Date(flight.scrape_time).toLocaleString('zh-CN', {
                        timeZone: 'Asia/Shanghai',
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit'
                      })}
                    </span>
                    <span className="text-xs text-gray-500">
                      {flight.source}
                    </span>
                  </div>
                </CardContent>
              </Card>
                    ))}
                  </div>
                </div>
              ));
            })()
          )}
        </div>
      </div>
    </div>
  );
};

export default FlightResults;
