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
  field_sources?: string;  // 字段来源标识（JSON格式）
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

  // 解析字段来源，判断哪些字段来自OCR
  const getOcrFields = (fieldSources?: string): Set<string> => {
    if (!fieldSources) return new Set();
    try {
      const sources = JSON.parse(fieldSources);
      return new Set(Object.keys(sources).filter(field => sources[field] === 'ocr'));
    } catch {
      return new Set();
    }
  };

  // 判断字段是否来自OCR
  const isOcrField = (field: string, ocrFields: Set<string>): boolean => {
    return ocrFields.has(field);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 紧凑的头部 */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="container mx-auto px-4 py-2">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-lg font-bold text-gray-900">航班查询结果</h1>
              <p className="text-xs text-gray-600">实时航班信息，按价格从低到高排列</p>
            </div>
            <div className="flex items-center space-x-3">
              {statistics && (
                <div className="flex items-center space-x-4 text-xs">
                  <div className="flex items-center space-x-1">
                    <Plane className="h-3 w-3 text-blue-600" />
                    <span className="text-gray-600">共</span>
                    <span className="font-semibold text-blue-600">{statistics.total_flights}</span>
                    <span className="text-gray-600">班</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <DollarSign className="h-3 w-3 text-green-600" />
                    <span className="text-gray-600">最低</span>
                    <span className="font-semibold text-green-600">{formatPrice(statistics.min_price)}</span>
                  </div>
                </div>
              )}
              <Button variant="outline" size="sm" onClick={fetchFlights} className="flex items-center text-xs h-7 px-2">
                <RefreshCw className="h-3 w-3 mr-1" />
                刷新
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-1 max-w-7xl">
        {/* 紧凑的筛选器 */}
        <Card className="mb-2">
          <CardContent className="p-3">
            <div className="flex flex-wrap items-center gap-2">
              <div className="flex items-center space-x-1.5">
                <Label className="text-xs font-medium text-gray-700">价格:</Label>
                <Input
                  type="number"
                  placeholder="最低"
                  value={searchParams.minPrice}
                  onChange={(e) => setSearchParams({...searchParams, minPrice: e.target.value})}
                  className="w-18 h-7 text-xs"
                />
                <span className="text-gray-500 text-xs">-</span>
                <Input
                  type="number"
                  placeholder="最高"
                  value={searchParams.maxPrice}
                  onChange={(e) => setSearchParams({...searchParams, maxPrice: e.target.value})}
                  className="w-18 h-7 text-xs"
                />
              </div>
              
              <div className="flex items-center space-x-1.5">
                <Label className="text-xs font-medium text-gray-700">航司:</Label>
                <Input
                  placeholder="航空公司"
                  value={searchParams.airline}
                  onChange={(e) => setSearchParams({...searchParams, airline: e.target.value})}
                  className="w-24 h-7 text-xs"
                />
              </div>
              
              <div className="flex items-center space-x-1.5">
                <Label className="text-xs font-medium text-gray-700">航班号:</Label>
                <Input
                  placeholder="CA1234"
                  value={searchParams.flightNumber}
                  onChange={(e) => setSearchParams({...searchParams, flightNumber: e.target.value})}
                  className="w-24 h-7 text-xs"
                />
              </div>
              
              <div className="flex items-center space-x-1.5">
                <Label className="text-xs font-medium text-gray-700">出发:</Label>
                <Input
                  placeholder="城市"
                  value={searchParams.departureCity}
                  onChange={(e) => setSearchParams({...searchParams, departureCity: e.target.value})}
                  className="w-20 h-7 text-xs"
                />
              </div>
              
              <div className="flex items-center space-x-1.5">
                <Label className="text-xs font-medium text-gray-700">到达:</Label>
                <Input
                  placeholder="城市"
                  value={searchParams.arrivalCity}
                  onChange={(e) => setSearchParams({...searchParams, arrivalCity: e.target.value})}
                  className="w-20 h-7 text-xs"
                />
              </div>
              
              <div className="flex items-center space-x-1.5">
                <Label className="text-xs font-medium text-gray-700">任务:</Label>
                <Input
                  type="number"
                  placeholder="209"
                  value={searchParams.taskId}
                  onChange={(e) => setSearchParams({...searchParams, taskId: e.target.value})}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleSearch();
                    }
                  }}
                  className="w-20 h-7 text-xs"
                />
                {searchParams.taskId && (
                  <Button 
                    onClick={handleSearch} 
                    size="sm" 
                    className="h-7 px-2 bg-blue-600 hover:bg-blue-700 text-xs"
                  >
                    查询
                  </Button>
                )}
              </div>
              
              <div className="flex items-center space-x-1.5">
                <Label className="text-xs font-medium text-gray-700">显示:</Label>
                <Select
                  value={searchParams.limit.toString()}
                  onValueChange={(value: string) => setSearchParams({...searchParams, limit: parseInt(value)})}
                >
                  <SelectTrigger className="w-16 h-7 text-xs">
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
              
              <div className="flex items-center space-x-1.5">
                <Label className="text-xs font-medium text-gray-700">排序:</Label>
                <Select
                  value={sortBy}
                  onValueChange={(value: 'price' | 'time') => setSortBy(value)}
                >
                  <SelectTrigger className="w-20 h-7 text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="price">价格</SelectItem>
                    <SelectItem value="time">时间</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="flex items-center space-x-1.5">
                <Button onClick={handleSearch} size="sm" className="h-7 px-2 text-xs">
                  <Search className="h-3 w-3 mr-1" />
                  搜索
                </Button>
                <Button variant="outline" onClick={handleReset} size="sm" className="h-7 px-2 text-xs">
                  重置
                </Button>
              </div>
              
              {/* 视图模式切换 */}
              <div className="flex items-center space-x-1.5 ml-2">
                <Button
                  variant={viewMode === 'list' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewMode('list')}
                  className="h-7 px-2 text-xs"
                >
                  列表
                </Button>
                <Button
                  variant={viewMode === 'compare' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setViewMode('compare')}
                  className="h-7 px-2 text-xs"
                >
                  对比
                </Button>
              </div>
              
              {/* 选择状态 */}
              {selectedFlights.length > 0 && (
                <div className="flex items-center space-x-1.5 ml-2">
                  <span className="text-xs text-gray-600">
                    已选 {selectedFlights.length}
                  </span>
                  <Button variant="outline" size="sm" onClick={clearSelection} className="h-7 px-2 text-xs">
                    清除
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* 对比视图 */}
        {viewMode === 'compare' && selectedFlights.length > 0 && (
          <Card className="mb-3 bg-blue-50 border-blue-200">
            <CardContent className="p-3">
              <h3 className="text-base font-semibold text-blue-900 mb-2">航班对比</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                {selectedFlights.map(flightId => {
                  const flight = flights.find(f => f.id === flightId);
                  if (!flight) return null;
                  
                  return (
                    <div key={flightId} className="bg-white p-2 rounded-lg border">
                      <div className="flex justify-between items-start mb-1.5">
                        <div>
                          <Badge className={`${getAirlineColor(flight.airline)} text-xs px-1.5 py-0.5`}>
                            {flight.airline}
                          </Badge>
                          <span className="ml-1.5 font-mono text-xs">{flight.flight_number}</span>
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => toggleFlightSelection(flightId)}
                          className="h-5 w-5 p-0 text-xs"
                        >
                          ×
                        </Button>
                      </div>
                      <div className="text-center">
                        <div className="text-base font-bold text-green-600">
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
        <div className="space-y-2">
          {loading ? (
            <div className="text-center py-8">
              <RefreshCw className="h-6 w-6 animate-spin mx-auto mb-2 text-blue-600" />
              <p className="text-sm text-gray-600">正在加载航班信息...</p>
            </div>
          ) : flights.length === 0 ? (
            <Card className="border-dashed">
              <CardContent className="p-8 text-center">
                <Plane className="h-12 w-12 text-gray-300 mx-auto mb-2" />
                <h3 className="text-base font-medium text-gray-900 mb-1">暂无航班数据</h3>
                <p className="text-xs text-gray-500">请尝试调整搜索条件或稍后再试</p>
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
                    <CardContent className="p-8 text-center">
                      <Plane className="h-12 w-12 text-gray-300 mx-auto mb-2" />
                      <h3 className="text-base font-medium text-gray-900 mb-1">暂无航班数据</h3>
                      <p className="text-xs text-gray-500">
                        {hasTaskIdFilter 
                          ? `未找到任务编号 ${searchParams.taskId} 的航班数据，请尝试调整搜索条件或稍后再试`
                          : '请尝试调整搜索条件或稍后再试'}
                      </p>
                    </CardContent>
                  </Card>
                );
              }

              // 按任务编号倒序排列（数字任务ID在前，未分类在后）
              const sortedTaskEntries = Object.entries(groupedFlights).sort(([a], [b]) => {
                // 如果都是数字，按数字倒序排列
                const aNum = a === '未分类' ? -1 : parseInt(a, 10);
                const bNum = b === '未分类' ? -1 : parseInt(b, 10);
                if (!isNaN(aNum) && !isNaN(bNum)) {
                  return bNum - aNum; // 倒序：大的在前
                }
                // 如果一个是未分类，未分类排在最后
                if (a === '未分类') return 1;
                if (b === '未分类') return -1;
                return 0;
              });

              return sortedTaskEntries.map(([taskId, taskFlights]) => (
                <div key={taskId} className="space-y-1.5">
                  {/* 任务标题 */}
                  <div className="flex items-center justify-between bg-blue-50 border border-blue-300 px-3 py-1.5 rounded mb-1.5">
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-bold text-blue-800 bg-blue-100 px-2 py-0.5 rounded border border-blue-300">
                        {taskId === '未分类' ? '未分类航班' : `任务 #${taskId}`}
                      </span>
                      <span className="text-xs text-blue-700 font-semibold">
                        {taskFlights.length} 个航班
                      </span>
                    </div>
                    <div className="flex items-center space-x-1.5">
                      <span className="text-xs text-gray-600">抓取:</span>
                      <span className="text-xs text-gray-700 font-medium">
                        {taskFlights[0]?.scrape_time && 
                          new Date(taskFlights[0].scrape_time).toLocaleString('zh-CN', {
                            timeZone: 'Asia/Shanghai',
                            year: 'numeric',
                            month: '2-digit',
                            day: '2-digit',
                            hour: '2-digit',
                            minute: '2-digit'
                          })
                        }
                      </span>
                    </div>
                  </div>
                  
                  {/* 该任务的航班列表 - 响应式网格布局 */}
                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-2">
                    {taskFlights.map((flight) => {
                      // 解析OCR字段
                      const ocrFields = getOcrFields(flight.field_sources);
                      
                      return (
              <Card 
                key={flight.id} 
                className={`hover:shadow-md transition-all duration-200 border-l-2 ${
                  selectedFlights.includes(flight.id) 
                    ? 'border-l-green-500 bg-green-50 shadow-sm' 
                    : 'border-l-blue-500 bg-white'
                } ${viewMode === 'compare' ? 'cursor-pointer' : ''}`}
                onClick={() => viewMode === 'compare' && toggleFlightSelection(flight.id)}
              >
                <CardContent className="p-3">
                  {/* 顶部：航班基本信息和价格 */}
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1 min-w-0">
                      {/* 航空公司、航班号、机型 */}
                      <div className="flex items-center flex-wrap gap-1.5 mb-1.5">
                        <Badge className={`${getAirlineColor(flight.airline)} text-xs px-1.5 py-0.5 font-semibold`}>
                          {flight.airline}
                        </Badge>
                        <span className="font-mono font-bold text-base text-gray-900">{flight.flight_number}</span>
                        {flight.aircraft_type && (
                          <span className={`text-xs px-1.5 py-0.5 rounded border flex items-center gap-0.5 ${isOcrField('aircraft_type', ocrFields) ? 'text-amber-700 bg-amber-50 border-amber-300' : 'text-gray-600 bg-gray-100 border-gray-200'}`}>
                            {flight.aircraft_type}
                            {isOcrField('aircraft_type', ocrFields) && (
                              <span className="text-xs" title="此字段来自OCR识别">📸</span>
                            )}
                          </span>
                        )}
                      </div>
                      
                      {/* 特殊标识 */}
                      <div className="flex items-center flex-wrap gap-1">
                        {flight.departure_date && (
                          <span className="text-xs text-blue-600 font-medium bg-blue-50 px-1.5 py-0.5 rounded border border-blue-200">
                            {formatDepartureDate(flight.departure_date)}
                          </span>
                        )}
                        {flight.is_shared_flight === '是' && (
                          <Badge variant="outline" className="text-xs bg-blue-50 text-blue-700 border-blue-300 font-medium px-1 py-0.5">
                            共享
                          </Badge>
                        )}
                        {flight.has_stopover === '是' && (
                          <Badge variant="outline" className="text-xs bg-orange-50 text-orange-700 border-orange-300 font-medium px-1 py-0.5">
                            经停
                          </Badge>
                        )}
                      </div>
                    </div>
                    
                    {/* 价格区域 */}
                    <div className="text-right ml-2 flex-shrink-0">
                      <div className="flex items-baseline justify-end gap-1 mb-0.5">
                        {flight.original_price && flight.original_price > flight.price && (
                          <span className="text-xs text-gray-400 line-through">
                            {formatPrice(flight.original_price)}
                          </span>
                        )}
                        <div className="text-xl font-bold text-green-600">
                          {formatPrice(flight.price)}
                        </div>
                      </div>
                      <div className="flex items-center justify-end gap-1 flex-wrap">
                        {flight.discount_rate && (
                          <Badge variant="destructive" className="text-xs px-1 py-0.5 bg-orange-500 hover:bg-orange-600">
                            {flight.discount_rate}
                          </Badge>
                        )}
                        {flight.cabin_class && (
                          <span className="text-xs text-gray-600 bg-gray-100 px-1 py-0.5 rounded">
                            {flight.cabin_class}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  {/* 航班路线 - 紧凑布局 */}
                  <div className="bg-gray-50 rounded-lg p-2 border border-gray-200 mb-2">
                    <div className="flex items-center justify-between">
                      {/* 出发信息 */}
                      <div className="flex-1 text-center">
                        <div className="text-xs text-gray-500 mb-0.5 font-medium">
                          {flight.departure_city || getAirportName(flight.departure_airport)}
                        </div>
                        <div className="text-xl font-bold text-gray-900 mb-0.5">{formatTime(flight.departure_time)}</div>
                        <div className="text-xs text-gray-600 flex items-center justify-center gap-0.5">
                          <span className={isOcrField('departure_airport', ocrFields) ? 'text-amber-600 font-semibold' : ''}>
                            {flight.departure_airport || '—'}
                          </span>
                          {isOcrField('departure_airport', ocrFields) && (
                            <span className="text-xs text-amber-600" title="此字段来自OCR识别">📸</span>
                          )}
                          {flight.departure_terminal && (
                            <span className={`ml-0.5 font-medium ${isOcrField('departure_terminal', ocrFields) ? 'text-amber-600' : 'text-blue-600'}`}>
                              {flight.departure_terminal}
                            </span>
                          )}
                        </div>
                      </div>
                      
                      {/* 中间：飞行路线和时间 */}
                      <div className="flex flex-col items-center px-2">
                        <div className="flex items-center space-x-0.5 mb-0.5">
                          <div className="w-6 h-0.5 bg-blue-400"></div>
                          <Plane className="h-3 w-3 text-blue-500" />
                          <div className="w-6 h-0.5 bg-blue-400"></div>
                        </div>
                        <div className={`text-xs font-semibold bg-white px-1 py-0.5 rounded border ${isOcrField('flight_duration', ocrFields) ? 'text-amber-700 border-amber-300' : 'text-gray-700 border-gray-200'} flex items-center gap-0.5`}>
                          {flight.flight_duration || (flight.departure_time && flight.arrival_time ? calculateFlightDuration(flight.departure_time, flight.arrival_time) : '')}
                          {isOcrField('flight_duration', ocrFields) && (
                            <span className="text-xs text-amber-600" title="此字段来自OCR识别">📸</span>
                          )}
                        </div>
                      </div>
                      
                      {/* 到达信息 */}
                      <div className="flex-1 text-center">
                        <div className="text-xs text-gray-500 mb-0.5 font-medium">
                          {flight.arrival_city || getAirportName(flight.arrival_airport)}
                        </div>
                        <div className="text-xl font-bold text-gray-900 mb-0.5">{formatTime(flight.arrival_time)}</div>
                        <div className="text-xs text-gray-600 flex items-center justify-center gap-0.5">
                          <span className={isOcrField('arrival_airport', ocrFields) ? 'text-amber-600 font-semibold' : ''}>
                            {flight.arrival_airport || '—'}
                          </span>
                          {isOcrField('arrival_airport', ocrFields) && (
                            <span className="text-xs text-amber-600" title="此字段来自OCR识别">📸</span>
                          )}
                          {flight.arrival_terminal && (
                            <span className={`ml-0.5 font-medium ${isOcrField('arrival_terminal', ocrFields) ? 'text-amber-600' : 'text-blue-600'}`}>
                              {flight.arrival_terminal}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {/* 操作按钮 */}
                  <div className="mb-2">
                    {viewMode === 'compare' ? (
                      <Button 
                        size="sm"
                        className={`w-full text-xs h-7 ${
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
                      <Button size="sm" className="w-full bg-blue-600 hover:bg-blue-700 text-white text-xs h-7">
                        选择
                      </Button>
                    )}
                  </div>
                  
                  {/* 底部：元数据信息（次要信息） */}
                  <div className="flex flex-wrap items-center gap-1.5 mt-2 pt-2 border-t border-gray-200">
                    {/* 任务编号 - 可点击查询 */}
                    {flight.task_id != null && flight.task_id !== undefined ? (
                      <span 
                        className="text-xs bg-blue-600 text-white font-semibold px-2 py-0.5 rounded cursor-pointer hover:bg-blue-700 transition-colors"
                        onClick={() => {
                          setSearchParams({...searchParams, taskId: String(flight.task_id)});
                          handleSearch();
                        }}
                        title="点击查询该任务的所有航班"
                      >
                        任务 #{flight.task_id}
                      </span>
                    ) : (
                      <span className="text-xs bg-gray-200 text-gray-600 font-medium px-2 py-0.5 rounded">
                        未分类
                      </span>
                    )}
                    
                    {/* 数据源和时间 */}
                    <span className="text-xs text-gray-500">
                      {flight.source}
                    </span>
                    <span className="text-xs text-gray-500">•</span>
                    <span className="text-xs text-gray-500">
                      {new Date(flight.scrape_time).toLocaleString('zh-CN', {
                        timeZone: 'Asia/Shanghai',
                        year: 'numeric',
                        month: '2-digit',
                        day: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </span>
                  </div>
                </CardContent>
              </Card>
                    );
                    })}
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
